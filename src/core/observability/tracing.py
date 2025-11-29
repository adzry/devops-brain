"""
Distributed Tracing

OpenTelemetry-based tracing for request tracking across services.
"""

import logging
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry, fallback to no-op if not available
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logger.warning("OpenTelemetry not available, tracing disabled")


class Tracer:
    """
    Distributed tracing wrapper.
    
    Uses OpenTelemetry if available, otherwise no-op.
    """
    
    def __init__(self, service_name: str = "devops-brain", enabled: bool = True):
        self.service_name = service_name
        self.enabled = enabled and OPENTELEMETRY_AVAILABLE
        
        if self.enabled:
            try:
                resource = Resource.create({"service.name": service_name})
                provider = TracerProvider(resource=resource)
                trace.set_tracer_provider(provider)
                
                # Add OTLP exporter (can be configured)
                # exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
                # provider.add_span_processor(BatchSpanProcessor(exporter))
                
                self._tracer = trace.get_tracer(service_name)
                logger.info(f"Tracing enabled for {service_name}")
            except Exception as e:
                logger.error(f"Failed to initialize tracing: {e}")
                self.enabled = False
        else:
            self._tracer = None
    
    @contextmanager
    def span(self, name: str, attributes: Optional[dict] = None):
        """
        Create a trace span.
        
        Usage:
            with tracer.span("task_execution", {"task_id": "123"}):
                # Do work
                pass
        """
        if not self.enabled or not self._tracer:
            yield
            return
        
        with self._tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
            yield span
    
    def add_event(self, name: str, attributes: Optional[dict] = None) -> None:
        """Add an event to the current span."""
        if not self.enabled:
            return
        
        try:
            span = trace.get_current_span()
            if span:
                span.add_event(name, attributes or {})
        except Exception:
            pass  # Silently fail if no span
    
    def set_attribute(self, key: str, value: str) -> None:
        """Set an attribute on the current span."""
        if not self.enabled:
            return
        
        try:
            span = trace.get_current_span()
            if span:
                span.set_attribute(key, value)
        except Exception:
            pass


# Global tracer instance
_global_tracer: Optional[Tracer] = None


def get_tracer(service_name: str = "devops-brain") -> Tracer:
    """Get the global tracer instance."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer(service_name)
    return _global_tracer
