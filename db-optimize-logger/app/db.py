from logs.logger import exp_analyze_logger
from sqlalchemy import create_engine
from utils import sync_timing_tracker

engine = create_engine(
    "postgresql+psycopg2://pom_oltp_superuser:changethis@db:5432/pom_oltp_db"
)


@sync_timing_tracker
def execute_sql_stmt(stmt, **stmt_info):  # noqa: ARG001
    with engine.begin() as conn:
        resp = conn.execute(stmt).scalars().all()
        exp_analyze_logger.info(resp)
