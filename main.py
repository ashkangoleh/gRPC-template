"""
main file to run the gRPC server with OpenTelemetry
"""
import asyncio
import grpc
from grpc_reflection.v1alpha import reflection
from opentelemetry.instrumentation.grpc import GrpcAioInstrumentorServer

import myservice_pb2
import myservice_pb2_grpc

from server.service_impl import UserService
from server.config import settings
from server import setup_tracing_and_metrics
from server import LoggingInterceptor
from server import add_health_check
from server import setup_logging

async def serve():
    setup_logging()
    # setup_instrumentation returns tracer and request_counter
    tracer, request_counter = setup_tracing_and_metrics()

    # Instrument the gRPC server
    GrpcAioInstrumentorServer().instrument()

    interceptors = [LoggingInterceptor()]
    server = grpc.aio.server(interceptors=interceptors)

    # Pass the tracer and request_counter into UserService
    user_service = UserService(tracer, request_counter)
    myservice_pb2_grpc.add_UserServiceServicer_to_server(user_service, server)

    # Reflection
    SERVICE_NAMES = (
        myservice_pb2.DESCRIPTOR.services_by_name['UserService'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    # Health Check
    add_health_check(server)

    listen_addr = f"{settings.GRPC_SERVER_HOST}:{settings.GRPC_SERVER_PORT}"
    print(f"Starting gRPC server on {listen_addr}")
    server.add_insecure_port(listen_addr)

    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
