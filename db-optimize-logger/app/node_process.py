import uuid
from typing import Any

import pandas as pd
from interface import NodeProp as NP
from interface import PlanProp as PP


def extract_nodes(plan_dict: dict[str, Any]) -> list[dict[str, Any]]:
    nodes_list = []
    stack: list[tuple[dict, str | None]] = [(plan_dict, None)]  # (node, parent_id)

    index = 0
    while stack:
        node, parent_id = stack.pop()
        node_type = node.get(NP.NODE_TYPE, "Unknown")
        node_id = f"{node_type}_{uuid.uuid4().hex[:8]}"

        # Create node data excluding 'Plans'
        node_data = {k: v for k, v in node.items() if k != NP.PLANS}
        startup_time = node_data[NP.ACTUAL_STARTUP_TIME]
        total_time = node_data[NP.ACTUAL_TOTAL_TIME]
        current_node = {
            **node_data,
            NP.NODE_ID.value: node_id,
            NP.PARENT_NODE.value: parent_id,
            NP.TIMING.value: round(total_time - startup_time, 1),
            NP.INDEX.value: index,
        }
        children = node.get(NP.PLANS, [])
        if children == []:
            current_node[NP.IS_LAST_CHILD.value] = True
        else:
            current_node[NP.BRANCHES.value] = len(children)
        nodes_list.append(current_node)

        for child in reversed(children):
            stack.append((child, node_id))

        index += 1

    return nodes_list


def process_explain_df(
    df: pd.DataFrame,
) -> pd.DataFrame:
    df[PP.NODES.value] = df[PP.PLAN].apply(extract_nodes)

    df = df.drop(columns=[PP.PLAN])

    return df
