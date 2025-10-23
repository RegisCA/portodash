from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


def schedule_daily_snapshot(csv_path, portfolio_path, timezone=None):
    """Schedule a daily snapshot job at 16:30 local time.

    This function returns the scheduler instance. It does not block.
    """
    # Lazy import to avoid heavy deps at module import
    from .data_fetch import get_current_prices, fetch_and_store_snapshot

    def job():
        try:
            import json
            with open(portfolio_path, 'r') as f:
                cfg = json.load(f)
            holdings = cfg.get('holdings', [])
            tickers = [h['ticker'] for h in holdings]
            prices = get_current_prices(tickers)
            df = fetch_and_store_snapshot(holdings, prices, csv_path)
            logger.info(f"Daily snapshot written: {len(df)} rows at {datetime.utcnow().isoformat()}")
        except Exception as e:
            logger.exception('Failed to run daily snapshot job')

    scheduler = BackgroundScheduler(timezone=timezone)
    # run every weekday at 16:30
    trigger = CronTrigger(hour=16, minute=30)
    scheduler.add_job(job, trigger)
    scheduler.start()
    logger.info('Scheduler started for daily snapshots')
    return scheduler
