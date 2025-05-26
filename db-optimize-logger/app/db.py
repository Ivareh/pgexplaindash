import json
from pathlib import Path
from typing import Any

from logs.logger import logger
from sqlalchemy import TextClause, bindparam, create_engine, text
from sqlalchemy.dialects.postgresql import BOOLEAN, JSON

engine = create_engine(
    "postgresql+psycopg2://pom_oltp_superuser:changethis@db:5432/pom_oltp_db"
)


# @sync_timing_tracker
def execute_exp_analyze_stmt(
    statement: TextClause, query_id: str, **stmt_info
) -> dict[Any, Any]:  # noqa: ARG001
    # Returns JSON string representation of explain analyze response
    logger.info(f"Performing query with query_id={query_id}")
    with engine.begin() as conn:
        response = conn.execute(statement)

    assert response

    response_dump: dict[Any, Any] = response.scalar_one()[0]

    assert isinstance(response_dump, dict)

    # print("\n\n\n")
    # print("STATEMENT:")
    # print(statement)
    # print("\n\n\n")
    # print("RESPONSE DUMP:")
    # print(response_dump)
    # print("\n\n\n")

    return response_dump


def add_line_id(response_dump: dict[Any, Any]) -> dict[Any, Any]:
    current_id = [0]  # Start with id 1

    def process_item(key: str, value: Any, layer_id: int) -> tuple[str, Any, str]:
        nonlocal current_id
        unique_id = current_id[0]
        prefix_id = f"{unique_id}:{layer_id}"
        new_key = f"{prefix_id}:{key}"

        if isinstance(value, dict):
            current_id[0] += 1
            new_dict = {}
            for k, v in value.items():
                processed_k, processed_v, prefix_id = process_item(k, v, layer_id + 1)
                new_dict[processed_k] = processed_v
                if "0:0" in prefix_id:
                    new_dict[f"{prefix_id}:Parent_Node"] = new_key
            return (new_key, new_dict, prefix_id)

        elif isinstance(value, list):
            new_list = []
            for item in value:
                if isinstance(item, dict):
                    current_id[0] += 1
                    list_item = {}
                    for k, v in item.items():
                        processed_k, processed_v, prefix_id = process_item(
                            k, v, layer_id + 1
                        )
                        list_item[processed_k] = processed_v
                        list_item[f"{prefix_id}:Parent Node"] = new_key
                    new_list.append(list_item)
                else:
                    new_list.append(item)
            return (new_key, new_list, prefix_id)

        else:
            return (new_key, value, prefix_id)

    transformed = {}
    for k, v in response_dump.items():
        _, new_value, _ = process_item(k, v, 0)

        transformed[f"{k}"] = new_value

    return transformed


def save_json_response(
    response_dump: dict[Any, Any], filename: str, output_dir: Path
) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / filename
    logger.info(f"Saving response object to '{file_path}'")

    # print("\n\n\n\n RESP_DUMP_TO_SAVE: ", transformed, "\n\n\n\n")

    with open(file_path, "w") as f:
        # json.dump(transformed, f, indent=2)
        json.dump(response_dump, f, indent=2)

    return str(file_path)


def flatten_with_paths(data: dict) -> dict:
    """Preserves nested structure in keys using path notation"""
    flattened = {}

    def process(path, item):
        if isinstance(item, dict):
            for k, v in item.items():
                process(k, v)
        elif isinstance(item, list):
            for element in item:
                process(path, element)
        else:
            flattened[path] = item

    process("", data)
    return flattened


def load_sql_script(script_path: Path) -> None:
    logger.info(f"Loading sql script '{script_path}'")
    ddl = script_path.read_text()
    with engine.begin() as conn:
        conn.execute(text(ddl))


def convert_json_analyze_to_text(
    exp_analyze_json: dict[Any, Any], do_analyze: bool, do_verbose: bool
) -> str:
    logger.info("Converting json explain response to text format")
    exp_analyze_l = [exp_analyze_json]

    sql = text(
        """
        SELECT *
        FROM json_explain_to_text_explain(
        CAST(:exp_analyze AS json),
        :do_analyze,
        :do_verbose
        )
    """
    ).bindparams(
        bindparam("exp_analyze", type_=JSON),
        bindparam("do_analyze", type_=BOOLEAN),
        bindparam("do_verbose", type_=BOOLEAN),
    )

    with engine.begin() as conn:
        rows = (
            conn.execute(
                sql,
                {
                    "exp_analyze": exp_analyze_l,
                    "do_analyze": do_analyze,
                    "do_verbose": do_verbose,
                },
            )
            .scalars()
            .all()
        )

    rows = [row for row in rows if row]
    return "\n".join(rows)
