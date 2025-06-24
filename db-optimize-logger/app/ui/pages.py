from nicegui import ui

from app.ui.components.database import databases_component
from app.ui.components.query import (
    queries_component,
)
from app.ui.components.toolbar import PageLink, toolbar


def show_toolbar():
    toolbar(
        [
            PageLink(label="Main", page=main_page),
            PageLink(label="Add databases", page=databases_page),
            PageLink(label="Add queries", page=queries_page),
        ],
    )


@ui.page("/")
def main_page():
    ui.dark_mode(value=True)
    show_toolbar()

    ui.label("HEY GUYS")


@ui.page("/databases")
def databases_page():
    ui.dark_mode(value=True)
    show_toolbar()

    databases_component()


@ui.page("/queries")
def queries_page():
    ui.dark_mode(value=True)
    show_toolbar()

    queries_component()
