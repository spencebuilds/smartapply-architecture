"""
Job scheduler for automated execution.
"""

import threading
import time
import logging
from typing import Callable
from datetime import datetime, timedelta


class JobScheduler:
    """Scheduler for running jobs at regular intervals."""
    
    def __init__(self, job_function: Callable, interval_minutes: int = 15):
        """Initialize job scheduler.
        
        Args:
            job_function: Function to execute on schedule
            interval_minutes: Interval between job executions in minutes
        """
        self.job_function = job_function
        self.interval_seconds = interval_minutes * 60
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.thread = None
        self.stop_event = threading.Event()
        
        self.logger.info(f"Scheduler initialized with {interval_minutes} minute interval")
    
    def _run_scheduler(self):
        """Internal method to run the scheduler loop."""
        self.logger.info("Scheduler started")
        
        while not self.stop_event.is_set():
            try:
                next_run = datetime.now() + timedelta(seconds=self.interval_seconds)
                self.logger.info(f"Next job execution scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Wait for the interval or until stop is requested
                if self.stop_event.wait(self.interval_seconds):
                    break
                
                if not self.stop_event.is_set():
                    self.logger.info("Executing scheduled job")
                    job_start_time = datetime.now()
                    
                    try:
                        self.job_function()
                        job_duration = datetime.now() - job_start_time
                        self.logger.info(f"Job completed in {job_duration.total_seconds():.2f} seconds")
                    except Exception as e:
                        self.logger.error(f"Error in scheduled job: {str(e)}")
                        
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {str(e)}")
                # Continue running even if there's an error
                time.sleep(60)  # Wait a minute before trying again
        
        self.logger.info("Scheduler stopped")
    
    def start(self):
        """Start the scheduler."""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        self.logger.info("Scheduler thread started")
    
    def stop(self, timeout: int = 30):
        """Stop the scheduler.
        
        Args:
            timeout: Maximum time to wait for scheduler to stop
        """
        if not self.is_running:
            self.logger.warning("Scheduler is not running")
            return
        
        self.logger.info("Stopping scheduler...")
        self.stop_event.set()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)
            
            if self.thread.is_alive():
                self.logger.warning(f"Scheduler did not stop within {timeout} seconds")
            else:
                self.logger.info("Scheduler stopped successfully")
        
        self.is_running = False
    
    def is_active(self) -> bool:
        """Check if scheduler is currently running."""
        return self.is_running and self.thread is not None and self.thread.is_alive()
    
    def get_status(self) -> dict:
        """Get current scheduler status."""
        return {
            "is_running": self.is_running,
            "thread_alive": self.thread.is_alive() if self.thread else False,
            "interval_seconds": self.interval_seconds,
            "interval_minutes": self.interval_seconds / 60
        }


class OneTimeScheduler:
    """Scheduler for running a job once at a specific time."""
    
    def __init__(self, job_function: Callable, run_at: datetime):
        """Initialize one-time scheduler.
        
        Args:
            job_function: Function to execute
            run_at: DateTime when to execute the job
        """
        self.job_function = job_function
        self.run_at = run_at
        self.logger = logging.getLogger(__name__)
        self.is_scheduled = False
        self.thread = None
        self.stop_event = threading.Event()
    
    def _wait_and_execute(self):
        """Wait until scheduled time and execute job."""
        now = datetime.now()
        
        if self.run_at <= now:
            self.logger.warning("Scheduled time is in the past, executing immediately")
            delay = 0
        else:
            delay = (self.run_at - now).total_seconds()
            self.logger.info(f"Job scheduled to run in {delay:.1f} seconds at {self.run_at}")
        
        # Wait until scheduled time
        if delay > 0 and self.stop_event.wait(delay):
            self.logger.info("One-time job cancelled before execution")
            return
        
        if not self.stop_event.is_set():
            try:
                self.logger.info("Executing one-time scheduled job")
                self.job_function()
                self.logger.info("One-time job completed successfully")
            except Exception as e:
                self.logger.error(f"Error in one-time job: {str(e)}")
        
        self.is_scheduled = False
    
    def start(self):
        """Start the one-time scheduler."""
        if self.is_scheduled:
            self.logger.warning("One-time job is already scheduled")
            return
        
        self.is_scheduled = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._wait_and_execute, daemon=True)
        self.thread.start()
        
        self.logger.info("One-time scheduler started")
    
    def cancel(self):
        """Cancel the scheduled job."""
        if not self.is_scheduled:
            self.logger.warning("No job is currently scheduled")
            return
        
        self.logger.info("Cancelling one-time scheduled job")
        self.stop_event.set()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        self.is_scheduled = False
        self.logger.info("One-time job cancelled")
