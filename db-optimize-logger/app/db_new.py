import uuid
from typing import Any

import pandas as pd
from interface import NodeProp as NP


def extract_nodes(plan_dict):
    nodes_list = []

    def traverse(node: dict[str, Any], parent_id=None):
        node_type = node.get(NP.NODE_TYPE, "Unknown")
        node_id = f"{node_type}_{uuid.uuid4().hex[:6]}"
        total = node.get(NP.ACTUAL_TOTAL_TIME, 0)
        startup = node.get(NP.ACTUAL_STARTUP_TIME, 0)
        node_timing = (total - startup) or None
        node_data = {k: v for k, v in node.items() if k != NP.PLANS}

        current_node = {
            NP.NODE_ID: node_id,
            NP.PARENT_NODE: parent_id,
            NP.TIMING: node_timing,
            **node_data,
        }
        nodes_list.append(current_node)
        # Traverse all children in 'Plans'
        for child in node.get(NP.PLANS, []):
            traverse(child, node_id)

    if isinstance(plan_dict, dict):
        traverse(plan_dict)
    return nodes_list


def process_explain_df(explain_df: pd.DataFrame) -> pd.DataFrame:
    explain_df["nodes_data"] = explain_df[NP.PLANS].apply(extract_nodes)

    explain_df = explain_df.explode("nodes_data", ignore_index=True)

    node_details = explain_df["nodes_data"].apply(pd.Series)

    df = pd.concat(
        [explain_df.drop(["nodes_data", "Plan"], axis=1), node_details], axis=1
    )

    return df
