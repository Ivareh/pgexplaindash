import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

import pandas as pd
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import TextClause, text

from app.core.interface import PlanEnum
from app.core.utils import log_key_value
from app.execute.database import (
    DatabaseInstance,
    execute_count_stmt,
    execute_explain_stmt,
    find_database_instance,
)
from app.execute.node_graph_plan import (
    create_graphedge_table,
    create_graphnode_table,
    create_level_divider,
    create_node_metrics_df,
)
from app.execute.node_process import extract_node_series, process_explain_df
from app.logs.logger import app_logger, explain_logger, graph_node_logger

QUERIES_SAVES_CSV = Path("app/saves/queries.csv")


class Query(BaseModel):
    id: str = Field(min_length=1)  # UUID identifier
    name: str = Field(min_length=1)  # Recognizable id for user to keep track of queries
    database_ids: list[str] = Field(min_length=1)
    sql: str = Field(min_length=1)
    repeat: int | None
    query_count: bool

    @property
    def statement(self) -> TextClause:
        return text(self.sql)

    @field_validator("repeat")
    @classmethod
    def convert_none(cls, v: int) -> int | None:
        if v == 0:
            return None
        return v


@dataclass
class QueryList:
    title: str
    on_change: Callable
    items: list[Query] = field(default_factory=list)

    def add(self, db_query: Query) -> None:
        # Found this PR: https://github.com/zauberzeug/nicegui/pull/1951 but not sure if it got merged properly
        if db_query.repeat is not None:
            db_query.repeat = int(db_query.repeat)
        self.items.append(db_query)
        self.on_change()

    def remove(self, query: Query) -> None:
        self.items.remove(query)
        self.on_change()


class NoQueriesFoundError(Exception):
    def __init__(self, *args):
        detail = "Found no saved queries"
        super().__init__(detail, args)


def read_queries_saves_df() -> pd.DataFrame:
    try:
        saves_df = pd.read_csv(
            QUERIES_SAVES_CSV,
            dtype={
                "id": "string",
                "database_ids": "string",
                "name": "string",
                "sql": "string",
                "repeat": "Int64",
                "query_count": "boolean",
            },
        )
        saves_df["repeat"] = saves_df["repeat"].fillna(0).astype("int64")
    except FileNotFoundError:
        raise NoQueriesFoundError

    if saves_df.empty:
        raise NoQueriesFoundError

    return saves_df


def parse_database_ids(database_ids: str) -> list[str]:
    "Parses `query.database_ids` field to a list"
    if database_ids == "[]":
        return []
    return database_ids[1:-1].replace("'", "").split(", ")


def find_query(id: str) -> Query:
    """Checks and returns if query with id specified exists in saves file.

    Raises exception if the query wasn't found.
    """
    saves_df = read_queries_saves_df()

    id_existing_index = saves_df.index[saves_df["id"] == id].to_list()
    if not id_existing_index:
        raise NoQueriesFoundError("Couldn't find db query id specified in saves file")

    id_existing_index = saves_df.iloc[id_existing_index]
    database_ids = parse_database_ids(id_existing_index["database_ids"].values[0])

    return Query(
        id=id_existing_index["id"].values[0],
        name=id_existing_index["name"].values[0],
        database_ids=database_ids,
        sql=id_existing_index["sql"].values[0],
        repeat=id_existing_index["repeat"].values[0],
        query_count=id_existing_index["query_count"].values[0],
    )


def delete_query(id: str) -> None:
    find_query(id)  # Check if query exist and handle it

    saves_df = read_queries_saves_df()

    id_existing_index = saves_df.index[saves_df["id"] == id].to_list()
    saves_df = saves_df.drop(id_existing_index)

    saves_df.to_csv(QUERIES_SAVES_CSV, index=False)


def delete_all_queries() -> None:
    try:
        os.remove(QUERIES_SAVES_CSV)
    except FileNotFoundError:
        app_logger.info("All queries are already deleted")


def save_query(query: Query) -> None:
    "Saves `query` to a row in query saves csv file."
    try:
        saves_df = read_queries_saves_df()
    except NoQueriesFoundError:
        cols = pd.Index(["id", "database_ids", "name", "sql", "repeat", "query_count"])
        saves_df = pd.DataFrame(columns=cols)
        saves_df.to_csv(QUERIES_SAVES_CSV, index=False)
    query_dump = query.model_dump()

    query_df = pd.DataFrame([query_dump])
    query_df = query_df.reindex(columns=saves_df.columns, fill_value=None)

    id_existing_index = saves_df.index[saves_df["id"] == query.id].to_list()
    if id_existing_index:
        saves_df = saves_df.drop(id_existing_index)

    saves_df = pd.concat([saves_df, query_df], ignore_index=True)

    saves_df.to_csv(QUERIES_SAVES_CSV, index=False)


def query_run_times(query_row: pd.Series) -> int:
    "Finds how many times to run a query based on `repeat` property"
    repeat = query_row.loc["repeat"]
    if pd.isna(repeat):
        repeat = 0
    else:
        repeat = int(repeat)
    run_times = repeat + 1 if repeat > 0 else 1
    return run_times


def define_query_name(query_row: pd.Series, db_name: str) -> str:
    "Defines an unique name for query with db_instance partial uuid4"
    run_id = str(uuid4())[:6]
    query_name = f"{query_row['name']}__{db_name}__{run_id}"
    return query_name


def get_count(*, sql_str: str, query_name: str, db_instance: DatabaseInstance) -> int:
    pattern = r"^\s*EXPLAIN\s*\(\s*ANALYZE\s*,\s*FORMAT\s*JSON\s*\)\s*"
    original_sql = re.sub(pattern, "", sql_str, flags=re.IGNORECASE).strip()
    if original_sql.endswith(";"):
        original_sql = original_sql[:-1].strip()
    if not original_sql.startswith("SELECT"):
        raise ValueError(f"Can't perform COUNT(*) on non-`SELECT` query: {query_name}")
    count_sql = text(f"SELECT COUNT(*) FROM ({original_sql}) AS count_subquery")
    count_dump = execute_count_stmt(
        database_instance=db_instance,
        statement=count_sql,
        query_name=query_name,
    )
    return count_dump["count"]


def process_queries(queries: pd.DataFrame) -> None:
    "This function is crap and needs to be refactored and more tidy"

    for index, (_, query_row) in enumerate(queries.iterrows(), start=1):
        database_ids = parse_database_ids(query_row.database_ids)
        db_instances: list[DatabaseInstance] = []
        for db_id in database_ids:
            db_instances.append(find_database_instance(db_id))

        run_times = query_run_times(query_row)
        for db_instance in db_instances:
            for _ in range(run_times):
                explain_log_obj = {}

                sql_str = str(query_row["sql"])

                db_name = db_instance.name
                query_name = define_query_name(query_row, db_name)

                if query_row.query_count:
                    explain_log_obj["count"] = get_count(
                        sql_str=sql_str, query_name=query_name, db_instance=db_instance
                    )

                sql = text(sql_str)
                explain_dump = execute_explain_stmt(
                    database_instance=db_instance, statement=sql, query_name=query_name
                )

                explain_log_obj = {
                    "db_name": db_name,
                    "query_name": query_name,
                    "sql": str(query_row["sql"]),
                    "total_exc_time": explain_dump[PlanEnum.EXECUTION_TIME],
                    **explain_log_obj,
                }
                log_key_value(
                    explain_logger,
                    explain_log_obj,
                )

                explain_dir = Path("/app/file/explain_output")

                explain_df = pd.DataFrame([explain_dump])

                explain_df.to_json(
                    explain_dir / f"{query_name}.json", orient="records", lines=True
                )

                explain_df = process_explain_df(explain_df)

                node_series = extract_node_series(explain_df)

                node_metrics_df = create_node_metrics_df(node_series)

                graphnode_df = create_graphnode_table(node_series)
                graphedge_df = create_graphedge_table(node_series)

                node_metrics_dict = node_metrics_df.to_dict(orient="records")
                graphnode_dict = graphnode_df.to_dict(orient="records")
                graphedge_dict = graphedge_df.to_dict(orient="records")

                for node in node_metrics_dict:
                    graph_node_logger.info(
                        f"db_name={db_name}&query_name={query_name}&node={node}"
                    )
                for node in graphnode_dict:
                    graph_node_logger.info(
                        f"db_name={db_name}&query_name={query_name}&node={node}"
                    )
                for edge in graphedge_dict:
                    graph_node_logger.info(
                        f"db_name={db_name}&query_name={query_name}&edge={edge}"
                    )

                level_divider_df = create_level_divider(node_series)
                level_divider_dict = level_divider_df.to_dict(orient="records")
                n = len(level_divider_dict)

                max_index_width = 1 + len(str(n - 1)) if n > 0 else 0

                for index, level in enumerate(level_divider_dict):
                    prefix_index = "0" if len(str(index)) < 2 else ""
                    index_str = prefix_index + str(index)
                    padded_index = index_str.ljust(
                        max_index_width
                    )  # Pad to fixed width
                    padded_index = padded_index.replace(" ", "\u00a0")
                    full_log_line = (
                        f"{padded_index} {level['nodes']}"  # Combine with log content
                    )

                    log_key_value(
                        explain_logger,
                        log_dict={
                            "db_name": db_name,
                            "query_name": query_name,
                            "level_divide": full_log_line,  # Use aligned log line
                        },
                    )
