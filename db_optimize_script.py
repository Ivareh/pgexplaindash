import sqlalchemy as sqla

from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import ParamSpec, TypeVar

from logs.logger import logger, exp_analyze_logger, setup_logging

Param = ParamSpec("Param")
RetType = TypeVar("RetType")


engine = sqla.create_engine(
    "postgresql+psycopg2://pom_oltp_superuser:changethis@localhost:5432/pom_oltp_db"
)


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


@sync_timing_tracker
def execute_sql_stmt(stmt, **stmt_info):
    with engine.begin() as conn:
        resp = conn.execute(stmt).scalars().all()
        exp_analyze_logger.info(resp)


if __name__ == "__main__":
    setup_logging()

    execute_sql_stmt(
        sqla.text(
            """
        EXPLAIN ANALYZE SELECT item."itemId", item."createdHoursSinceLaunch", item."itemBaseTypeId",
            item."currencyId", item."currencyAmount", currency."tradeName", currency."valueInChaos",
            currency."createdHoursSinceLaunch" AS "currencyCreatedHoursSinceLaunch"

            FROM item JOIN currency ON currency."currencyId" = item."currencyId"
            WHERE item.league = 'Phrecia' AND item."createdHoursSinceLaunch" >= 0 AND item."createdHoursSinceLaunch" <= 312

            AND

            (EXISTS (SELECT 1 FROM item_modifier

            WHERE item."itemId" = item_modifier."itemId" AND item_modifier."modifierId" = 85

            AND item_modifier."createdHoursSinceLaunch" >= 0 AND item_modifier."createdHoursSinceLaunch" <= 312
            ))

            AND item.name = 'Watcher''s Eye' AND item."itemBaseTypeId"= 29;
        """
        ),
        tables="item&item_modifier&currency",
        mods="Watcher's eye with increased maximum life",
        time="1week",
    )
