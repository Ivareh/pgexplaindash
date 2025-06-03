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
            NE.TIMING.value: timing,
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

    total_timing = 0
    for node in nodes_list:
        total_timing += node[NE.TIMING]

    for node in nodes_list:
        pct = round(node[NE.TIMING] / total_timing, 2) * 100
        node[NE.TIMING.value] = f'"{node[NE.TIMING]}ms | {pct:.0f}%"'

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
