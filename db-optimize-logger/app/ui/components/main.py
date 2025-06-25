from docker import DockerClient, errors
from nicegui import ui

from app.core.progress import Progress
from app.docker_app.loki import (
    create_docker_client,
    reset_loki_volume,
    start_loki_container,
)
from app.execute.start_log import start_log
from app.logs.logger import setup_logging
from app.ui.components.common import notify_and_log


@ui.refreshable
def query_progress(queries_progress: Progress):
    ui.linear_progress(value=queries_progress.progress)


def start_queries_logger(client: DockerClient, queries_progress: Progress):
    if queries_progress.progress == 0:
        try:
            start_loki_container(client)
        except errors.APIError as e:
            if e.args[0].response.status_code == 409:
                notify_and_log(
                    "Logger has already run. Check the logs at http://localhost:3000/a/ivarehaugland-explaindbdashboard-app/home",
                    "info",
                )
            else:
                notify_and_log(
                    f"An error occured while starting loki container: {e}", "negative"
                )
            return
        except Exception as e:
            notify_and_log(
                f"An error occured while starting loki container: {e}", "negative"
            )
            return

        try:
            start_log(queries_progress)
            notify_and_log(
                "Successfully ran logs. Check them at http://localhost:3000/a/ivarehaugland-explaindbdashboard-app/home",
                "positive",
            )
        except Exception as e:
            notify_and_log(
                f"An error occured while starting loki container: {e}", "negative"
            )
            return
    else:
        notify_and_log(
            "Logger has already run. Check the logs at http://localhost:3000/a/ivarehaugland-explaindbdashboard-app/home",
            "info",
        )


def reset_logs(client: DockerClient, queries_progress: Progress):
    queries_progress.set_progress(0)
    try:
        reset_loki_volume(client)
        notify_and_log("Successfully cleared logs from loki database", "positive")
    except errors.APIError as e:
        if e.args[0].response.status_code == 404:
            notify_and_log("There's nothing to clear since logs are empty", "info")
        else:
            notify_and_log(
                f"An error occured while starting queries logger: {e}", "negative"
            )
    except Exception as e:
        notify_and_log(
            f"An error occured while starting queries logger: {e}", "negative"
        )


def main_component() -> None:
    setup_logging()
    client = create_docker_client()

    with ui.card().classes("mx-auto items-center text-xl border border-gray"):
        ui.label("Welcome!")
        ui.label("First add databases, then queries.")
        ui.label("Click `START LOG` when you want to execute your queries.")

        queries_progress = Progress(0, on_change=query_progress.refresh)

        ui.button(
            "START LOG", on_click=lambda: start_queries_logger(client, queries_progress)
        ).classes("text-xl")
        query_progress(queries_progress)
        ui.button(
            "CLEAR LOGS", on_click=lambda: reset_logs(client, queries_progress)
        ).classes("bg-orange")
