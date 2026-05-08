from bot.config import BotSettings

_tracing_configured = False


def setup_tracing(service_name: str) -> None:
    global _tracing_configured
    if _tracing_configured:
        return
    settings = BotSettings()
    if not settings.otel_enabled or not settings.otel_exporter_otlp_endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        span_exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(span_exporter))
        trace.set_tracer_provider(provider)
        _tracing_configured = True
    except Exception:
        # Tracing should never block runtime pipeline.
        return
