import clickhouse_connect
from typing import Any, Dict, List, Optional

class ClickhouseHandler:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        # Initialize a synchronous or asynchronous client
        # As of now, clickhouse-connect stable version is primarily sync;
        # We'll assume sync version and run it in thread executor if needed.
        # If async support is available in your version, use that.
        self.client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=user,
            password=password,
            database=database
        )

    def select(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # For dynamic queries, user provides query and params
        # The result will be returned as list of dicts
        rows = self.client.query(query, parameters=params)
        # Convert rows to list of dict since clickhouse-connect returns a special result object
        result = [dict(zip(rows.column_names, row)) for row in rows.result_set]
        return result

    def insert(self, table: str, data: List[tuple]) -> None:
        # Use table name directly and pass data
        self.client.insert(table, data)

    def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> None:
        # For non-SELECT/INSERT queries (e.g. CREATE, DROP)
        self.client.command(query, parameters=params)