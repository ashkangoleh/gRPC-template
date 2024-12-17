"""
main file to run the gRPC server with OpenTelemetry
"""
import asyncio
import grpc
import importlib.util
from typing import Dict
from pathlib import Path
from grpc_reflection.v1alpha import reflection
from opentelemetry.instrumentation.grpc import GrpcAioInstrumentorServer # noqa

from server.service_impl import UserService
from server.config import settings
from server import setup_tracing_and_metrics
from server import LoggingInterceptor
from server import add_health_check
from server import setup_logging

def load_pb2_files():
    """
    Dynamically loads all *_pb2.py and *_pb2_grpc.py files from the current directory.
    """
    pb2_modules = {}
    current_dir = Path(__file__).parent  # Set to current directory

    # Load *_pb2.py files
    for pb2_file in current_dir.glob("*_pb2.py"):
        module_name = pb2_file.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name, pb2_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            pb2_modules[module_name] = module
            print(f"Loaded module: {module_name}")
        except Exception as e:
            print(f"Failed to load module {module_name}: {e}")

    # Load *_pb2_grpc.py files
    for pb2_grpc_file in current_dir.glob("*_pb2_grpc.py"):
        module_name = pb2_grpc_file.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name, pb2_grpc_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            pb2_modules[module_name] = module
            print(f"Loaded module: {module_name}")
        except Exception as e:
            print(f"Failed to load module {module_name}: {e}")

    return pb2_modules

def get_service_names(pb2_modules):
    """
    Dynamically fetch all available service names from loaded pb2 modules
    """
    service_names = []
    for module in pb2_modules.values():
        if hasattr(module, "DESCRIPTOR") and module.DESCRIPTOR.services_by_name:
            for service in module.DESCRIPTOR.services_by_name.values():
                service_names.append(service.full_name)
    return service_names

def load_required_services(pb2_modules):
    """
    Load required services and fallback if not found.
    """
    pb2_grpc_module = None
    pb2_module = None
    if isinstance(pb2_modules,Dict):
        for k,v in pb2_modules.items():
            if k.endswith("grpc"):
                pb2_grpc_module = pb2_modules.get(k)
            elif k.endswith("pb2"):
                pb2_module = pb2_modules.get(k)
    if not pb2_module or not pb2_grpc_module:
        raise ImportError("Failed to dynamically load required pb2 or pb2_grpc modules. Check proto generation.")
    return pb2_module, pb2_grpc_module

async def serve():
    setup_logging()
    # setup_instrumentation returns tracer and request_counter
    tracer, request_counter = setup_tracing_and_metrics()

    # Instrument the gRPC server
    GrpcAioInstrumentorServer().instrument()

    interceptors = [LoggingInterceptor()]
    server = grpc.aio.server(interceptors=interceptors)

    # Load pb2 dynamically and add services
    pb2_modules = load_pb2_files()
    _, pb2_grpc_module = load_required_services(pb2_modules)

    user_service = UserService(tracer, request_counter)
    pb2_grpc_module.add_UserServiceServicer_to_server(user_service, server)

    # Reflection with dynamic service names
    service_names = get_service_names(pb2_modules)
    service_names.append(reflection.SERVICE_NAME)
    reflection.enable_server_reflection(service_names, server)

    # Health Check
    add_health_check(server)

    listen_addr = f"{settings.GRPC_SERVER_HOST}:{settings.GRPC_SERVER_PORT}"
    print(f"Starting gRPC server on {listen_addr}")
    server.add_insecure_port(listen_addr)

    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    # A more production-friendly asyncio entry point
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(serve())
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Error while running server: {e}")
    finally:
        print("Server shutting down gracefully")
        loop.close()
