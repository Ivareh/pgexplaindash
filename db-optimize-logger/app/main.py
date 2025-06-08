from logs.logger import setup_logging

from app.query_handler import load_database_queries, process_queries

if __name__ == "__main__":
    setup_logging()

    queries = load_database_queries()
    process_queries(queries)
