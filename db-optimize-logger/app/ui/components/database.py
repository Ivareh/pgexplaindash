from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd
from nicegui import ui

from app.execute.database import (
    DatabaseInstance,
    ExplodedURLDBInstance,
    ExplodedURLDBInstanceList,
    NoDatabasesFoundError,
    create_database_url,
    delete_all_databases,
    delete_database_instance,
    mapped_database_url,
    read_database_saves_df,
    save_database_instance,
)
from app.ui.components.common import (
    create_field_with_tooltip,
    notify_popup,
    ui_int_input,
)


@ui.refreshable
def _saved_databases_ui(database_instances: ExplodedURLDBInstanceList):
    if not database_instances.items:
        ui.label("Databases are empty.").classes("mx-auto")
        return
    for database in database_instances.items:
        with ui.column().classes("w-full items-stretch border rounded p-4 mb-4 gap-4"):
            with ui.row().classes("w-full items-stretch items-center gap-5"):
                ui.input("Name", value=database.name).classes("flex-grow").bind_value(
                    database, "name"
                )
                ui.input("?Description", value=database.description or "").classes(
                    "flex-grow w-full"
                ).bind_value(database, "description")
                with ui.row().classes("w-full"):
                    ui.input("?Username", value=database.username or "").classes(
                        "flex-grow"
                    ).bind_value(database, "username")
                    ui.input(
                        "?Password",
                        value=database.password or "",
                        password=True,
                    ).classes("flex-grow").bind_value(database, "password")
                    ui.input("Host", value=database.host).classes(
                        "flex-grow"
                    ).bind_value(database, "host")
                    ui_int_input(
                        label="?Port",
                        value=database.port or 0,
                        attr_name="port",
                        bind_object=database,
                        width_px=160,
                    )
                ui.input("Database name", value=database.db).classes(
                    "flex-grow"
                ).bind_value(database, "db")

            ui.button(
                on_click=lambda _, database=database: _delete_database_handler(
                    database=database, database_instances=database_instances
                ),
                icon="delete",
            ).classes("mt-auto")


def _add_database_handler(
    database_instances: ExplodedURLDBInstanceList,
    *,
    add_name: Any,
    add_description: Any,
    add_username: Any,
    add_password: Any,
    add_host: Any,
    add_port: Any,
    add_db: Any,
):
    "Takes add inputs from query UI, saves and adds the values of them to a db query object"

    database_id = str(uuid4())

    try:
        db_url = str(
            create_database_url(
                username=add_username.value,
                password=add_password.value,
                host=add_host.value,
                port=int(add_port.value or 0),
                db=add_db.value,
            )
        )
        db_instance = DatabaseInstance(
            id=database_id,
            name=add_name.value,
            description=add_description.value,
            url=db_url,
        )
        ui_db_instance = ExplodedURLDBInstance(
            id=database_id,
            name=add_name.value,
            description=add_description.value,
            username=add_username.value,
            password=add_password.value,
            host=add_host.value,
            port=add_port.value,
            db=add_db.value,
        )

        # Save in csv and add to UI
        save_database_instance(db_instance)
        database_instances.add(ui_db_instance)

        notify_popup(f"Added and saved database `{add_name.value}`", type="positive")

        # Clears the fields after adding
        add_name.value = ""
        add_description.value = ""
        add_username.value = ""
        add_password.value = ""
        add_host.value = ""
        add_port.value = None
        add_db.value = ""

    except Exception as e:
        notify_popup(str(e), type="negative")


def _delete_database_handler(
    *, database: ExplodedURLDBInstance, database_instances: ExplodedURLDBInstanceList
) -> None:
    "Deletes `database` from database saves csv and from ui list `databases`"
    try:
        delete_database_instance(database.id)
        database_instances.remove(database)
        notify_popup(f"Successfully deleted database `{database.name}`", "positive")
    except Exception as e:
        notify_popup(str(e), "negative")
        return


def _save_all_databases_handler(database_instances: ExplodedURLDBInstanceList):
    try:
        for query in database_instances.items:
            # Validate fields
            ExplodedURLDBInstance(**query.model_dump())

        delete_all_databases()

        for database in database_instances.items:
            db_url = str(
                create_database_url(
                    username=database.username,
                    password=database.password,
                    host=database.host,
                    port=database.port,
                    db=database.db,
                )
            )
            database = DatabaseInstance(
                id=database.id,
                name=database.name,
                description=database.description,
                url=db_url,
            )
            save_database_instance(database)
        notify_popup("Successfully saved all databases", type="positive")
    except Exception as e:
        notify_popup(str(e), type="negative")
        return


def _add_databases_component(database_instances: ExplodedURLDBInstanceList) -> None:
    "Loads component to add more databases with input"

    with ui.card().classes(
        "mt-10 w-full items-stretch overflow-hidden border border-gray"
    ):
        with ui.element("div").classes(
            "fixed top-0 right-12 z-[9999] p-4 flex items-center"
        ):
            ui.button(
                "Save All Databases",
                on_click=lambda _: _save_all_databases_handler(database_instances),
            )

        ui.label().bind_text_from(database_instances, "title").classes(
            "text-semibold text-2xl"
        )
        add_name = create_field_with_tooltip(
            "Name to help identify the database (can be anything)",
            lambda: ui.input("Name")._props('autocomplete="off"'),
        )
        add_description = create_field_with_tooltip(
            "Description with some info about the database (ex: partitions, indexes)",
            lambda: ui.input("?Description")._props('autocomplete="off"'),
        )

        ui.label("Database URL fields:").classes(
            "text-gray-400 w-100 mx-20 mt-10 text-lg"
        )
        with ui.row().classes("w-full"):
            add_username = create_field_with_tooltip(
                "Username of the database login",
                lambda: ui.input("?Username")._props('autocomplete="off"'),
            )
            add_password = create_field_with_tooltip(
                "Password of the database login",
                lambda: ui.input(
                    "?Password", password=True, password_toggle_button=True
                )._props('autocomplete="off"'),
            )
            add_host = create_field_with_tooltip(
                "Host of the database (often docker service name locally)",
                lambda: ui.input("Host")._props('autocomplete="off"'),
            )
            add_port = create_field_with_tooltip(
                "Port of the database (defaults to 5432)",
                lambda: ui.number("?Port")._props('autocomplete="off"'),
            )
            add_db = create_field_with_tooltip(
                "Name of the database",
                lambda: ui.input(
                    "Database name",
                )._props('autocomplete="off"'),
            )

        ui.button(
            "Add database",
            on_click=lambda _: _add_database_handler(
                database_instances,
                add_name=add_name,
                add_description=add_description,
                add_username=add_username,
                add_password=add_password,
                add_host=add_host,
                add_port=add_port,
                add_db=add_db,
            ),
        ).classes("mt-auto")


def ui_load_databases(databases: ExplodedURLDBInstanceList):
    try:
        saves_df = read_database_saves_df().replace(
            {np.nan: None, pd.NA: None, pd.NaT: None}
        )

    except NoDatabasesFoundError:
        return

    if saves_df.empty:
        return

    def process_database(database_instance_row):
        id = database_instance_row.id
        name = database_instance_row["name"]
        description = database_instance_row["description"]
        url_map, db_name = mapped_database_url(database_instance_row.url)
        if not url_map["host"] or not db_name:
            raise ValueError(
                f"Error while loading databases, either username `{url_map['username']}` "
                f"or host `{url_map['host']}` or db name `{db_name}` is None"
            )
        db_instance = ExplodedURLDBInstance(
            id=id,
            name=name,
            description=description,
            username=url_map["username"],
            password=url_map["password"],
            host=url_map["host"],
            port=url_map["port"],
            db=db_name,
        )
        databases.add(db_instance)

    saves_df = saves_df.apply(process_database, axis=1)


def _saved_databases_component(database_instances: ExplodedURLDBInstanceList) -> None:
    "Loads component with a grid for all saved databases"

    ui.label("Saved databases").classes("text-semibold text-2xl mt-10")
    with ui.grid(columns=2).classes("w-full mx-auto"):
        _saved_databases_ui(database_instances)
        ui_load_databases(database_instances)
    ui.space().classes("h-20")


def databases_component() -> None:
    database_instances = ExplodedURLDBInstanceList(
        title="Add databases", on_change=_saved_databases_ui.refresh
    )
    _add_databases_component(database_instances)
    _saved_databases_component(database_instances)
