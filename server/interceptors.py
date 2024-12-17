"""
This module provides a logging interceptor for gRPC servers.
"""
import grpc
import logging

class LoggingInterceptor(grpc.aio.ServerInterceptor):
    async def intercept_service(self, continuation, handler_call_details)-> None:
        """
        Intercepts gRPC service calls to log request and response details.

        This asynchronous method is part of a gRPC server interceptor. It logs
        a message when a call is received and another message when the call is
        completed. The `continuation` function is used to proceed with the call
        to the next interceptor in the chain or the actual RPC handler.

        :param continuation: A function that proceeds with the next interceptor or the RPC handler.
        :param handler_call_details: Provides information about the RPC being called, including the method.
        :return: The response from the continuation of the call.
        """
        logging.info(f"Received call to {handler_call_details.method}")
        # Call the next interceptor in the chain
        response = await continuation(handler_call_details)
        logging.info("Completed call")
        return response