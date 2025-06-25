import asyncio

from app.core.progress import Progress
from app.execute.database import process_databases, read_database_saves_df
from app.execute.query_handler import process_queries, read_queries_saves_df
from app.logs.logger import setup_logging


async def start_log(progress: Progress):
    setup_logging()

    databases = read_database_saves_df()
    process_databases(databases)
    await asyncio.sleep(4)

    queries = read_queries_saves_df()
    process_queries(queries)
    progress.set_loading(False)
