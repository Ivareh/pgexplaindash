import os
from pathlib import Path

import pandas as pd
from db import (
    DatabaseInstance,
    execute_explain_stmt,
    find_db_instance,
)
from interface import PlanEnum
from logs.logger import explain_logger, graph_node_logger
from node_graph_plan import (
    create_graphedge_table,
    create_graphnode_table,
    create_level_divider,
    create_node_metrics_df,
)
from node_process import extract_node_series, process_explain_df
from pydantic import BaseModel
from sqlalchemy import TextClause, text
from utils import log_key_value

QUERIES_SAVES_CSV = Path("app/saves/queries.csv")


class DatabaseQuery(BaseModel):
    id: str  # UUID identifier
    db_instance: DatabaseInstance
    name: str  # Recognizable id for user to keep track of queries
    sql: str

    @property
    def statement(self) -> TextClause:
        return text(self.sql)


def find_database_query(id: str) -> DatabaseQuery:
    """Checks and returns if db query with id specified exists in saves file.

    Raises exception if the query wasn't found.
    """
    try:
        saves_df = pd.read_csv(QUERIES_SAVES_CSV)
    except FileNotFoundError:
        raise ValueError("Couldn't find db query id specified in saves file")

    id_existing_index = saves_df.index[saves_df["id"] == id].to_list()
    if not id_existing_index:
        raise ValueError("Couldn't find db query id specified in saves file")

    id_existing_index = saves_df.iloc[id_existing_index]
    db_instance_id = id_existing_index["db_instance_id"].values[0]

    try:
        db_instance = find_db_instance(db_instance_id)
    except ValueError:
        raise ValueError(
            "Could not retrieve db query, since the db instance id wasn't found"
        )

    return DatabaseQuery(
        id=id_existing_index["id"].values[0],
        name=id_existing_index["name"].values[0],
        db_instance=db_instance,
        sql=id_existing_index["sql"].values[0],
    )


def delete_database_query(id: str) -> None:
    find_database_query(id)  # Check if query exist and handle it

    saves_df = pd.read_csv(QUERIES_SAVES_CSV)

    id_existing_index = saves_df.index[saves_df["id"] == id].to_list()
    saves_df = saves_df.drop(id_existing_index)

    saves_df.to_csv(QUERIES_SAVES_CSV, index=False)


def delete_all_queries() -> None:
    try:
        os.remove(QUERIES_SAVES_CSV)
    except FileNotFoundError:
        print("All queries are already deleted")


def save_database_query(query: DatabaseQuery) -> None:
    """
    Saves `query` to a row in database saves csv file.

    If `db_instance` has an existing `db_instance.id` in the saves, it replaces the row with
    the existing `db_instance.id`"""
    try:
        saves_df = pd.read_csv(QUERIES_SAVES_CSV)
    except FileNotFoundError:
        cols = pd.Index(["id", "db_instance_id", "name", "sql"])
        saves_df = pd.DataFrame(columns=cols)
        saves_df.to_csv(QUERIES_SAVES_CSV, index=False)
    query_dump = query.model_dump()
    db_instance = query_dump.pop("db_instance")
    query_dump["db_instance_id"] = db_instance["id"]

    query_df = pd.DataFrame([query_dump])
    query_df = query_df.reindex(columns=saves_df.columns, fill_value=None)

    id_existing_index = saves_df.index[saves_df["id"] == query.id].to_list()
    if id_existing_index:
        saves_df = saves_df.drop(id_existing_index)

    saves_df = pd.concat([saves_df, query_df], ignore_index=True)

    saves_df.to_csv(QUERIES_SAVES_CSV, index=False)


class NoQueriesFoundError(Exception):
    def __init__(self, *args):
        detail = "Found no saved queries, please add some queries before starting the program"
        super().__init__(detail, args)


def load_database_queries() -> pd.DataFrame:
    try:
        saves_df = pd.read_csv(QUERIES_SAVES_CSV)
    except FileNotFoundError:
        raise NoQueriesFoundError

    if saves_df.empty:
        raise NoQueriesFoundError

    return saves_df


def process_queries(queries: pd.DataFrame) -> None:
    for _, row in queries.iterrows():
        db_instance_id = str(row["db_instance_id"])
        db_instance = find_db_instance(db_instance_id)

        id_short = row["id"][:6]
        db_name = db_instance.name
        query_name = f"{row['name']}__{db_name}__{id_short}"
        sql = text(str(row["sql"]))

        explain_dump = execute_explain_stmt(
            db_instance=db_instance, statement=sql, query_name=query_name
        )

        explain_dir = Path("/app/file/explain_output")

        explain_df = pd.DataFrame([explain_dump])

        explain_df.to_json(
            explain_dir / f"{query_name}.json", orient="records", lines=True
        )

        explain_df = process_explain_df(explain_df)
        log_key_value(
            explain_logger,
            {
                "db_name": db_name,
                "query_name": query_name,
                "sql": str(row["sql"]),
                "total_exc_time": explain_dump[PlanEnum.EXECUTION_TIME],
            },
        )

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
            padded_index = index_str.ljust(max_index_width)  # Pad to fixed width
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
