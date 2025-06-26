import os
from collections.abc import Callable
from dataclasses import field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, PostgresDsn, field_validator
from pydantic_core import MultiHostHost
from sqlalchemy import Engine, TextClause, create_engine, engine

from app.core.utils import log_key_value
from app.logs.logger import app_logger, db_logger, explain_logger

DATABASES_SAVES_CSV = Path("app/saves/databases.csv")


class DatabaseInstance(BaseModel):
    id: str = Field(min_length=1)  # UUID identifier
    name: str = Field(min_length=1)
    description: str | None = None
    url: str = Field(min_length=1)

    @property
    def engine(self) -> Engine:
        return create_engine(self.url)


class ExplodedURLDBInstance(BaseModel):
    "Database instance with exploded url"

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str | None = None
    username: str | None = None
    password: str | None = None
    host: str = Field(min_length=1)
    port: int | None = None
    db: str = Field(min_length=1)

    @field_validator("port")
    @classmethod
    def convert_none(cls, v: int) -> int | None:
        if v == 0:
            return None
        return v


class ExplodedURLDBInstanceList(BaseModel):
    title: str
    on_change: Callable
    items: list[ExplodedURLDBInstance] = field(default_factory=list)

    def add(self, database_instance: ExplodedURLDBInstance) -> None:
        # Found this PR: https://github.com/zauberzeug/nicegui/pull/1951 but not sure if it got merged properly
        self.items.append(database_instance)
        self.on_change()

    def remove(self, database_instance: ExplodedURLDBInstance) -> None:
        self.items.remove(database_instance)
        self.on_change()


def create_database_url(
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


class NoDatabasesFoundError(Exception):
    def __init__(self, *args):
        detail = "Database not found in saves"
        super().__init__(detail, args)


def read_database_saves_df() -> pd.DataFrame:
    try:
        saves_df = pd.read_csv(DATABASES_SAVES_CSV)
    except FileNotFoundError:
        raise NoDatabasesFoundError

    if saves_df.empty:
        raise NoDatabasesFoundError

    return saves_df


def find_database_instance(id: str) -> DatabaseInstance:
    "Uses database instance `id` to find corresponding in saves and return the instance"

    df = read_database_saves_df().replace({np.nan: None, pd.NA: None, pd.NaT: None})
    mask = df["id"] == id
    if not mask.any():
        raise NoDatabasesFoundError(f"ID {id!r} isn’t in {DATABASES_SAVES_CSV!r}")

    row = df.loc[mask].squeeze("rows")

    return DatabaseInstance(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        url=row["url"],
    )


def delete_database_instance(id: str) -> None:
    find_database_instance(id)  # Check if database exist and handle it

    saves_df = read_database_saves_df()

    id_existing_index = saves_df.index[saves_df["id"] == id].to_list()
    saves_df = saves_df.drop(id_existing_index)

    saves_df.to_csv(DATABASES_SAVES_CSV, index=False)


def delete_all_databases() -> None:
    try:
        os.remove(DATABASES_SAVES_CSV)
    except FileNotFoundError:
        app_logger.info("All databases already deleted")


def save_database_instance(database_instance: DatabaseInstance) -> None:
    """
    Saves `database_instance` to a row in database saves csv file.

    If `database_instance` has an existing `database_instance.id` in the saves, it replaces the row with
    the existing `database_instance.id`"""
    try:
        saves_df = read_database_saves_df()
    except NoDatabasesFoundError:
        cols = pd.Index(["id", "name", "description", "url"])
        saves_df = pd.DataFrame(columns=cols)
        saves_df.to_csv(DATABASES_SAVES_CSV, index=False)

    db_instance_df = pd.DataFrame([database_instance.model_dump()])
    db_instance_df = db_instance_df.reindex(columns=saves_df.columns, fill_value=None)

    id_existing_index = saves_df.index[saves_df["id"] == database_instance.id].to_list()
    if id_existing_index:
        saves_df = saves_df.drop(id_existing_index)

    saves_df = pd.concat([saves_df, db_instance_df], ignore_index=True)

    saves_df.to_csv(DATABASES_SAVES_CSV, index=False)


def read_database_ids_list() -> list[str]:
    try:
        database_instances = read_database_saves_df()
    except NoDatabasesFoundError:
        return []

    return list(database_instances["id"])


def hide_password_url(database_url: str) -> str:
    url = engine.make_url(database_url)
    return url.render_as_string(hide_password=True)


def mapped_database_url(database_url: str) -> tuple[MultiHostHost, str | None]:
    """
    Returns a mapped database url.

    Usage:
    mapped_db_url, db_name = mapped_database_url(db_url)
    username = mapped_database_url["username"]
    password = mapped_database_url["password"]
    ... other db url fields

    """
    db_url = PostgresDsn(database_url)
    path = db_url.path[1:] if db_url.path else None  # database name
    url_dict = db_url.hosts()[0]
    return url_dict, path


def process_databases(databases: pd.DataFrame) -> None:
    for _, row in databases.iterrows():
        db_name = row["name"]
        db_description = row["description"]
        db_url = row["url"]

        hided_url = hide_password_url(str(db_url))

        log_key_value(
            db_logger,
            {"db_name": db_name, "db_description": db_description, "db_url": hided_url},
        )


def execute_explain_stmt(
    database_instance: DatabaseInstance,
    statement: TextClause,
    query_name: str,
) -> dict[Any, Any]:
    # Returns JSON string representation of explain query
    explain_logger.info(
        f"Performing query in db.id={database_instance.id} with query_name={query_name}"
    )
    with database_instance.engine.begin() as conn:
        explain = conn.execute(statement)

    assert explain

    explain_dump: dict[Any, Any] = explain.scalar_one()[0]
    explain_dump["database"] = database_instance.name + "_" + database_instance.id[:6]

    assert isinstance(explain_dump, dict)
    return explain_dump
