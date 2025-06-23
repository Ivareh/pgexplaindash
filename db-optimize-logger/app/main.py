from db import process_databases, read_database_instances
from logs.logger import setup_logging
from query_handler import process_queries, read_database_queries

if __name__ == "__main__":
    setup_logging()

    databases = read_database_instances()
    process_databases(databases)

    queries = read_database_queries()
    process_queries(queries)
