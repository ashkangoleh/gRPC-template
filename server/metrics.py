"""
Module for setting up tracing and metrics for the application using OpenTelemetry.
"""
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GrpcSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter as GrpcMetricExporter
from server.config import settings

def setup_tracing_and_metrics():
    """
    Sets up tracing and metrics for the application using OpenTelemetry.

    This function configures a tracing provider and a metrics provider
    based on the service settings. It exports traces and metrics via
    OTLP over gRPC if the protocol is set to "grpc" in the settings.

    Tracing:
    - Configures a TracerProvider with a resource indicating the service name.
    - Sets up a BatchSpanProcessor with a GrpcSpanExporter to export spans to
      the specified gRPC endpoint.

    Metrics:
    - Configures a MeterProvider with a PeriodicExportingMetricReader and a
      GrpcMetricExporter if the protocol is "grpc". Otherwise, configures a
      basic MeterProvider.
    - Creates a global meter and a request counter with the description from
      the settings.

    Returns:
        tracer (Tracer): An OpenTelemetry Tracer instance for creating spans.
        request_counter (Counter): A Counter instrument for counting requests.
    """
    # Setup Resource
    resource = Resource(attributes={"service.name": settings.SERVICE_NAME})
    # Setup Tracing
    tracer_provider = TracerProvider(resource=resource)
    if settings.OTEL_EXPORTER_OTLP_PROTOCOL == "grpc":
        # Span exporter for gRPC
        span_exporter = GrpcSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True)
        # Span processor
        tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    # Set the TracerProvider to the OpenTelemetry
    trace.set_tracer_provider(tracer_provider)

    # Setup Metrics
    if settings.OTEL_EXPORTER_OTLP_PROTOCOL == "grpc":
        # Metric exporter for gRPC
        metric_exporter = GrpcMetricExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True)
        # Metric reader with export interval of 5 seconds
        metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
        # Meter provider with metric reader and resource
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    else:
        # Meter provider with resource only
        meter_provider = MeterProvider(resource=resource)
    # Set the MeterProvider to the OpenTelemetry
    metrics.set_meter_provider(meter_provider)

    # Create Tracer and Counter for requests
    global_meter = metrics.get_meter(__name__)
    request_counter = global_meter.create_counter(
        name="requests_total",
        unit="1",
        description=settings.REQUESTS_TOTAL_DESCRIPTION
    )
    # Return Tracer and Counter instances
    tracer = trace.get_tracer(__name__)
    return tracer, request_counter
