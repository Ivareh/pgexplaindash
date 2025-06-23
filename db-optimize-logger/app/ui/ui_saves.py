from nicegui import ui

from app.db import read_database_ids
from app.query_handler import DatabaseQueryList
from app.ui.components.common import ui_int_input
from app.ui.components.query import delete_query_handler


@ui.refreshable
def saved_queries_ui(databases: list[str]):
    if not queries.items:
        ui.label("Queries are empty.").classes("mx-auto")
        return
    for query in queries.items:
        with ui.column().classes("w-full items-stretch border rounded p-4 mb-4 gap-4"):
            with ui.row().classes("w-full items-center gap-2"):
                ui.input("Query name", value=query.name).classes(
                    "flex-grow w-full"
                ).bind_value(query, "name")
                ui.select(
                    databases,
                    label="Database ids",
                    multiple=True,
                    value=query.database_ids,
                ).classes("flex-grow w-full").bind_value(query, "database_ids")._props(
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
                on_click=lambda _, query=query: delete_query_handler(query),
                icon="delete",
            ).classes("mt-auto")


queries = DatabaseQueryList("Add queries", on_change=saved_queries_ui.refresh)
databases = read_database_ids()
