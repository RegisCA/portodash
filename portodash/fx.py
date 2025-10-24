"""Foreign exchange helper: fetch rates and cache them locally.

We store cached rates in `logs/fx_rates.json` to avoid frequent network calls.
Rates returned map currency code -> rate_to_base (e.g. USD -> 1.34 means 1 USD = 1.34 CAD).
"""
from datetime import datetime, timedelta
import json
import os
import logging
from typing import Iterable, Dict

import requests

logger = logging.getLogger(__name__)


def _cache_path():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logs = os.path.join(root, 'logs')
    try:
        os.makedirs(logs, exist_ok=True)
    except Exception:
        pass
    return os.path.join(logs, 'fx_rates.json')


def get_fx_rates(currencies: Iterable[str], base: str = 'CAD', max_age_hours: int = 12) -> Dict[str, float]:
    """Return a mapping currency -> rate_to_base.

    currencies: iterable of currency codes (e.g. ['USD','EUR']). If a currency equals base it will be skipped.
    base: base currency code (default 'CAD').

    This will attempt to read cached values from logs/fx_rates.json if not older than max_age_hours.
    Otherwise it will query exchangerate.host for latest rates.
    """
    currs = {c.upper() for c in currencies if c and c.upper() != base.upper()}
    if not currs:
        return {}

    cache_file = _cache_path()
    now = datetime.utcnow()
    # try cache
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as fh:
                data = json.load(fh)
            ts = data.get('_fetched_at')
            if ts:
                fetched = datetime.fromisoformat(ts)
                if (now - fetched).total_seconds() < max_age_hours * 3600:
                    rates = data.get('rates', {})
                    # return only requested currencies present
                    return {c: rates.get(c) for c in currs if rates.get(c) is not None}
    except Exception:
        logger.debug('Failed to read fx cache', exc_info=True)

    # Fetch from open.er-api.com (free, no API key required)
    try:
        # Fetch rates with base currency
        url = f'https://open.er-api.com/v6/latest/{base.upper()}'
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        j = r.json()
        
        if not j.get('result') == 'success':
            logger.error(f"FX API returned non-success: {j}")
            return {}
            
        base_rates = j.get('rates', {})  # rates: currency -> value (currency per base)

        # Convert: base_rates[c] = CURRENCY per BASE
        # So 1 BASE = base_rates[c] CURRENCY
        # We want: 1 CURRENCY = ? BASE
        # Answer: 1 CURRENCY = 1 / base_rates[c] BASE
        out = {}
        for c in currs:
            v = base_rates.get(c)
            if v is None or v == 0:
                continue
            out[c] = 1.0 / float(v)

        # persist cache
        try:
            with open(cache_file, 'w') as fh:
                json.dump({'_fetched_at': now.isoformat(), 'rates': out}, fh)
        except Exception:
            logger.debug('Failed to write fx cache', exc_info=True)

        return out
    except Exception:
        logger.exception('Failed to fetch FX rates')
        # fallback: empty
        return {}
