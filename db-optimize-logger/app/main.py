from pathlib import Path
from typing import Any

import pandas as pd
from db import (
    execute_explain_stmt,
)
from logs.logger import explain_logger, graph_node_logger, setup_logging
from node_graph_plan import (
    create_graphedge_table,
    create_graphnode_table,
    create_level_divider,
)
from sqlalchemy import text

from app.node_process import extract_node_series, process_explain_df


def log_with_query(query_id: str, log_dict: dict[str, Any]) -> None:
    """
    Logs query_id with keys and values for log_dict.
    Vector.dev config uses regex matches to produce an object with key and values
    for query_id and items in log_dict.


    NB!: The keys and values in query_id and log_dict can't have '&' in them in conflict
    of the regex matches. This is a temporary fault.

    Example:

        Input: log_with_query("qid1", {"key1": "value1", "key2": "value2"})
        Output: query_id=qid1&key1=value1&key2=value2


    """
    log_stmt = f"query_id={query_id}"
    log_stmt = log_stmt + "".join(
        [f"&{key}={value}" for key, value in log_dict.items()]
    )
    explain_logger.info(log_stmt)


if __name__ == "__main__":
    setup_logging()

    sql_script = Path("/app/app/scripts/json_explain_to_text_explain.sql")
    # load_sql_script(sql_script)

    queries = [
        {
            "query_id": "1 week Watcher Eye Increased Max Life",
            "statement": text(
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
        },
        {
            "query_id": "2 week Watcher Eye Increased Max Life",
            "statement": text(
                """
                    EXPLAIN (ANALYZE, FORMAT JSON) SELECT item."itemId", item."createdHoursSinceLaunch", item."itemBaseTypeId",
                    item."currencyId", item."currencyAmount", currency."tradeName", currency."valueInChaos",
                    currency."createdHoursSinceLaunch" AS "currencyCreatedHoursSinceLaunch"
                    FROM item JOIN currency ON currency."currencyId" = item."currencyId"
                    WHERE item.league = 'Phrecia' AND item."createdHoursSinceLaunch" >= 0 AND item."createdHoursSinceLaunch" <= 624
                    AND
                    (EXISTS (SELECT 1 FROM item_modifier
                    WHERE item."itemId" = item_modifier."itemId" AND item_modifier."modifierId" = 85
                    AND item_modifier."createdHoursSinceLaunch" >= 0 AND item_modifier."createdHoursSinceLaunch" <= 624
                    ))
                    AND item.name = 'Watcher''s Eye' AND item."itemBaseTypeId"= 29;
                """
            ),
        },
    ]

    for query in queries:
        statement = query["statement"]
        query_id = query["query_id"]
        explain_explain_dump = execute_explain_stmt(
            statement=statement,
            query_id=query_id,
        )

        explain_dir = Path("/app/file/explain_output")
        graphs_dir = Path("/app/file/graphs_output")

        explain_df = pd.DataFrame([explain_explain_dump])

        explain_df.to_json(
            explain_dir / f"{query_id}.json", orient="records", lines=True
        )

        explain_df = process_explain_df(explain_df)

        node_series = extract_node_series(explain_df)

        graphnode_df = create_graphnode_table(node_series)
        graphedge_df = create_graphedge_table(node_series)

        graphnode_dict = graphnode_df.to_dict(orient="records")
        graphedge_dict = graphedge_df.to_dict(orient="records")

        for node in graphnode_dict:
            graph_node_logger.info(f"query_id={query_id}&node={node}")
        for edge in graphedge_dict:
            graph_node_logger.info(f"query_id={query_id}&edge={edge}")

        level_divider_df = create_level_divider(node_series)
        level_divider_dict = level_divider_df.to_dict(orient="records")

        for index, level in enumerate(level_divider_dict):
            index_character = chr(
                ord("@") + index + 1
            )  # converts index to corresponding letter in alphabet series
            log_with_query(
                query_id=query_id,
                log_dict={
                    "index": index_character + str(index),
                    "level_divide": level["nodes"],
                },
            )
