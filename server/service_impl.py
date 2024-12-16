import asyncio
import grpc

from .config import (
    CLICKHOUSE_HOST, CLICKHOUSE_PORT,
    CLICKHOUSE_USER, CLICKHOUSE_PASSWORD,
    CLICKHOUSE_DATABASE
)
from .ch_handler import ClickhouseHandler
from .models import GetUserRequestModel, ListUsersRequestModel, InsertUserRequestModel
from myservice_pb2 import User as UserProto, GetUserResponse, ListUsersResponse, Empty
from .instrumentation import traced_and_measured, dynamic_span_name, dynamic_metric_attrs

import myservice_pb2_grpc

handler = ClickhouseHandler(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DATABASE
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
            return GetUserResponse()

        query = "SELECT id, username, email FROM users WHERE id = %(id)s"
        params = {"id": validated.user_id}
        rows = await asyncio.to_thread(handler.select, query, params)

        if not rows:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("User not found")
            return GetUserResponse()

        row = rows[0]
        user_proto = UserProto(id=row["id"], username=row["username"], email=row["email"])
        return GetUserResponse(user=user_proto)

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
            return ListUsersResponse()

        offset = (validated.page - 1) * validated.page_size
        limit = validated.page_size

        query = "SELECT id, username, email FROM users ORDER BY id LIMIT %(limit)s OFFSET %(offset)s"
        params = {"limit": limit, "offset": offset}
        rows = await asyncio.to_thread(handler.select, query, params)

        total_query = "SELECT count(*) as cnt FROM users"
        total_rows = await asyncio.to_thread(handler.select, total_query)
        total = total_rows[0]["cnt"] if total_rows else 0

        users = [
            UserProto(id=row["id"], username=row["username"], email=row["email"]) for row in rows
        ]
        return ListUsersResponse(users=users, total=total)

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
            return Empty()

        # Construct the raw query string
        insert_query = f"INSERT INTO users (username, email) VALUES ('{validated.username}', '{validated.email}')"

        # Use the execute method
        await asyncio.to_thread(handler.execute, insert_query)

        return Empty()


