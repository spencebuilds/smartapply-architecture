"""
Observability Service - Production-Ready Logging and Metrics
Portfolio showcase of comprehensive system observability.
"""

import logging
import time
import json
from contextlib import contextmanager
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class APICallMetric:
    service: str
    endpoint: str
    method: str
    status_code: int
    response_time_ms: int
    cost: float = 0.0
    user_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class IngestRunMetric:
    source: str
    run_type: str
    jobs_discovered: int = 0
    jobs_processed: int = 0
    jobs_matched: int = 0
    error_count: int = 0
    execution_time_ms: int = 0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ObservabilityService:
    """
    Production-ready observability service for tracking system health,
    performance, and business metrics.
    
    Features:
    - Structured logging with context
    - Performance timing
    - API call tracking
    - Cost monitoring
    - Error aggregation
    - Business metric collection
    """
    
    def __init__(self, service_name: str = "smartapply"):
        """Initialize observability service."""
        self.service_name = service_name
        
        # Configure structured logging
        self.logger = logging.getLogger(f"{service_name}.observability")
        
        # In-memory metric storage for demo
        # Production would use Prometheus, DataDog, etc.
        self.metrics = {
            "counters": {},
            "gauges": {},
            "histograms": {},
            "api_calls": [],
            "ingest_runs": []
        }
        
        self.logger.info(f"ObservabilityService initialized for {service_name}")
    
    def log_structured(self, level: str, message: str, **context):
        """Log with structured context data."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "service": self.service_name,
            "message": message,
            "context": context
        }
        
        getattr(self.logger, level.lower())(json.dumps(log_entry))
    
    @contextmanager
    def timer(self, operation: str, **context):
        """Context manager for timing operations."""
        start_time = time.time()
        start_ms = int(start_time * 1000)
        
        self.log_structured("info", f"Starting {operation}", operation=operation, **context)
        
        try:
            yield
            
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            
            self.record_metric("timer", f"{operation}_duration_ms", duration_ms)
            self.log_structured(
                "info", 
                f"Completed {operation}",
                operation=operation,
                duration_ms=duration_ms,
                **context
            )
            
        except Exception as e:
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            
            self.record_metric("counter", f"{operation}_errors", 1)
            self.log_structured(
                "error",
                f"Failed {operation}",
                operation=operation,
                duration_ms=duration_ms,
                error=str(e),
                **context
            )
            raise
    
    def record_metric(self, metric_type: str, name: str, value: float, labels: Dict[str, str] = None):
        """Record a metric value."""
        labels = labels or {}
        
        metric_key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        
        if metric_type == "counter":
            self.metrics["counters"][metric_key] = self.metrics["counters"].get(metric_key, 0) + value
        elif metric_type == "gauge":
            self.metrics["gauges"][metric_key] = value
        elif metric_type == "histogram" or metric_type == "timer":
            if metric_key not in self.metrics["histograms"]:
                self.metrics["histograms"][metric_key] = []
            self.metrics["histograms"][metric_key].append(value)
        
        self.log_structured(
            "debug",
            f"Recorded {metric_type} metric",
            metric_name=name,
            value=value,
            labels=labels
        )
    
    def track_api_call(self, service: str, endpoint: str, method: str, 
                      status_code: int, response_time_ms: int, 
                      cost: float = 0.0, user_id: str = None):
        """Track API call metrics."""
        metric = APICallMetric(
            service=service,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            cost=cost,
            user_id=user_id
        )
        
        self.metrics["api_calls"].append(metric)
        
        # Record aggregate metrics
        self.record_metric("counter", "api_calls_total", 1, {
            "service": service,
            "endpoint": endpoint,
            "status": str(status_code)
        })
        
        self.record_metric("histogram", "api_response_time_ms", response_time_ms, {
            "service": service,
            "endpoint": endpoint
        })
        
        if cost > 0:
            self.record_metric("counter", "api_cost_total", cost, {
                "service": service
            })
        
        self.log_structured(
            "info",
            "API call tracked",
            service=service,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            cost=cost
        )
    
    def track_ingest_run(self, source: str, run_type: str, jobs_discovered: int = 0,
                        jobs_processed: int = 0, jobs_matched: int = 0,
                        error_count: int = 0, execution_time_ms: int = 0):
        """Track job ingestion run metrics."""
        metric = IngestRunMetric(
            source=source,
            run_type=run_type,
            jobs_discovered=jobs_discovered,
            jobs_processed=jobs_processed,
            jobs_matched=jobs_matched,
            error_count=error_count,
            execution_time_ms=execution_time_ms
        )
        
        self.metrics["ingest_runs"].append(metric)
        
        # Record business metrics
        self.record_metric("counter", "jobs_discovered_total", jobs_discovered, {"source": source})
        self.record_metric("counter", "jobs_processed_total", jobs_processed, {"source": source})
        self.record_metric("counter", "jobs_matched_total", jobs_matched, {"source": source})
        self.record_metric("counter", "ingest_errors_total", error_count, {"source": source})
        
        self.log_structured(
            "info",
            "Ingest run completed",
            source=source,
            run_type=run_type,
            jobs_discovered=jobs_discovered,
            jobs_processed=jobs_processed,
            jobs_matched=jobs_matched,
            error_count=error_count,
            execution_time_ms=execution_time_ms
        )
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get system health metrics."""
        # Calculate recent error rates
        recent_api_calls = [
            call for call in self.metrics["api_calls"]
            if call.timestamp > datetime.now() - timedelta(minutes=5)
        ]
        
        recent_errors = len([call for call in recent_api_calls if call.status_code >= 400])
        error_rate = recent_errors / max(len(recent_api_calls), 1)
        
        # Calculate average response times
        if recent_api_calls:
            avg_response_time = sum(call.response_time_ms for call in recent_api_calls) / len(recent_api_calls)
        else:
            avg_response_time = 0
        
        return {
            "service": self.service_name,
            "timestamp": datetime.now().isoformat(),
            "health": "healthy" if error_rate < 0.05 else "degraded",
            "metrics": {
                "recent_api_calls": len(recent_api_calls),
                "error_rate": error_rate,
                "avg_response_time_ms": avg_response_time,
                "total_counters": len(self.metrics["counters"]),
                "total_gauges": len(self.metrics["gauges"]),
                "total_histograms": len(self.metrics["histograms"])
            }
        }
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        if format == "json":
            # Convert dataclasses to dicts for JSON serialization
            exportable = {
                "service": self.service_name,
                "timestamp": datetime.now().isoformat(),
                "counters": self.metrics["counters"],
                "gauges": self.metrics["gauges"],
                "histograms": {k: {"count": len(v), "sum": sum(v), "avg": sum(v)/len(v) if v else 0} 
                              for k, v in self.metrics["histograms"].items()},
                "recent_api_calls": len(self.metrics["api_calls"]),
                "recent_ingest_runs": len(self.metrics["ingest_runs"])
            }
            return json.dumps(exportable, indent=2)
        
        # Add Prometheus format if needed
        return "Format not supported"