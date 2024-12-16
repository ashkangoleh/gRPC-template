import os
from dotenv import load_dotenv

from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GrpcSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter as GrpcMetricExporter

load_dotenv()

SERVICE_NAME = os.getenv("SERVICE_NAME", "my-service")

def setup_tracing_and_metrics():
    resource = Resource(attributes={"service.name": SERVICE_NAME})
    grpc_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
    grpc_protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")

    # Setup Tracing
    tracer_provider = TracerProvider(resource=resource)
    if grpc_protocol == "grpc":
        span_exporter = GrpcSpanExporter(endpoint=grpc_endpoint, insecure=True)
        tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Setup Metrics
    if grpc_protocol == "grpc":
        metric_exporter = GrpcMetricExporter(endpoint=grpc_endpoint, insecure=True)
        metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    else:
        meter_provider = MeterProvider(resource=resource)
    metrics.set_meter_provider(meter_provider)

    # Load the metric description dynamically from environment
    requests_total_description = os.getenv(
        "REQUESTS_TOTAL_DESCRIPTION",
        "Number of requests processed by the UserService"
    )

    global_meter = metrics.get_meter(__name__)
    request_counter = global_meter.create_counter(
        name="requests_total",
        unit="1",
        description=requests_total_description
    )

    tracer = trace.get_tracer(__name__)
    return tracer, request_counter
