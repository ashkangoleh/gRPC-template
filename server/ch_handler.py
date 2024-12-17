import inspect
import clickhouse_connect
from typing import Any, Dict, List, Optional
from server import setup_logging

logger = setup_logging()

class ClickhouseHandler:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        """
        Initializes a ClickhouseHandler instance with connection details.

        Args:
            host (str): The hostname or IP address of the ClickHouse server.
            port (int): The port number of the ClickHouse server.
            user (str): The username to use for authentication.
            password (str): The password to use for authentication.
            database (str): The name of the ClickHouse database to use.
        """
        self.client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=user,
            password=password,
            database=database
        )
    def close(self) -> None:
        self.client.close()

    def select(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Executes a dynamic query on the database.

        Args:
            query: The SQL query to execute. It can contain placeholders for parameters.
            params: A dictionary of parameters to pass to the query.

        Returns:
            A list of dictionaries where each dictionary represents a row in the result set.
        """
        try:
            rows = self.client.query(query, parameters=params)
            # Convert rows to list of dict since clickhouse-connect returns a special result object
            result = [dict(zip(rows.column_names, row)) for row in rows.result_set]
            return result
        except Exception as e:
            class_name = self.__class__.__name__  # Retrieve class name
            method_name = inspect.currentframe().f_code.co_name  # Retrieve method name
            logger.error(
                f"Error executing query in {class_name}.{method_name}: {e}",
                exc_info=True  # Logs the exception traceback
            )
            raise
        finally:
            self.client.close()

    def insert(self, table: str, data: List[tuple]) -> None:
        # Use table name directly and pass data
        """
        Inserts data into the specified table in the ClickHouse database.

        Args:
            table (str): The name of the table into which data should be inserted.
            data (List[tuple]): A list of tuples, where each tuple represents a row of data to insert.

        Returns:
            None
        """
        try:
            self.client.insert(table, data)
        except Exception as e:
            class_name = self.__class__.__name__  # Retrieve class name
            method_name = inspect.currentframe().f_code.co_name  # Retrieve method name
            logger.error(
                f"Error executing query in {class_name}.{method_name}: {e}",
                exc_info=True  # Logs the exception traceback
            )
            raise
        finally:
            self.client.close()

    def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> None:
        # For non-SELECT/INSERT queries (e.g. CREATE, DROP)
        """
        Executes a dynamic query on the database that is not a SELECT/INSERT query.

        Args:
            query: The SQL query to execute. It can contain placeholders for parameters.
            params: A dictionary of parameters to pass to the query.

        Returns:
            None

        Raises:
            Exception: If the query execution fails, an exception is raised with the error message.
        """
        try:
            self.client.command(query, parameters=params)
        except Exception as e:
            class_name = self.__class__.__name__  # Retrieve class name
            method_name = inspect.currentframe().f_code.co_name  # Retrieve method name
            logger.error(
                f"Error executing query in {class_name}.{method_name}: {e}",
                exc_info=True  # Logs the exception traceback
            )
            raise
        finally:
            self.client.close()