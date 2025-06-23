from typing import Any, Literal

from nicegui import ui
from nicegui.elements.number import Number


def create_field_with_tooltip(tooltip_text, widget_factory):
    "Helper to create an inline field with tooltip"

    with ui.row().classes("items-center items-stretch mx-12"):
        with ui.icon("info", size="sm").classes("text-blue-400 cursor-help mt-6"):
            ui.tooltip(tooltip_text).classes("text-base")
        widget = widget_factory().classes("flex-1")
    return widget


def notify_popup(
    message: str,
    type: Literal[
        "positive",
        "negative",
        "warning",
        "info",
        "ongoing",
    ],
) -> None:
    ui.notify(
        message,
        type=type,
        position="bottom-right",
        timeout=5000,  # milliseconds before auto-dismissal
    )


def ui_int_input(
    *,
    label: str,
    value: int | float,
    attr_name: str,
    bind_object: Any,
    width_px: int,
) -> Number:
    return (
        ui.number(label, value=value)
        .classes(f"flex-grow w-[{width_px}]")
        .on_value_change(
            lambda e, q=bind_object: setattr(
                q, attr_name, int(e.value) if e.value else None
            )
        )
        .bind_value(bind_object, attr_name)
    )
