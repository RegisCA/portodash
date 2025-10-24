from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime
import json
import logging
import pytz
import threading

from .data_fetch import get_current_prices, fetch_and_store_snapshot

logger = logging.getLogger(__name__)
import os
import json as _json


class SchedulerStatus:
    """Thread-safe status tracking for scheduler."""
    def __init__(self):
        self._lock = threading.Lock()
        self._last_run = None
        self._next_run = None
        self._last_error = None
        self._job_running = False

    def update_run_times(self, last=None, next_=None):
        """Update last/next run times."""
        with self._lock:
            if last is not None:
                self._last_run = last
            if next_ is not None:
                self._next_run = next_

    def set_error(self, error):
        """Record last error message (or clear if None)."""
        with self._lock:
            self._last_error = str(error) if error is not None else None

    def set_running(self, running):
        """Update job running status."""
        with self._lock:
            self._job_running = running

    def get_status(self):
        """Return current status as dict."""
        with self._lock:
            return {
                'last_run': self._last_run.isoformat() if self._last_run else None,
                'next_run': self._next_run.isoformat() if self._next_run else None,
                'last_error': self._last_error,
                'job_running': self._job_running
            }


# Global status tracker
_status = SchedulerStatus()


def get_scheduler_status():
    """Return current scheduler status."""
    return _status.get_status()


def _status_file_path():
    """Return path to a JSON status file in the project's logs directory."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    log_dir = os.path.join(project_root, 'logs')
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        pass
    return os.path.join(log_dir, 'scheduler_status.json')


def _write_status_file():
    try:
        path = _status_file_path()
        with open(path, 'w') as fh:
            _json.dump(_status.get_status(), fh)
    except Exception:
        logger.exception('Failed to write scheduler status file')


def schedule_daily_snapshot(csv_path, portfolio_path, timezone=None):
    """Schedule a daily snapshot job at 16:30 local time.

    Args:
        csv_path: Path to historical.csv for snapshots
        portfolio_path: Path to portfolio.json config
        timezone: Timezone for scheduler (default America/Toronto)

    Returns:
        BackgroundScheduler instance (already started)
    """
    if timezone is None:
        timezone = pytz.timezone('America/Toronto')

    def _snapshot_job():
        """Price snapshot job with status tracking."""
        _status.set_running(True)
        _write_status_file()
        try:
            with open(portfolio_path, 'r') as f:
                cfg = json.load(f)
            holdings = cfg.get('holdings', [])
            tickers = [h['ticker'] for h in holdings]

            prices = get_current_prices(tickers, csv_path=csv_path)  # Enable cache fallback
            df = fetch_and_store_snapshot(holdings, prices, csv_path)

            now = datetime.now(timezone)
            _status.update_run_times(last=now)
            _write_status_file()
            _status.set_error(None)
            _write_status_file()
            logger.info(f"Daily snapshot written: {len(df)} rows at {now.isoformat()}")

        except Exception as e:
            logger.exception('Failed to run daily snapshot job')
            _status.set_error(e)

        finally:
            _status.set_running(False)
            _write_status_file()

    scheduler = BackgroundScheduler(timezone=timezone)

    # Run every weekday at 16:30
    trigger = CronTrigger(
        hour=16,
        minute=30,
        day_of_week='mon-fri',
        timezone=timezone
    )

    # Add the job (give the function a distinct local name)
    added_job = scheduler.add_job(_snapshot_job, trigger, name='price_snapshot')

    # Start scheduler so next_run_time is populated
    scheduler.start()

    # Safely obtain next_run_time
    try:
        j = scheduler.get_job(added_job.id)
        next_rt = getattr(j, 'next_run_time', None)
        _status.update_run_times(next_=next_rt)
        _write_status_file()
    except Exception:
        logger.exception('Unable to determine next run time after starting scheduler')

    # Listener to update next_run_time and record errors
    def _listener(event):
        try:
            j = scheduler.get_job(event.job_id)
            next_rt = getattr(j, 'next_run_time', None)
            _status.update_run_times(next_=next_rt)
            _write_status_file()
            # If the event carries an exception, record it
            if hasattr(event, 'exception') and event.exception:
                _status.set_error(event.exception)
                _write_status_file()
            else:
                _status.set_error(None)
                _write_status_file()
        except Exception:
            logger.exception('Scheduler listener failed')

    scheduler.add_listener(_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    logger.info('Scheduler configured for daily snapshots at 4:30 PM (weekdays)')
    return scheduler
