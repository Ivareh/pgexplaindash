from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import ParamSpec, TypeVar

from logs.logger import logger

Param = ParamSpec("Param")
RetType = TypeVar("RetType")


def sync_timing_tracker(func: Callable[Param, RetType]) -> Callable[Param, RetType]:
    @wraps(func)
    def wrap(*args: Param.args, **kwargs: Param.kwargs) -> RetType:
        start_time = perf_counter()
        result = func(*args, **kwargs)
        end_time = perf_counter()
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds

        logger.info(f"'{list(kwargs.values())}:{total_time:.2f}ms")

        return result

    return wrap
