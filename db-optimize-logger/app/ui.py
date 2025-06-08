import uuid

import dearpygui.dearpygui as dpg
import pandas as pd
from db import (
    DATABASES_SAVES_CSV,
    DatabaseInstance,
    create_db_url,
    delete_all_databases,
    delete_db_instance,
    find_db_instance,
    save_db_instance,
)
from pydantic import PostgresDsn
from query_handler import (
    QUERIES_SAVES_CSV,
    DatabaseQuery,
    delete_all_queries,
    delete_database_query,
    save_database_query,
)

dpg.create_context()


def delete_all_databases_callback():
    children = dpg.get_item_children("databases", slot=1)
    if children:
        for child in list(children):
            dpg.delete_item(child)
    delete_all_databases()


def delete_database(tag: str):
    dpg.delete_item(f"db_id_{tag}")
    dpg.delete_item(f"db_url_fields_{tag}")
    dpg.delete_item(f"db_name_{tag}")
    dpg.delete_item(f"db_username_{tag}")
    dpg.delete_item(f"db_password_{tag}")
    dpg.delete_item(f"db_host_{tag}")
    dpg.delete_item(f"db_port_{tag}")
    dpg.delete_item(f"db_db_{tag}")
    dpg.delete_item(f"db_port_{tag}")
    dpg.delete_item(f"db_save_{tag}")
    dpg.delete_item(f"db_separator_{tag}")
    dpg.delete_item(f"delete_db_{tag}")
    dpg.delete_item(f"db_save_error_{tag}")

    delete_db_instance(tag)


def load_databases() -> None:
    try:
        saves_df = pd.read_csv(DATABASES_SAVES_CSV)
    except FileNotFoundError:
        return

    if saves_df.empty:
        return

    def process_database(database_instance_row):
        id = database_instance_row.id
        name = database_instance_row["name"]
        db_url = PostgresDsn(database_instance_row.url)
        path = db_url.path[1:] if db_url.path else None
        url_dict = db_url.hosts()[0]
        add_database(
            default_tag=id,
            default_name=name,
            default_username=url_dict["username"],
            default_password=url_dict["password"],
            default_host=url_dict["host"],
            default_port=url_dict["port"],
            default_db=path,
        )

    saves_df = saves_df.apply(process_database, axis=1)


def save_database(
    id: str, name: str, username: str, password: str, host: str, port: int, db: str
) -> None:
    db_url = create_db_url(
        username=username,
        password=password,
        host=host,
        port=port,
        db=db,
    )
    db_instance = DatabaseInstance(id=id, name=name, url=str(db_url))
    save_db_instance(db_instance)


def _save_database_callback(sender, app_data, user_data):
    """
    Callback which gets query values from input fields and saves them in save file.

    sender    = the Save button’s tag
    app_data  = None (for a button click)
    user_data = the unique database_tag string
    """
    tag = user_data

    name = dpg.get_value(f"db_name_{tag}")
    username = dpg.get_value(f"db_username_{tag}")
    password = dpg.get_value(f"db_password_{tag}")
    host = dpg.get_value(f"db_host_{tag}")
    port = dpg.get_value(f"db_port_{tag}")
    db = dpg.get_value(f"db_db_{tag}")

    try:
        save_database(
            id=tag,
            name=name,
            username=username,
            password=password,
            host=host,
            port=port,
            db=db,
        )
        dpg.set_item_label(sender, "Saved!")
        if dpg.get_value(f"db_save_error_{tag}"):
            dpg.delete_item(f"db_save_error_{tag}")
    except Exception as e:
        dpg.set_item_label(sender, "Save Database")
        if not dpg.get_value(f"db_save_error_{tag}"):
            dpg.delete_item(f"db_separator_{tag}")
            dpg.add_text(
                default_value=f"Something went wrong saving the database id {tag}\n:{e}",
                color=[255, 0, 0],
                parent=f"database_group_{tag}",
                tag=f"db_save_error_{tag}",
            )
            dpg.add_text(
                default_value="-" * 50,
                parent=f"database_group_{tag}",
                tag=f"db_separator_{tag}",
            )


def _save_all_databases_callback(sender) -> None:
    """Callback which gets all database items and values and saves them in save file."""
    groups = dpg.get_item_children("databases", slot=1) or []

    tags = set()
    for grp in groups:
        children = dpg.get_item_children(grp, slot=1) or []
        for child_id in children:
            child_tag = dpg.get_item_alias(child_id)
            if isinstance(child_tag, str) and child_tag.startswith("db_username_"):
                suffix = child_tag[len("db_username_") :]
                tags.add(suffix)

    for tag in tags:
        name = dpg.get_value(f"db_name_{tag}")
        username = dpg.get_value(f"db_username_{tag}")
        password = dpg.get_value(f"db_password_{tag}")
        host = dpg.get_value(f"db_host_{tag}")
        port = dpg.get_value(f"db_port_{tag}")  # int by virtue of add_input_int
        db = dpg.get_value(f"db_db_{tag}")

        try:
            save_database(
                id=tag,
                name=name,
                username=username,
                password=password,
                host=host,
                port=port,
                db=db,
            )
            if dpg.get_value(f"db_save_error_{tag}"):
                dpg.delete_item(f"db_save_error_{tag}")
            dpg.set_item_label(sender, "Saved!")
        except Exception as e:
            dpg.set_item_label(sender, "Save All Databases")
            if not dpg.get_value(f"db_save_error_{tag}"):
                dpg.delete_item(f"db_separator_{tag}")
                dpg.add_text(
                    default_value=f"Something went wrong saving database:{tag}\nexception:\n{e}",
                    color=[255, 0, 0],
                    parent="databases",
                    tag=f"db_save_error_{tag}",
                )
                dpg.add_text(
                    default_value="-" * 50,
                    parent="databases",
                    tag=f"db_separator_{tag}",
                )


def add_database(
    default_tag: str | None = None,
    default_name: str | None = "",
    default_username: str | None = "",
    default_password: str | None = "",
    default_host: str | None = "",
    default_port: int | None = 0,
    default_db: str | None = "",
) -> None:
    """Adds database items with optional default values and displays them in ui."""

    defaults = {
        "name": default_name or "",
        "username": default_username or "",
        "password": default_password or "",
        "host": default_host or "",
        "port": default_port or 0,
        "db": default_db or "",
    }
    database_tag = default_tag or str(uuid.uuid4())

    group_tag = f"database_group_{database_tag}"
    with dpg.group(tag=group_tag, parent="databases"):
        dpg.add_button(
            label=f"Database id: {database_tag}",
            tag=f"db_id_{database_tag}",
            user_data=database_tag,
            callback=lambda s, a, u: dpg.set_clipboard_text(u),
        )
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("Press to copy to clipboard")

        dpg.add_input_text(
            label="Add name",
            tag=f"db_name_{database_tag}",
            default_value=defaults["name"],
        )

        dpg.add_text(
            default_value="Database URL fields:",
            tag=f"db_url_fields_{database_tag}",
        )

        input_text_fields = [
            ("username", "Add username", False, dpg.add_input_text),
            ("password", "Add password", True, dpg.add_input_text),
            ("host", "Add host", False, dpg.add_input_text),
            ("db", "Add db name", False, dpg.add_input_text),
        ]

        for field_name, label, is_password, widget in input_text_fields:
            widget(
                label=label,
                tag=f"db_{field_name}_{database_tag}",
                password=is_password,
                default_value=defaults[field_name],
            )
        dpg.add_input_int(
            label="Add port",
            tag=f"db_port_{database_tag}",
            default_value=defaults["port"],
        )

        dpg.add_button(
            label="Save Database",
            user_data=database_tag,
            callback=_save_database_callback,
            tag=f"db_save_{database_tag}",
        )

        dpg.add_button(
            label="Delete Database",
            callback=lambda _: delete_database(database_tag),
            tag=f"delete_db_{database_tag}",
        )

        dpg.add_text(
            default_value="-" * 50,
            tag=f"db_separator_{database_tag}",
        )


def delete_query(tag: str):
    dpg.delete_item(f"query_database_id_{tag}")
    dpg.delete_item(f"query_name_{tag}")
    dpg.delete_item(f"query_sql_{tag}")
    dpg.delete_item(f"delete_query_{tag}")
    dpg.delete_item(f"save_query_{tag}")
    dpg.delete_item(f"save_query_{tag}")
    dpg.delete_item(f"query_separator_{tag}")
    dpg.delete_item(f"query_save_error_{tag}")

    delete_database_query(tag)


def delete_all_queries_callback():
    children = dpg.get_item_children("queries", slot=1)
    if children:
        for child in list(children):
            dpg.delete_item(child)
    delete_all_queries()


def load_queries() -> None:
    try:
        saves_df = pd.read_csv(QUERIES_SAVES_CSV)
    except FileNotFoundError:
        return

    if saves_df.empty:
        return

    def process_query(query_row):
        id = query_row.id
        database_id = query_row.db_instance_id
        name = query_row["name"]
        sql = query_row.sql
        add_query(
            default_tag=id,
            default_database_id=database_id,
            default_name=name,
            default_sql=sql,
        )
        try:
            find_db_instance(database_id)
        except ValueError as e:
            dpg.delete_item(f"query_separator_{id}")
            dpg.add_text(
                default_value=str(e),
                color=[255, 0, 0],
                parent="queries",
                tag=f"query_save_error_{id}",
            )
            dpg.add_text(
                default_value="-" * 50,
                parent="queries",
                tag=f"query_separator_{id}",
            )

    saves_df = saves_df.apply(process_query, axis=1)


def save_query(
    id: str,
    database_id: str,
    name: str,
    sql: str,
) -> None:
    db_instance = find_db_instance(database_id)
    db_query = DatabaseQuery(id=id, db_instance=db_instance, name=name, sql=sql)
    save_database_query(db_query)


def _save_query_callback(sender, app_data, user_data):
    """
    Callback which gets query values from input fields and saves them in save file.

    sender    = the Save button’s tag
    app_data  = None (for a button click)
    user_data = the unique database_tag string
    """
    tag = user_data

    database_id = dpg.get_value(f"query_database_id_{tag}")
    name = dpg.get_value(f"query_name_{tag}")
    sql = dpg.get_value(f"query_sql_{tag}")

    error_value = dpg.get_value(f"query_save_error_{tag}")
    try:
        save_query(
            tag,
            database_id,
            name,
            sql,
        )
        dpg.set_item_label(sender, "Saved!")
        if error_value:
            dpg.delete_item(f"query_save_error_{tag}")
    except Exception as e:
        dpg.set_item_label(sender, "Save Query")
        if not error_value:
            dpg.delete_item(f"query_separator_{tag}")
            dpg.add_text(
                default_value=str(e),
                color=[255, 0, 0],
                parent=f"query_group_{tag}",
                tag=f"query_save_error_{tag}",
            )
            dpg.add_text(
                default_value="-" * 50,
                parent=f"query_group_{tag}",
                tag=f"query_separator_{tag}",
            )


def _save_all_queries_callback(sender) -> None:
    groups = dpg.get_item_children("queries", slot=1) or []

    tags = set()
    for grp in groups:
        children = dpg.get_item_children(grp, slot=1) or []
        for child_id in children:
            child_tag = dpg.get_item_alias(child_id)
            if isinstance(child_tag, str) and child_tag.startswith("query_name_"):
                suffix = child_tag[len("query_name_") :]
                tags.add(suffix)

    for tag in tags:
        database_id = dpg.get_value(f"query_database_id_{tag}")
        name = dpg.get_value(f"query_name_{tag}")
        sql = dpg.get_value(f"query_sql_{tag}")

        try:
            save_query(id=tag, database_id=database_id, name=name, sql=sql)
            dpg.set_item_label(sender, "Saved!")
            if dpg.get_value(f"query_save_error_{tag}"):
                dpg.delete_item(f"query_save_error_{tag}")
        except Exception as e:
            dpg.set_item_label(sender, "Save All Queries")
            if not dpg.get_value(f"query_save_error_{tag}"):
                dpg.delete_item(f"query_separator_{tag}")
                dpg.add_text(
                    default_value=f"Something went wrong saving query:{tag}\nexception:\n{e}",
                    color=[255, 0, 0],
                    parent="queries",
                    tag=f"query_save_error_{tag}",
                )
                dpg.add_text(
                    default_value="-" * 50,
                    parent="queries",
                    tag=f"query_separator_{tag}",
                )


def add_query(
    default_tag: str | None = None,
    default_database_id: str | None = None,
    default_name: str | None = None,
    default_sql: str | None = None,
):
    """Adds query items with optional default values and displays them in ui."""

    defaults = {
        "database_id": default_database_id or "",
        "name": default_name or "",
        "sql": default_sql or "",
    }
    query_tag = default_tag or str(uuid.uuid4())
    group_tag = f"query_group_{query_tag}"
    with dpg.group(tag=group_tag, parent="queries"):
        input_text_fields = [
            ("database_id", "Database instance id"),
            ("name", "Query name"),
            ("sql", "Statement"),
        ]
        for field_name, label in input_text_fields:
            dpg.add_input_text(
                label=label,
                tag=f"query_{field_name}_{query_tag}",
                default_value=defaults[field_name],
            )
        dpg.add_button(
            label="Save Query",
            user_data=query_tag,
            callback=_save_query_callback,
            tag=f"save_query_{query_tag}",
        )

        dpg.add_button(
            label="Delete Query",
            callback=lambda _: delete_query(query_tag),
            tag=f"delete_query_{query_tag}",
        )

        dpg.add_text(
            default_value="-" * 50,
            tag=f"query_separator_{query_tag}",
        )


with dpg.window(label="Query Builder", tag="query_builder", width=400, height=700):
    dpg.add_child_window(
        label="Queries Container",
        tag="queries",
        autosize_x=True,
        height=500,
    )

    load_queries()

    dpg.add_button(label="Add Query", callback=lambda _: add_query())

    dpg.add_button(label="Save All Queries", callback=_save_all_queries_callback)

    dpg.add_button(label="Delete All Queries", callback=delete_all_queries_callback)


with dpg.window(
    label="Database Builder", tag="database_builder", width=400, height=700
):
    dpg.add_child_window(
        label="Databases Container",
        tag="databases",
        autosize_x=True,
        height=500,
    )

    load_databases()

    dpg.add_button(label="Add Database", callback=lambda _: add_database())

    dpg.add_button(label="Save All Databases", callback=_save_all_databases_callback)

    dpg.add_button(label="Delete All Databases", callback=delete_all_databases_callback)

dpg.create_viewport(title="DearPyGui – Delete All Example", width=1000, height=1000)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
