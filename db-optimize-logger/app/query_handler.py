import os
from pathlib import Path
from typing import Any

import pandas as pd
from db import (
    DatabaseInstance,
    execute_explain_stmt,
    find_db_instance,
)
from logs.logger import explain_logger, graph_node_logger
from node_graph_plan import (
    create_graphedge_table,
    create_graphnode_table,
    create_level_divider,
)
from node_process import extract_node_series, process_explain_df
from pydantic import BaseModel
from sqlalchemy import TextClause, text

QUERIES_SAVES_CSV = Path("app/saves/queries.csv")


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
    def process_sql(row):
        db_instance_id = row["db_instance_id"]
        db_instance = find_db_instance(db_instance_id)
        query_id = row["name"]
        sql = text(row["sql"])
        explain_dump = execute_explain_stmt(
            db_instance=db_instance, statement=sql, query_id=query_id
        )

        explain_dir = Path("/app/file/explain_output")

        explain_df = pd.DataFrame([explain_dump])

        explain_df.to_json(
            explain_dir / f"{query_id}.json", orient="records", lines=True
        )

        explain_df = process_explain_df(explain_df)

        node_series = extract_node_series(explain_df)

        graphnode_df = create_graphnode_table(node_series)
        graphedge_df = create_graphedge_table(node_series)

        graphnode_dict = graphnode_df.to_dict(orient="records")
        graphedge_dict = graphedge_df.to_dict(orient="records")

        for node in graphnode_dict:
            graph_node_logger.info(f"query_id={query_id}&node={node}")
        for edge in graphedge_dict:
            graph_node_logger.info(f"query_id={query_id}&edge={edge}")

        level_divider_df = create_level_divider(node_series)
        level_divider_dict = level_divider_df.to_dict(orient="records")

        for index, level in enumerate(level_divider_dict):
            index_character = chr(
                ord("@") + index + 1
            )  # converts index to corresponding letter in alphabet series
            log_with_query(
                query_id=query_id,
                log_dict={
                    "index": index_character + str(index),
                    "level_divide": level["nodes"],
                },
            )

    queries.apply(process_sql, axis=1)
