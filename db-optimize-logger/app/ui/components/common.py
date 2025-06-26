from typing import Any, Literal

from nicegui import ui
from nicegui.elements.number import Number

from app.logs.logger import app_logger


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


def notify_and_log(
    msg, msg_type: Literal["positive", "negative", "warning", "info", "ongoing"]
) -> None:
    "Both notifies in UI and logs the message"
    match msg_type:
        case "positive":
            app_logger.info(msg)
        case "negative":
            app_logger.error(msg)
        case "warning":
            app_logger.warning(msg)
        case "info":
            app_logger.info(msg)
        case "ongoing":
            app_logger.info(msg)

    notify_popup(msg, msg_type)


def ui_int_input(
    *,
    label: str,
    value: int | float | None,
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
