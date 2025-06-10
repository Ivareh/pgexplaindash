from db import load_database_instances, process_databases
from logs.logger import setup_logging
from query_handler import load_database_queries, process_queries

if __name__ == "__main__":
    setup_logging()

    databases = load_database_instances()
    process_databases(databases)

    queries = load_database_queries()
    process_queries(queries)
