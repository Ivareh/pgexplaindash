from db import execute_sql_stmt
from logs.logger import setup_logging
from sqlalchemy import text

if __name__ == "__main__":
    setup_logging()

    execute_sql_stmt(
        statement=text(
            """
            EXPLAIN (ANALYZE, FORMAT JSON) SELECT item."itemId", item."createdHoursSinceLaunch", item."itemBaseTypeId",
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
        query_id="default_query",
    )
