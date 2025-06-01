from typing import Any

from logs.logger import explain_logger
from sqlalchemy import TextClause, create_engine

engine = create_engine(
    "postgresql+psycopg2://pom_oltp_superuser:changethis@db:5432/pom_oltp_db"
)


# @sync_timing_tracker
def execute_explain_stmt(
    statement: TextClause,
    query_id: str,
) -> dict[Any, Any]:
    # Returns JSON string representation of explain query
    explain_logger.info(f"Performing query with query_id={query_id}")
    with engine.begin() as conn:
        explain = conn.execute(statement)

    assert explain

    explain_dump: dict[Any, Any] = explain.scalar_one()[0]

    assert isinstance(explain_dump, dict)
    return explain_dump
