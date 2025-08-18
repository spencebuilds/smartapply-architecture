"""
SmartApply Rev A Observability Service
Wraps ingestion cycles and API calls with comprehensive tracking.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import timedelta
from supabase import Client


class IngestRunTracker:
    """Tracks ingestion runs with comprehensive metrics."""
    
    def __init__(self, sb: Client):
        """Initialize with Supabase client."""
        self.sb = sb
        self.logger = logging.getLogger(__name__)
        self.current_run_id = None
        self.start_time = None
        self.metrics = {}
    
    @contextmanager
    def track_ingestion(self, run_type: str, source: str = "", metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for tracking ingestion runs.
        
        Usage:
            with tracker.track_ingestion("job_fetch", "greenhouse") as run_id:
                # Do ingestion work
                tracker.increment_processed()
                tracker.increment_successful() 
        """
        # Start ingestion run
        run_id = self._start_run(run_type, source, metadata)
        
        try:
            yield run_id
            # Mark as completed on success
            self._complete_run(run_id, "completed")
        except Exception as e:
            # Mark as failed on exception
            self._complete_run(run_id, "failed", str(e))
            raise
    
    def _start_run(self, run_type: str, source: str = "", metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a new ingestion run."""
        try:
            self.start_time = datetime.now()
            self.metrics = {
                "processed": 0,
                "successful": 0,
                "failed": 0
            }
            
            run_data = {
                "run_type": run_type,
                "status": "running",
                "source": source,
                "items_processed": 0,
                "items_successful": 0,
                "items_failed": 0,
                "run_metadata": metadata or {},
                "started_at": self.start_time.isoformat()
            }
            
            result = self.sb.table("ingest_runs").insert(run_data).execute()
            
            if result.data:
                run_id = result.data[0]["id"]
                self.current_run_id = run_id
                self.logger.info(f"Started ingestion run {run_id}: {run_type} from {source}")
                return run_id
            
            raise Exception("Failed to create ingest run record")
            
        except Exception as e:
            self.logger.error(f"Error starting ingestion run: {str(e)}")
            raise
    
    def _complete_run(self, run_id: str, status: str, error_summary: Optional[str] = None):
        """Complete an ingestion run with final metrics."""
        try:
            end_time = datetime.now()
            duration_seconds = int((end_time - self.start_time).total_seconds()) if self.start_time else 0
            
            update_data = {
                "status": status,
                "items_processed": self.metrics.get("processed", 0),
                "items_successful": self.metrics.get("successful", 0),
                "items_failed": self.metrics.get("failed", 0),
                "completed_at": end_time.isoformat(),
                "duration_seconds": duration_seconds
            }
            
            if error_summary:
                update_data["error_summary"] = error_summary
            
            self.sb.table("ingest_runs").update(update_data).eq("id", run_id).execute()
            
            self.logger.info(f"Completed ingestion run {run_id}: {status} - {self.metrics['successful']}/{self.metrics['processed']} successful")
            
        except Exception as e:
            self.logger.error(f"Error completing ingestion run {run_id}: {str(e)}")
    
    def increment_processed(self, count: int = 1):
        """Increment processed items count."""
        self.metrics["processed"] = self.metrics.get("processed", 0) + count
    
    def increment_successful(self, count: int = 1):
        """Increment successful items count."""
        self.metrics["successful"] = self.metrics.get("successful", 0) + count
    
    def increment_failed(self, count: int = 1):
        """Increment failed items count."""
        self.metrics["failed"] = self.metrics.get("failed", 0) + count
    
    def update_metadata(self, metadata: Dict[str, Any]):
        """Update run metadata during processing."""
        if self.current_run_id:
            try:
                self.sb.table("ingest_runs").update({
                    "run_metadata": metadata
                }).eq("id", self.current_run_id).execute()
            except Exception as e:
                self.logger.error(f"Error updating run metadata: {str(e)}")


class APICallTracker:
    """Tracks API calls with detailed metrics."""
    
    def __init__(self, sb: Client):
        """Initialize with Supabase client."""
        self.sb = sb
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def track_api_call(self, service_name: str, endpoint: str, method: str = "GET"):
        """
        Context manager for tracking API calls.
        
        Usage:
            with api_tracker.track_api_call("greenhouse", "/jobs", "GET") as call_tracker:
                response = requests.get(url)
                call_tracker.set_response(response.status_code, len(response.content))
        """
        call_start = datetime.now()
        call_data = {
            "service_name": service_name,
            "endpoint": endpoint,
            "method": method,
            "created_at": call_start.isoformat()
        }
        
        class CallTracker:
            def __init__(self, sb, call_data, start_time, logger):
                self.sb = sb
                self.call_data = call_data
                self.start_time = start_time
                self.logger = logger
            
            def set_request_size(self, size_bytes: int):
                self.call_data["request_size_bytes"] = size_bytes
            
            def set_response(self, status_code: int, response_size_bytes: int = 0):
                self.call_data["status_code"] = status_code
                self.call_data["response_size_bytes"] = response_size_bytes
            
            def set_error(self, error_message: str):
                self.call_data["error_message"] = error_message
        
        call_tracker = CallTracker(self.sb, call_data, call_start, self.logger)
        
        try:
            yield call_tracker
        finally:
            # Calculate response time
            call_end = datetime.now()
            response_time_ms = int((call_end - call_start).total_seconds() * 1000)
            call_data["response_time_ms"] = response_time_ms
            
            # Insert API call record
            try:
                self.sb.table("api_calls").insert(call_data).execute()
                self.logger.debug(f"Tracked API call: {service_name} {method} {endpoint} - {response_time_ms}ms")
            except Exception as e:
                self.logger.error(f"Error tracking API call: {str(e)}")
    
    def get_api_metrics(self, service_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get API call metrics for a service over the last N hours."""
        try:
            since = datetime.now() - timedelta(hours=hours)
            
            result = self.sb.table("api_calls").select(
                "status_code, response_time_ms, error_message"
            ).eq(
                "service_name", service_name
            ).gte(
                "created_at", since.isoformat()
            ).execute()
            
            calls = result.data if result.data else []
            
            total_calls = len(calls)
            successful_calls = len([c for c in calls if 200 <= c.get("status_code", 0) < 300])
            failed_calls = total_calls - successful_calls
            
            response_times = [c.get("response_time_ms", 0) for c in calls if c.get("response_time_ms")]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                "service_name": service_name,
                "period_hours": hours,
                "total_calls": total_calls,
                "successful_calls": successful_calls,
                "failed_calls": failed_calls,
                "success_rate": successful_calls / total_calls if total_calls > 0 else 0,
                "avg_response_time_ms": round(avg_response_time, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting API metrics for {service_name}: {str(e)}")
            return {
                "service_name": service_name,
                "period_hours": hours,
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "success_rate": 0,
                "avg_response_time_ms": 0
            }