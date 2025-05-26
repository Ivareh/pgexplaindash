from pathlib import Path

from db import (
    add_line_id,
    convert_json_analyze_to_text,
    execute_exp_analyze_stmt,
    flatten_with_paths,
    load_sql_script,
    save_json_response,
)
from logs.logger import exp_text_logger, setup_logging
from node_graph_plan import process_node_graph
from sqlalchemy import text


def log_explain(query_id: str, explain_text: str) -> None:
    explain_text = "\n" + explain_text
    exp_text_logger.info(f"query_id={query_id}&explain_text={explain_text}")


if __name__ == "__main__":
    setup_logging()

    sql_script = Path("/app/app/scripts/json_explain_to_text_explain.sql")
    load_sql_script(sql_script)

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
        response_dump = execute_exp_analyze_stmt(
            statement=statement,
            query_id=query_id,
        )

        output_dir = Path("/app/responses_output")
        filename = f"{query_id}_response.json"

        exp_str = convert_json_analyze_to_text(
            response_dump, do_analyze=True, do_verbose=False
        )

        response_dump = add_line_id(response_dump)

        response_dump = flatten_with_paths(response_dump)
        process_node_graph(response_dump)

        save_json_response(response_dump, filename=filename, output_dir=output_dir)

        log_explain(query_id=query_id, explain_text=exp_str)

    # print(f"""EXPLAIN ANALYZE TEXT:

    # {exp_str}

    # """)
