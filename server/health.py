"""
This module provides a function to add a health check to a gRPC server.
"""
from grpc_health.v1 import health, health_pb2_grpc, health_pb2

def add_health_check(server):
    """
    Add a health check to the given gRPC server.

    The health check returns a SERVING status for all services.

    :param server: The gRPC server to add the health check to.
    :type server: grpc.Server
    """
    health_servicer = health.HealthServicer()
    # Set the health status to SERVING
    health_servicer.set('', health_pb2.HealthCheckResponse.SERVING)
    # Add the health servicer to the server
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
