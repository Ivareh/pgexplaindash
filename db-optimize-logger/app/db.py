import json
from pathlib import Path

from logs.logger import exp_analyze_logger
from sqlalchemy import Result, TextClause, create_engine
from utils import sync_timing_tracker

engine = create_engine(
    "postgresql+psycopg2://pom_oltp_superuser:changethis@db:5432/pom_oltp_db"
)


@sync_timing_tracker
def execute_sql_stmt(statement: TextClause, query_id: str, **stmt_info):  # noqa: ARG001
    with engine.begin() as conn:
        response = conn.execute(statement)

    save_response(response, f"{query_id}_response.json")
    exp_analyze_logger.info(f"""query_id={query_id}'""")

    print("\n\n\n")
    print(statement)
    print("\n\n\n")
    print(response)
    print("\n\n\n")


def save_response(response: Result, filename: str) -> str:
    # Path to mounted directory
    output_dir = Path("/app/responses_output")

    # Create directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create full file path
    file_path = output_dir / filename

    # Write content
    with open(file_path, "w") as f:
        json.dump(response.scalars().one()[0], f, indent=4)

    return str(file_path)
