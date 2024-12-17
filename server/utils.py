"""
This module provides utility functions for the server.
* Logging configuration
"""
import logging
import sys

def setup_logging()-> None:
    """
    Configures the logging for the server.

    This function sets up the logging to output to standard output (sys.stdout) with
    an INFO level, using a specified format that includes the timestamp, log level,
    logger name, and the log message.
    """
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )