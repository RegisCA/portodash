#!/usr/bin/env python3
"""Standalone scheduler script for PortoDash.

This script runs a background process that fetches prices and updates the historical CSV
at scheduled intervals (4:30 PM local time on weekdays).

Run with:
    python scripts/run_scheduler.py
"""
import os
import logging
import signal
import sys
import pytz
from datetime import datetime

# Add parent dir to path so we can import portodash
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portodash.scheduler import schedule_daily_snapshot


def setup_logging():
    """Configure logging to both file and console."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Format with timestamps and log level
    fmt = '%(asctime)s %(levelname)s: %(message)s'
    
    # Console handler with INFO level
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(fmt))
    
    # File handler with DEBUG level
    log_file = os.path.join(log_dir, f'scheduler_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(fmt))
    
    # Root logger configuration
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(console)
    root.addHandler(file_handler)
    
    return log_file


def handle_signals(signum, frame):
    """Signal handler for graceful shutdown."""
    logging.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signals)
    signal.signal(signal.SIGTERM, handle_signals)
    
    # Setup logging
    log_file = setup_logging()
    logging.info("Starting PortoDash scheduler daemon")
    
    # Get base paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    portfolio_path = os.path.join(base_dir, 'portfolio.json')
    hist_csv = os.path.join(base_dir, 'historical.csv')
    
    # Configure timezone for market time
    timezone = pytz.timezone('America/Toronto')
    
    try:
        # Start the scheduler
        scheduler = schedule_daily_snapshot(hist_csv, portfolio_path, timezone=timezone)
        logging.info(f"Scheduler running. View logs at: {log_file}")
        
        # Keep the main thread alive
        while True:
            signal.pause()
    
    except Exception as e:
        logging.exception("Fatal error in scheduler daemon")
        sys.exit(1)


if __name__ == '__main__':
    main()