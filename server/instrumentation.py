"""
Instrumentation for OpenTelemetry and gRPC as Dynamic Tracing and Metrics decorators
"""
import logging
from functools import wraps
from opentelemetry.trace import Status, StatusCode
import grpc

logger = logging.getLogger(__name__)


def traced_and_measured(tracer, request_counter, span_name_func, metric_attrs_func):
    """
    Decorator for tracing and measuring a function using OpenTelemetry.

    This decorator provides a default implementation of tracing and metrics instrumentation.
    It expects four arguments:

    - `tracer`: a function that takes an instance of the class and returns an `opentelemetry.trace.Tracer`
    - `request_counter`: a function that takes an instance of the class and returns an `opentelemetry.metrics.Meter`
    - `span_name_func`: a function that takes the function arguments and returns a name for the span
    - `metric_attrs_func`: a function that takes the function arguments and returns a dictionary of attributes to set on the span and metric

    The decorator expects the function being decorated to have the following signature:

    - The first argument is an instance of the class
    - The second argument is the request object
    - The third argument is the gRPC context (optional)

    The decorator will:

    - Start a span with the name returned by `span_name_func`
    - Set attributes on the span from the dictionary returned by `metric_attrs_func`
    - Set the span status to OK if no error is encountered, or ERROR if an error occurs
    - Increment the metric counter returned by `request_counter` with the attributes from `metric_attrs_func`
    """

    def decorator(func):
        """
        Decorator to instrument a function with OpenTelemetry tracing and metrics.

        It wraps the original function, adding tracing and metrics instrumentation.
        If the original function is a coroutine, the wrapped function will also be a coroutine.

        :param func: The function to be instrumented
        :return: The wrapped function with tracing and metrics
        """

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """
            Async wrapper for a function that starts a span and sets attributes based on the provided functions.
            It also handles error recording based on gRPC context and increments metric counters.

            :param func: The function to be instrumented
            :return: The result of the original function
            """
            instance = args[0]
            actual_tracer = tracer(instance)
            actual_request_counter = request_counter(instance)
            span_name = span_name_func(args)
            attributes = metric_attrs_func(args)

            with actual_tracer.start_as_current_span(span_name) as span:
                _set_span_attributes(span, attributes)
                logger.info(f"Starting span '{span_name}' with attributes {attributes}")

                _increment_metrics(actual_request_counter, attributes)

                try:
                    result = await func(*args, **kwargs)
                    _handle_span_status(span, args)
                except Exception as e:
                    _record_exception(span, e)
                    raise

                logger.info(f"Completed span '{span_name}'")
                return result

        return async_wrapper

    return decorator


def _set_span_attributes(span, attributes):
    """
    Sets multiple attributes on the given span.

    :param span: The OpenTelemetry span
    :param attributes: A dictionary of attributes to set on the span
    """
    for key, value in attributes.items():
        span.set_attribute(key, value)


def _increment_metrics(counter, attributes):
    """
    Increments the metric counter with the provided attributes.

    :param counter: The OpenTelemetry meter counter
    :param attributes: A dictionary of attributes for the metric
    """
    counter.add(1, attributes)


def _handle_span_status(span, args):
    """
    Handles setting the span status based on the gRPC context.

    :param span: The OpenTelemetry span
    :param args: The arguments passed to the original function
    """
    context = args[2] if len(args) > 2 else None
    if context:
        error_code = context.code()
        error_details = context.details()
        if error_code and error_code != grpc.StatusCode.OK:
            span.set_status(Status(StatusCode.ERROR, f"gRPC error: {error_code}, details: {error_details}"))
            _set_error_attributes(span, error_code, error_details)
            logger.error(f"Span completed with error: {error_code} - {error_details}")
        else:
            span.set_status(Status(StatusCode.OK))
    else:
        span.set_status(Status(StatusCode.OK))


def _set_error_attributes(span, error_code, error_details):
    """
    Sets error-related attributes on the span.

    :param span: The OpenTelemetry span
    :param error_code: The gRPC error code
    :param error_details: The gRPC error details
    """
    span.set_attribute("error", True)
    span.set_attribute("error.code", str(error_code.value))  # Numeric code
    span.set_attribute("error.description", error_details)


def _record_exception(span, exception):
    """
    Records an exception on the span and sets its status to ERROR.

    :param span: The OpenTelemetry span
    :param exception: The exception to record
    """
    span.record_exception(exception)
    span.set_status(Status(StatusCode.ERROR, str(exception)))
    span.set_attribute("error", True)
    logger.error(f"Exception recorded in span: {exception}")
def dynamic_span_name(args):
    """
    Construct a string name for a span, given arguments passed to an RPC method.

    The name is in the format "Handler: <service_name>.<method_name>".
    If the request has a DESCRIPTOR with a full_name, that is used; otherwise
    the class name of the request is used.

    :param args: The arguments passed to the RPC method
    :return: A string name for the span
    """
    service_name = args[0].__class__.__name__
    # If the request has a DESCRIPTOR with full_name, use it; otherwise fallback to class name
    method_id = getattr(args[1], 'DESCRIPTOR', args[1].__class__).full_name \
        if hasattr(args[1], 'DESCRIPTOR') else args[1].__class__.__name__
    return f"Handler: {service_name}.{method_id}"


def _get_endpoint_attrs(service_name, request_type):
    """
    Construct a dictionary of attributes related to the endpoint being called.

    The dictionary contains a single key-value pair, where the key is
    "endpoint" and the value is a string of the form
    "<service_name>.<request_type>".

    :param service_name: The name of the service implementing the endpoint.
    :type service_name: str
    :param request_type: The name of the request message type.
    :type request_type: str
    :returns: A dictionary of attributes.
    :rtype: dict[str, str]
    """
    return {"endpoint": f"{service_name}.{request_type}"}


def _get_protobuf_attrs(request):
    """
    Extract a dictionary of attributes from a Protobuf message.

    The dictionary contains a key-value pair for each field in the message.
    The key is the name of the field and the value is a string representation
    of the field's value (or "unknown" if the field is not set).

    :param request: The Protobuf message to extract attributes from.
    :type request: google.protobuf.message.Message
    :returns: A dictionary of extracted attributes.
    :rtype: dict[str, str]
    """
    attrs = {}
    # Iterate over the fields in the message
    for field in request.DESCRIPTOR.fields:
        # Get the name and value of the field
        field_name = field.name
        field_value = getattr(request, field_name, None)
        attrs[field_name] = str(field_value) if field_value is not None else "unknown"
    return attrs

def _get_generic_attrs(request):
    """
    Extract a dictionary of attributes from a generic object using its
    public (non-private) attributes. This is a fallback strategy for
    objects that do not have a `DESCRIPTOR` field.

    :param request: The object to extract attributes from.
    :type request: object
    :returns: A dictionary of extracted attributes.
    :rtype: dict[str, str]
    """
    attrs = {}
    # Iterate over the public (non-private) attributes of the object
    for attr_name in dir(request):
        if not attr_name.startswith("_") and not callable(getattr(request, attr_name)):
            field_value = getattr(request, attr_name, None)
            attrs[attr_name] = str(field_value) if field_value is not None else "unknown"
    return attrs

def dynamic_metric_attrs(args):
    """
    Construct a dictionary of attributes for a metric, given arguments passed to an RPC method.

    The dictionary contains a key-value pair for each field in the message, plus the endpoint
    information. The key is the name of the field and the value is a string representation
    of the field's value (or "unknown" if the field is not set).

    :param args: The arguments passed to the RPC method
    :return: A dictionary of attributes.
    :rtype: dict[str, str]
    """
    # Extract the arguments from the args tuple 
    request = args[1]
    service_name = args[0].__class__.__name__
    request_type = request.__class__.__name__

    # Construct the endpoint attributes
    attrs = _get_endpoint_attrs(service_name, request_type)
    # If the request has a DESCRIPTOR with full_name, use it; otherwise fallback to class name
    if hasattr(request, 'DESCRIPTOR'):
        # Extract attributes from the Protobuf message
        attrs.update(_get_protobuf_attrs(request))
    else:
        # Extract attributes from the generic object
        attrs.update(_get_generic_attrs(request))

    return attrs
