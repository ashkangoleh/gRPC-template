"""
service_impl.py / server module for the gRPC server
"""
import asyncio
import grpc
import importlib.util
from pathlib import Path
from .ch_handler import ClickhouseHandler
from .models import GetUserRequestModel, ListUsersRequestModel, InsertUserRequestModel
from .instrumentation import traced_and_measured, dynamic_span_name, dynamic_metric_attrs
from server.config import settings

# Dynamic loading of myservice_pb2 and myservice_pb2_grpc
def load_pb2_modules():
    root_dir = Path(__file__).parent.parent  # Adjust path to project root
    pb2_modules = {}

    for pb_file in root_dir.rglob("*_pb2.py"):
        module_name = pb_file.stem
        if module_name not in pb2_modules:  # Avoid overwriting modules
            spec = importlib.util.spec_from_file_location(module_name, pb_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            pb2_modules[module_name] = module

    for pb_grpc_file in root_dir.rglob("*_pb2_grpc.py"):
        module_name = pb_grpc_file.stem
        if module_name not in pb2_modules:  # Avoid overwriting modules
            spec = importlib.util.spec_from_file_location(module_name, pb_grpc_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            pb2_modules[module_name] = module

    return pb2_modules

def get_module(pb2_modules, name):
    if name not in pb2_modules:
        available_modules = ", ".join(pb2_modules.keys())
        raise ImportError(f"Required module '{name}' not found. Available modules: [{available_modules}]. Check proto file generation.")
    return pb2_modules[name]

pb2_modules = load_pb2_modules()
print(f"Loaded modules: {list(pb2_modules.keys())}")

myservice_pb2 = get_module(pb2_modules, "myservice_pb2")
myservice_pb2_grpc = get_module(pb2_modules, "myservice_pb2_grpc")

handler = ClickhouseHandler(
    host=settings.CLICKHOUSE_HOST,
    port=settings.CLICKHOUSE_PORT,
    user=settings.CLICKHOUSE_USER,
    password=settings.CLICKHOUSE_PASSWORD,
    database=settings.CLICKHOUSE_DATABASE
)

class UserService(myservice_pb2_grpc.UserServiceServicer):
    def __init__(self, tracer, request_counter):
        self._tracer = tracer
        self._request_counter = request_counter

    @traced_and_measured(
        tracer=lambda self: self._tracer,
        request_counter=lambda self: self._request_counter,
        span_name_func=dynamic_span_name,
        metric_attrs_func=dynamic_metric_attrs
    )
    async def GetUser(self, request, context):
        req_data = {"user_id": request.user_id}
        try:
            validated = GetUserRequestModel(**req_data)
        except Exception as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return myservice_pb2.GetUserResponse()

        query = "SELECT id, username, email FROM users WHERE id = %(id)s"
        params = {"id": validated.user_id}
        rows = await asyncio.to_thread(handler.select, query, params)

        if not rows:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("User not found")
            return myservice_pb2.GetUserResponse()

        row = rows[0]
        user_proto = myservice_pb2.User(id=row["id"], username=row["username"], email=row["email"])
        return myservice_pb2.GetUserResponse(user=user_proto)

    @traced_and_measured(
        tracer=lambda self: self._tracer,
        request_counter=lambda self: self._request_counter,
        span_name_func=dynamic_span_name,
        metric_attrs_func=dynamic_metric_attrs
    )
    async def ListUsers(self, request, context):
        req_data = {"page": request.page, "page_size": request.page_size}
        try:
            validated = ListUsersRequestModel(**req_data)
        except Exception as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return myservice_pb2.ListUsersResponse()

        offset = (validated.page - 1) * validated.page_size
        limit = validated.page_size

        query = "SELECT id, username, email FROM users ORDER BY id LIMIT %(limit)s OFFSET %(offset)s"
        params = {"limit": limit, "offset": offset}
        rows = await asyncio.to_thread(handler.select, query, params)

        total_query = "SELECT count(*) as cnt FROM users"
        total_rows = await asyncio.to_thread(handler.select, total_query)
        total = total_rows[0]["cnt"] if total_rows else 0

        users = [
            myservice_pb2.User(id=row["id"], username=row["username"], email=row["email"])
            for row in rows
        ]
        return myservice_pb2.ListUsersResponse(users=users, total=total)

    @traced_and_measured(
        tracer=lambda self: self._tracer,
        request_counter=lambda self: self._request_counter,
        span_name_func=dynamic_span_name,
        metric_attrs_func=dynamic_metric_attrs
    )
    async def InsertUser(self, request, context):
        req_data = {"username": request.username, "email": request.email}
        try:
            validated = InsertUserRequestModel(**req_data)
        except Exception as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return myservice_pb2.Empty()

        insert_query = "INSERT INTO users (username, email) VALUES (%(username)s, %(email)s)"
        params = {"username": validated.username, "email": validated.email}
        await asyncio.to_thread(handler.execute, insert_query, params)

        return myservice_pb2.Empty()
