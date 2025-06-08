from typing import Any

from logs.logger import explain_logger, setup_logging

from app.query_handler import load_database_queries, process_queries


def log_with_query(query_id: str, log_dict: dict[str, Any]) -> None:
    """
    Logs query_id with keys and values for log_dict.
    Vector.dev config uses regex matches to produce an object with key and values
    for query_id and items in log_dict.


    NB!: The keys and values in query_id and log_dict can't have '&' in them in conflict
    of the regex matches. This is a temporary fault.

    Example:

        Input: log_with_query("qid1", {"key1": "value1", "key2": "value2"})
        Output: query_id=qid1&key1=value1&key2=value2


    """
    log_stmt = f"query_id={query_id}"
    log_stmt = log_stmt + "".join(
        [f"&{key}={value}" for key, value in log_dict.items()]
    )
    explain_logger.info(log_stmt)


if __name__ == "__main__":
    setup_logging()
    queries = load_database_queries()
    process_queries(queries)
