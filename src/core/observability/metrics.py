"""
Enhanced Metrics Collection

Prometheus-compatible metrics for observability.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Try to import Prometheus, fallback to basic metrics
try:
    from prometheus_client import Counter, Histogram, Gauge, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus not available, using basic metrics")


@dataclass
class MetricValue:
    """A metric value with timestamp."""
    value: float
    timestamp: datetime
    labels: dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Enhanced metrics collector.
    
    Uses Prometheus if available, otherwise basic in-memory metrics.
    """
    
    def __init__(self, use_prometheus: bool = True):
        self.use_prometheus = use_prometheus and PROMETHEUS_AVAILABLE
        
        if self.use_prometheus:
            self._init_prometheus()
        else:
            self._init_basic()
    
    def _init_prometheus(self) -> None:
        """Initialize Prometheus metrics."""
        # Counters
        self.task_counter = Counter(
            "devops_brain_tasks_total",
            "Total number of tasks",
            ["agent", "status", "action"],
        )
        self.llm_requests = Counter(
            "devops_brain_llm_requests_total",
            "Total LLM requests",
            ["provider", "model"],
        )
        self.errors = Counter(
            "devops_brain_errors_total",
            "Total errors",
            ["component", "error_type"],
        )
        
        # Histograms
        self.task_duration = Histogram(
            "devops_brain_task_duration_seconds",
            "Task execution duration",
            ["agent", "action"],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
        )
        self.llm_latency = Histogram(
            "devops_brain_llm_latency_seconds",
            "LLM request latency",
            ["provider", "model"],
        )
        
        # Gauges
        self.active_tasks = Gauge(
            "devops_brain_active_tasks",
            "Currently active tasks",
            ["agent"],
        )
        self.queue_size = Gauge(
            "devops_brain_queue_size",
            "Message queue size",
        )
        
        logger.info("Prometheus metrics initialized")
    
    def _init_basic(self) -> None:
        """Initialize basic in-memory metrics."""
        self._counters: dict[str, dict] = defaultdict(lambda: defaultdict(int))
        self._histograms: dict[str, list] = defaultdict(list)
        self._gauges: dict[str, float] = {}
        logger.info("Basic metrics initialized")
    
    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[dict] = None,
    ) -> None:
        """Increment a counter."""
        if self.use_prometheus:
            # Prometheus counters are handled by Counter objects
            return
        
        key = self._make_key(name, labels)
        self._counters[name][key] += value
    
    def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[dict] = None,
    ) -> None:
        """Record a histogram value."""
        if self.use_prometheus:
            # Prometheus histograms are handled by Histogram objects
            return
        
        key = self._make_key(name, labels)
        self._histograms[name].append(MetricValue(value, datetime.utcnow(), labels or {}))
        
        # Keep only last 1000 values
        if len(self._histograms[name]) > 1000:
            self._histograms[name] = self._histograms[name][-1000:]
    
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[dict] = None,
    ) -> None:
        """Set a gauge value."""
        if self.use_prometheus:
            # Prometheus gauges are handled by Gauge objects
            return
        
        key = self._make_key(name, labels)
        self._gauges[key] = value
    
    def _make_key(self, name: str, labels: Optional[dict]) -> str:
        """Create a key from name and labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics(self) -> dict[str, Any]:
        """Get all metrics."""
        if self.use_prometheus:
            # Prometheus metrics are exposed via /metrics endpoint
            return {"type": "prometheus", "endpoint": "/metrics"}
        
        return {
            "type": "basic",
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: {
                    "count": len(values),
                    "min": min(v.value for v in values) if values else 0,
                    "max": max(v.value for v in values) if values else 0,
                    "avg": sum(v.value for v in values) / len(values) if values else 0,
                }
                for name, values in self._histograms.items()
            },
        }


# Global metrics collector
_global_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector."""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector()
    return _global_metrics
