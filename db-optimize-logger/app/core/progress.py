from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Progress:
    progress: float
    on_change: Callable

    def set_progress(self, progress: float) -> None:
        self.progress = progress
        self.on_change()
