"""
Job storage module for tracking processed jobs and preventing duplicates.
"""

import json
import os
import logging
from typing import Set, Dict, Any
from datetime import datetime, timedelta


class JobStorage:
    """Handles storage and tracking of processed jobs."""
    
    def __init__(self, storage_file: str = "processed_jobs.json"):
        """Initialize job storage."""
        self.logger = logging.getLogger(__name__)
        self.storage_file = storage_file
        self.processed_jobs = self._load_processed_jobs()
        
        # Clean up old entries periodically
        self._cleanup_old_entries()
    
    def _load_processed_jobs(self) -> Dict[str, str]:
        """Load processed jobs from storage file."""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    # Handle case where file contains a list instead of dict (from calibration reset)
                    if isinstance(data, list):
                        self.logger.info("Converting processed jobs from list to dict format")
                        return {}
                    self.logger.info(f"Loaded {len(data)} processed jobs from storage")
                    return data
            else:
                self.logger.info("No existing storage file found, starting fresh")
                return {}
        except Exception as e:
            self.logger.error(f"Error loading processed jobs: {str(e)}")
            return {}
    
    def _save_processed_jobs(self):
        """Save processed jobs to storage file."""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.processed_jobs, f, indent=2)
            self.logger.debug(f"Saved {len(self.processed_jobs)} processed jobs to storage")
        except Exception as e:
            self.logger.error(f"Error saving processed jobs: {str(e)}")
    
    def _cleanup_old_entries(self, days_to_keep: int = 30):
        """Remove old entries to prevent unlimited growth."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.isoformat()
            
            initial_count = len(self.processed_jobs)
            
            # Filter out old entries
            self.processed_jobs = {
                job_id: timestamp 
                for job_id, timestamp in self.processed_jobs.items()
                if timestamp > cutoff_str
            }
            
            removed_count = initial_count - len(self.processed_jobs)
            
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} old job entries (older than {days_to_keep} days)")
                self._save_processed_jobs()
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    def is_job_processed(self, job_id: str) -> bool:
        """Check if a job has already been processed."""
        return job_id in self.processed_jobs
    
    def mark_job_processed(self, job_id: str):
        """Mark a job as processed."""
        self.processed_jobs[job_id] = datetime.now().isoformat()
        self._save_processed_jobs()
        self.logger.debug(f"Marked job as processed: {job_id}")
    
    def get_processed_job_count(self) -> int:
        """Get count of processed jobs."""
        return len(self.processed_jobs)
    
    def get_processed_jobs_in_range(self, days: int = 7) -> Dict[str, str]:
        """Get jobs processed within the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        recent_jobs = {
            job_id: timestamp 
            for job_id, timestamp in self.processed_jobs.items()
            if timestamp > cutoff_str
        }
        
        return recent_jobs
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job from processed list (for reprocessing)."""
        if job_id in self.processed_jobs:
            del self.processed_jobs[job_id]
            self._save_processed_jobs()
            self.logger.info(f"Removed job from processed list: {job_id}")
            return True
        return False
    
    def clear_all_processed_jobs(self):
        """Clear all processed jobs (use with caution)."""
        self.processed_jobs = {}
        self._save_processed_jobs()
        self.logger.warning("Cleared all processed jobs from storage")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about the job storage."""
        total_jobs = len(self.processed_jobs)
        recent_jobs = len(self.get_processed_jobs_in_range(7))
        oldest_entry = None
        newest_entry = None
        
        if self.processed_jobs:
            timestamps = list(self.processed_jobs.values())
            oldest_entry = min(timestamps)
            newest_entry = max(timestamps)
        
        return {
            "total_processed_jobs": total_jobs,
            "jobs_last_7_days": recent_jobs,
            "oldest_entry": oldest_entry,
            "newest_entry": newest_entry,
            "storage_file": self.storage_file
        }
