import uuid
from typing import Any

import pandas as pd
from interface import (
    NodeEnum as NE,
)
from interface import (
    PlanEnum as PE,
)
from node_type_handlers import (
    NodeTypeService,
)


def calc_timing_color(timing_proportion: float) -> str:
    if timing_proportion >= 0.5:
        return "#FF0000"
    elif 0.10 <= timing_proportion < 0.5:
        return "#FFFF00"
    else:
        return "#008000"


def add_node_timing(nodes_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total_timing = 0
    for node in nodes_list:
        total_timing += node[NE.TIMING_MS]

    for node in nodes_list:
        timing_ms = node[NE.TIMING_MS]
        timing_proportion = round(timing_ms / total_timing, 2)
        timing_pct = timing_proportion * 100
        node[NE.TIMING.value] = f"{timing_ms}ms | {timing_pct:.0f}%"
        node[NE.TIMING_PROPORTION.value] = timing_proportion
        node[NE.TIMING_COLOR.value] = calc_timing_color(timing_proportion)

    return nodes_list


def extract_nodes(plan_dict: dict[str, Any]) -> list[dict[str, Any]]:
    nodes_list = []
    stack: list[tuple[dict, str | None, int, list[int]]] = [
        (plan_dict, None, 0, [])
    ]  # (node, parent_id, depth, branches)

    index = 0
    while stack:
        node, parent_id, node_depth, branches = stack.pop()
        node_type = node.get(NE.NODE_TYPE, "Unknown")
        node_id = f"{node_type}_{uuid.uuid4().hex[:8]}"

        # Create node data excluding 'Plans'
        node_data = {k: v for k, v in node.items() if k != NE.PLANS}

        startup_time = node_data[NE.ACTUAL_STARTUP_TIME]
        total_time = node_data[NE.ACTUAL_TOTAL_TIME]
        timing = round(total_time - startup_time, 1)

        type_service = NodeTypeService(node_type)
        type_detail = type_service.create_node_type_detail(node_data)
        description = type_service.get_description()
        current_node = {
            **node_data,
            NE.NODE_ID.value: node_id,
            NE.PARENT_NODE.value: parent_id,
            NE.INDEX.value: index,
            NE.DEPTH.value: node_depth,
            NE.BRANCHES.value: branches[:-1],
            NE.TIMING.value: None,
            NE.TIMING_COLOR.value: None,
            NE.TIMING_MS.value: timing,
            NE.NODE_TYPE_DETAIL.value: type_detail,
            NE.DESCRIPTION.value: description,
        }
        nodes_list.append(current_node)
        if NE.IS_LAST_CHILD in current_node and current_node[NE.IS_LAST_CHILD.value]:
            branches.remove(node_depth - 1)

        children = node.get(NE.PLANS, [])

        for i, child in reversed(list(enumerate(children))):
            if i == (len(children) - 1):
                child[NE.IS_LAST_CHILD.value] = True
            stack.append((child, node_id, node_depth + 1, branches + [node_depth]))

        index += 1

    nodes_list = add_node_timing(nodes_list)

    return nodes_list


def process_explain_df(
    df: pd.DataFrame,
) -> pd.DataFrame:
    df[PE.NODES.value] = df[PE.PLAN].apply(extract_nodes)

    df = df.drop(columns=[PE.PLAN])

    return df


def extract_node_series(
    explain_df: pd.DataFrame,
) -> pd.Series:
    """Explodes nodes and returns them"""
    explain_df = explain_df.explode(PE.NODES)
    nodes = explain_df[PE.NODES]
    assert isinstance(nodes, pd.Series)

    return nodes
