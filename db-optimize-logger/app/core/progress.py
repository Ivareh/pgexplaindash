from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui


@dataclass
class Progress:
    loading: bool
    on_change: Callable

    def set_loading(self, loading: bool) -> None:
        self.loading = loading
        self.on_change()


@ui.refreshable
async def query_progress(queries_progress: Progress):
    if queries_progress.loading:
        with ui.spinner(size="lg") as spinner:
            spinner.set_visibility(True)
    else:
        with ui.spinner(size="lg") as spinner:
            spinner.set_visibility(False)
