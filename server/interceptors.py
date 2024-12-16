import grpc
import logging

class LoggingInterceptor(grpc.aio.ServerInterceptor):
    async def intercept_service(self, continuation, handler_call_details):
        logging.info(f"Received call to {handler_call_details.method}")
        response = await continuation(handler_call_details)
        logging.info("Completed call")
        return response