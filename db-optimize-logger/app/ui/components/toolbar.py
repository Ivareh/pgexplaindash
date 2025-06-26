from collections.abc import Callable

from nicegui import ui
from nicegui.page import page
from pydantic import BaseModel


class PageLink(BaseModel):
    label: str
    page: Callable[[], page]


def toolbar(page_links: list[PageLink]):
    "Displays toolbar on top of page"

    with ui.grid(rows="auto 1fr").classes("h-screen, mx-auto w-full"):
        with ui.row():
            for page_link in page_links:
                ui.link(page_link.label, page_link.page).classes(
                    "my-auto text-lg underline-false no-underline"
                )
