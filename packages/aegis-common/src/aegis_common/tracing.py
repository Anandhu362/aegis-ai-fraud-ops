"""OpenTelemetry tracing setup and span helpers."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def configure_tracing(service_name: str, export_console: bool = False) -> None:
    """Initialize OpenTelemetry tracer provider."""
    provider = TracerProvider()
    if export_console:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)


def get_tracer(instrumenting_module_name: str = "aegis") -> trace.Tracer:
    """Obtain an OpenTelemetry Tracer instance."""
    return trace.get_tracer(instrumenting_module_name)
