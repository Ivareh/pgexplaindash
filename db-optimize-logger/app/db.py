import os
from pathlib import Path
from typing import Any

import pandas as pd
from logs.logger import explain_logger
from pydantic import BaseModel, PostgresDsn
from sqlalchemy import Engine, TextClause, create_engine

DATABASES_SAVES_CSV = Path("app/saves/databases.csv")


class DatabaseInstance(BaseModel):
    id: str
    name: str
    url: str

    @property
    def engine(self) -> Engine:
        return create_engine(self.url)


def create_db_url(
    username: str | None,
    password: str | None,
    host: str | None,
    port: int | None,
    db: str | None,
) -> PostgresDsn:
    url = PostgresDsn.build(
        scheme="postgresql+psycopg2",
        username=username,
        password=password,
        host=host,
        port=port,
        path=db,
    )

    return url


def find_db_instance(id: str) -> DatabaseInstance:
    """Checks and returns if db instance with id specified exists in saves file.

    Raises exception if the instance wasn't found.
    """
    try:
        saves_df = pd.read_csv(DATABASES_SAVES_CSV)
    except FileNotFoundError:
        raise ValueError("Couldn't find db instance id specified in saves file")

    id_existing_index = saves_df.index[saves_df["id"] == id].to_list()
    if not id_existing_index:
        raise ValueError("Couldn't find db instance id specified in saves file")

    id_existing_index = saves_df.iloc[id_existing_index]

    return DatabaseInstance(
        id=id_existing_index["id"].values[0],
        name=id_existing_index["name"].values[0],
        url=id_existing_index["url"].values[0],
    )


def delete_db_instance(id: str) -> None:
    find_db_instance(id)  # Check if database exist and handle it

    saves_df = pd.read_csv(DATABASES_SAVES_CSV)

    id_existing_index = saves_df.index[saves_df["id"] == id].to_list()
    saves_df = saves_df.drop(id_existing_index)

    saves_df.to_csv(DATABASES_SAVES_CSV, index=False)


def delete_all_databases() -> None:
    try:
        os.remove(DATABASES_SAVES_CSV)
    except FileNotFoundError:
        print("All databases already deleted")


def save_db_instance(db_instance: DatabaseInstance) -> None:
    """
    Saves `db_instance` to a row in database saves csv file.

    If `db_instance` has an existing `db_instance.id` in the saves, it replaces the row with
    the existing `db_instance.id`"""
    try:
        saves_df = pd.read_csv(DATABASES_SAVES_CSV)
    except FileNotFoundError:
        cols = pd.Index(["id", "name", "url"])
        saves_df = pd.DataFrame(columns=cols)
        saves_df.to_csv(DATABASES_SAVES_CSV, index=False)

    db_instance_df = pd.DataFrame([db_instance.model_dump()])
    db_instance_df = db_instance_df.reindex(columns=saves_df.columns, fill_value=None)

    id_existing_index = saves_df.index[saves_df["id"] == db_instance.id].to_list()
    if id_existing_index:
        saves_df = saves_df.drop(id_existing_index)

    saves_df = pd.concat([saves_df, db_instance_df], ignore_index=True)

    saves_df.to_csv(DATABASES_SAVES_CSV, index=False)


# @sync_timing_tracker
def execute_explain_stmt(
    db_instance: DatabaseInstance,
    statement: TextClause,
    query_name: str,
) -> dict[Any, Any]:
    # Returns JSON string representation of explain query
    explain_logger.info(
        f"Performing query in db.id={db_instance.id} with query_name={query_name}"
    )
    with db_instance.engine.begin() as conn:
        explain = conn.execute(statement)

    assert explain

    explain_dump: dict[Any, Any] = explain.scalar_one()[0]

    assert isinstance(explain_dump, dict)
    return explain_dump
