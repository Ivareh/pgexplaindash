from collections.abc import Callable
from functools import wraps
from logging import Logger
from time import perf_counter
from typing import Any, ParamSpec, TypeVar

from app.logs.logger import explain_logger

Param = ParamSpec("Param")
RetType = TypeVar("RetType")


def sync_timing_tracker(func: Callable[Param, RetType]) -> Callable[Param, RetType]:
    @wraps(func)
    def wrap(*args: Param.args, **kwargs: Param.kwargs) -> RetType:
        start_time = perf_counter()
        result = func(*args, **kwargs)
        end_time = perf_counter()
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds

        explain_logger.info(f"'{list(kwargs.values())}:{total_time:.2f}ms")

        return result

    return wrap


def log_key_value(logger: Logger, log_dict: dict[str, Any]) -> None:
    """
    Logs with keys and values for log_dict.
    Vector.dev config uses regex matches to produce an object with key and values
    for items in log_dict.


    NB!: The keys and values in log_dict can't have '&' in them in conflict
    of the regex matches. This is a temporary fault.

    Example:

        Input: log_with_query({"key1": "value1", "key2": "value2"})
        log format: query_name=key1=value1&key2=value2


    """
    log_stmt = "".join([f"{key}={value}&" for key, value in log_dict.items()])
    logger.info(log_stmt[:-1])  # -1 since there's one extra &
