from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from .config import AppConfig

tracer = trace.get_tracer("service")


def configure_tracing(config: AppConfig) -> None:
    """Configure OpenTelemetry tracing with OTLP exporter."""
    exporter = OTLPSpanExporter(endpoint=config.jaeger_endpoint)
    provider = TracerProvider(
        resource=Resource.create({"service.name": config.jaeger_service_name})
    )
    try:
        provider.add_span_processor(BatchSpanProcessor(exporter))
    except Exception:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware creating a span for each HTTP request."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        with tracer.start_as_current_span("api_request_span"):
            return await call_next(request)
