import warnings
from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd
from nicegui import ui

from app.db import (
    NoDatabasesFoundError,
    find_database_instance,
    read_database_ids_list,
    read_database_saves_df,
)
from app.interface import WarningEnum
from app.query_handler import (
    DatabaseQuery,
    DatabaseQueryList,
    NoQueriesFoundError,
    delete_all_queries,
    delete_database_query,
    parse_database_ids,
    read_queries_saves_df,
    save_database_query,
)
from app.ui.components.common import (
    create_field_with_tooltip,
    notify_popup,
    ui_int_input,
)


@ui.refreshable
def _saved_queries_ui(queries: DatabaseQueryList, databases: list[str]):
    if not queries.items:
        ui.label("Queries are empty.").classes("mx-auto")
        return
    for query in queries.items:
        with ui.column().classes("w-full items-stretch border rounded p-4 mb-4 gap-4"):
            with ui.row().classes("w-full items-center gap-2"):
                ui.input("Query name", value=query.name).classes(
                    "flex-grow w-full"
                ).bind_value(query, "name")
                with ui.row().classes("w-full"):
                    display_dbs = databases.copy()
                    for database_id in query.database_ids:
                        if database_id not in databases:
                            ui.label(
                                f"Database id {database_id[:6]}... was not found"
                            ).classes("my-auto text-red")
                            display_dbs.append(database_id)
                    ui.select(
                        display_dbs,
                        label="Database ids",
                        multiple=True,
                        value=query.database_ids,
                    ).classes("flex-grow").bind_value(query, "database_ids")._props(
                        "use-chips"
                    )
                with ui.row().classes("mx-auto items-stretch"):
                    ui_int_input(
                        label="Repeat",
                        value=query.repeat,
                        attr_name="repeat",
                        bind_object=query,
                        width_px=160,
                    )
                    ui.switch("Query count", value=query.query_count).classes(
                        "flex-grow w-[160px]"
                    ).bind_value(query, "query_count")

            ui.textarea("Sql statement", value=query.sql).classes("w-full")._props(
                "autogrow rows=3"
            ).style("height: full").bind_value(query, "sql")

            ui.button(
                on_click=lambda _, query=query: _delete_query_handler(queries, query),
                icon="delete",
            ).classes("mt-auto")


def _add_query_handler(
    queries: DatabaseQueryList,
    *,
    add_name: Any,
    add_database_ids: Any,
    add_sql: Any,
    add_repeat: Any,
    add_query_count: Any,
):
    "Takes add inputs from query UI, saves and adds the values of them to a db query object"

    query_id = str(uuid4())

    try:
        db_query = DatabaseQuery(
            id=query_id,
            name=add_name.value,
            database_ids=add_database_ids.value,
            sql=add_sql.value,
            repeat=add_repeat.value,
            query_count=add_query_count.value,
        )

        # Save in csv and add to UI
        save_database_query(db_query)
        queries.add(db_query)

        notify_popup(f"Added and saved query `{add_name.value}`", type="positive")

        # Clears the fields after adding
        add_name.value = ""
        add_database_ids.value = []
        add_sql.value = ""
        add_repeat.value = 0
        add_query_count.value = False

    except Exception as e:
        notify_popup(str(e), type="negative")


def _delete_query_handler(queries: DatabaseQueryList, query: DatabaseQuery) -> None:
    try:
        delete_database_query(query.id)
        queries.remove(query)
        notify_popup(f"Successfully deleted query `{query.name}`", "positive")
    except Exception as e:
        notify_popup(str(e), "negative")
        return


def _save_all_queries_handler(queries: DatabaseQueryList):
    try:
        for query in queries.items:
            # Validate fields
            DatabaseQuery(**query.model_dump())

            for db_id in query.database_ids:
                try:
                    find_database_instance(db_id)
                except Exception as e:
                    notify_popup(str(e), type="negative")
                    return

        delete_all_queries()

        for query in queries.items:
            save_database_query(query)
        _saved_queries_ui.refresh()
        notify_popup("Successfully saved all queries", type="positive")
    except Exception as e:
        notify_popup(str(e), type="negative")
        return


def _ui_load_queries(queries: DatabaseQueryList):
    try:
        saves_df = read_queries_saves_df()

        saves_df = saves_df.replace({np.nan: None, pd.NA: None, pd.NaT: None})

    except NoQueriesFoundError:
        return

    if saves_df.empty:
        return

    def process_query(query_row):
        db_query_dict = {
            "id": query_row["id"],
            "name": query_row["name"],
            "database_ids": (
                parse_database_ids(query_row["database_ids"])
            ),  # Parses list format
            "sql": query_row["sql"],
            "repeat": query_row["repeat"],
            "query_count": bool(query_row["query_count"]),
        }
        db_query = DatabaseQuery(**db_query_dict)
        queries.add(db_query)

        try:
            for db_id in db_query_dict["database_ids"]:
                find_database_instance(db_id)
        except NoDatabasesFoundError:
            warnings.warn(
                f"{WarningEnum.WARNING}Didn't find database id for query {db_query_dict['id'][:6]}_{db_query_dict['name'][:50]}{WarningEnum.RESET}",
                stacklevel=2,
            )

    try:
        saves_df = saves_df.apply(process_query, axis=1)
    except Exception as e:
        ui.label(str(e)).classes("text-red")


def _add_queries_component(queries: DatabaseQueryList, databases: list[str]) -> None:
    "Loads component to add more queries with input"

    with ui.card().classes(
        "mt-10 w-full items-stretch overflow-hidden border border-gray"
    ):
        with ui.element("div").classes(
            "fixed top-0 right-12 z-[9999] p-4 flex items-center"
        ):
            ui.button(
                "Save All Queries",
                on_click=lambda _: _save_all_queries_handler(queries),
            )

        ui.label().bind_text_from(queries, "title").classes("text-semibold text-2xl")
        add_query_name = create_field_with_tooltip(
            "Query name to help identify the query (can be anything)",
            lambda: ui.input("Query name")._props('autocomplete="off"'),
        )

        add_database_ids = create_field_with_tooltip(
            "Database ids from databases previously saved. The query will execute for each of the databases specified",
            lambda: ui.select(databases, label="Database ids", multiple=True)._props(
                "use-chips"
            ),
        )

        with ui.row().classes("mx-auto items-stretch mt-8"):
            add_repeat = create_field_with_tooltip(
                "Times to repeat the query (for each database specified). Compare multiple executes",
                lambda: ui.number("Repeat").classes("w-[160Bpx]"),
            )
            add_query_count = create_field_with_tooltip(
                "(NB! Only for `SELECT` queries): Whether to perform an additional COUNT(*) query to check how many rows the execute returns",
                lambda: ui.switch("Query count").classes("mt-4 w-[160px]"),
            )
        add_sql = create_field_with_tooltip(
            "SQL statement with `EXPLAIN (ANALYZE, FORMAT JSON)` ",
            lambda: ui.textarea("Sql statement")
            ._props("autogrow rows=3")
            .style("height: full"),
        )

        ui.button(
            "Add query",
            on_click=lambda _: _add_query_handler(
                queries,
                add_name=add_query_name,
                add_database_ids=add_database_ids,
                add_sql=add_sql,
                add_repeat=add_repeat,
                add_query_count=add_query_count,
            ),
        ).classes("mt-auto")


def _saved_queries_component(
    queries: DatabaseQueryList, database_ids: list[str]
) -> None:
    "Loads component with a grid for all saved queries"

    ui.label("Saved queries").classes("text-semibold text-2xl mt-10")
    with ui.grid(columns=2).classes("w-full mx-auto"):
        _saved_queries_ui(queries, database_ids)
        _ui_load_queries(queries)
    ui.space().classes("h-20")


def _databases_help_table() -> None:
    "Helper table to see which database to choose while creating queries"
    try:
        db_saves_df = read_database_saves_df()
    except NoDatabasesFoundError:
        ui.label("Warning: Please add databases before adding queries").classes(
            "text-yellow text-xl"
        )
        return

    db_saves_df.replace(pd.NaT, "")

    columns = [
        {
            "name": col,
            "label": col,
            "field": col,
            "align": "left",
            "classes": "whitespace-normal break-words",
        }
        for col in db_saves_df.columns
    ]

    rows = db_saves_df.to_dict(orient="records")

    table = ui.table(
        title="Saved databases",
        columns=columns,
        rows=rows,
    ).classes("border border-gray w-full rounded")

    # 5) If you still want a custom “top-left” slot:
    with table.add_slot("top-left"):
        ui.label("Saved databases").classes("text-lg")


def queries_component() -> None:
    queries = DatabaseQueryList("Add queries", on_change=_saved_queries_ui.refresh)
    _databases_help_table()
    database_ids = read_database_ids_list()
    _add_queries_component(queries, database_ids)
    _saved_queries_component(queries, database_ids)
