import logging
from functools import wraps
from opentelemetry.trace import Status, StatusCode
import grpc

logger = logging.getLogger(__name__)

def traced_and_measured(tracer, request_counter, span_name_func, metric_attrs_func):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            instance = args[0]

            actual_tracer = tracer(instance)
            actual_request_counter = request_counter(instance)

            span_name = span_name_func(args)
            attributes = metric_attrs_func(args)

            with actual_tracer.start_as_current_span(span_name) as span:
                # Set attributes on the span
                for k, v in attributes.items():
                    span.set_attribute(k, v)

                logger.info(f"Starting {span_name} with attributes {attributes}")

                # Increment the metric counter with dynamic attributes
                actual_request_counter.add(1, attributes)

                # Execute the actual function
                result = await func(*args, **kwargs)

                # Get the gRPC context from the arguments, typically args[2]
                # Adjust if your method signature differs
                context = args[2] if len(args) > 2 else None

                if context is not None:
                    # Use public methods to get code and details
                    error_code = context.code()
                    error_details = context.details()
                    # If the code is not OK, record an error on the span
                    if (error_code is not None) and (grpc.StatusCode.OK != error_code):
                        span.set_status(Status(StatusCode.ERROR, f"gRPC error: {error_code}, details: {error_details}"))
                        span.set_attribute("error", True)
                        span.set_attribute("error.code", f"{error_code}")  # numeric code
                        span.set_attribute("error.description", error_details)

                        logger.error(f"Span {span_name} completed with error: {error_code} - {error_details}")
                    else:
                        # If the code is OK, explicitly mark span as successful
                        span.set_status(Status(StatusCode.OK))
                else:
                    # If no context is available, just set span to OK
                    span.set_status(Status(StatusCode.OK))

                logger.info(f"Completed {span_name}")
                return result

        return async_wrapper
    return decorator



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


def get_endpoint_attrs(service_name, request_type):
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


def get_protobuf_attrs(request):
    attrs = {}
    for field in request.DESCRIPTOR.fields:
        field_name = field.name
        field_value = getattr(request, field_name, None)
        attrs[field_name] = str(field_value) if field_value is not None else "unknown"
    return attrs

def get_generic_attrs(request):
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
    for attr_name in dir(request):
        if not attr_name.startswith("_") and not callable(getattr(request, attr_name)):
            field_value = getattr(request, attr_name, None)
            attrs[attr_name] = str(field_value) if field_value is not None else "unknown"
    return attrs

def dynamic_metric_attrs(args):
    request = args[1]
    service_name = args[0].__class__.__name__
    request_type = request.__class__.__name__

    attrs = get_endpoint_attrs(service_name, request_type)

    if hasattr(request, 'DESCRIPTOR'):
        attrs.update(get_protobuf_attrs(request))
    else:
        attrs.update(get_generic_attrs(request))

    return attrs
