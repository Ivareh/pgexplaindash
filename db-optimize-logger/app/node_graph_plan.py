import pandas as pd

from app.interface import (
    NODE_TYPE_INFO,
    NodeProp,
    NodeType,
    PlanProp,
)
from app.interface import (
    GrafanaEdgeProp as GEP,
)
from app.interface import (
    GrafanaNodeProp as GNP,
)


def _get_node_type_info(node_type: str):
    node_type = NodeType(node_type)

    return NODE_TYPE_INFO[node_type]


def create_graphnode_table(explain_df: pd.DataFrame) -> pd.DataFrame:
    explain_df = explain_df.explode(PlanProp.NODES)
    nodes = explain_df[PlanProp.NODES]

    graphnode_df = pd.DataFrame(
        {
            GNP.ID.value: nodes.str[NodeProp.NODE_ID],
            GNP.TITLE.value: nodes.str[NodeProp.NODE_TYPE],
            GNP.MAINSTAT.value: nodes.str[NodeProp.TIMING],
            GNP.SECONDARYSTAT.value: nodes.str[NodeProp.ACTUAL_ROWS],
            f"{GNP.DETAIL__.value}{NodeProp.ACTUAL_TOTAL_TIME.value}": nodes.str[
                NodeProp.ACTUAL_TOTAL_TIME
            ],
            f"{GNP.DETAIL__.value}{NodeProp.ACTUAL_STARTUP_TIME.value}": nodes.str[
                NodeProp.ACTUAL_STARTUP_TIME
            ],
        }
    )

    return graphnode_df


def create_graphedge_table(explain_df: pd.DataFrame) -> pd.DataFrame:
    explain_df = explain_df.explode(PlanProp.NODES)
    nodes = explain_df[PlanProp.NODES]

    graphedge_df = pd.DataFrame(
        {
            GEP.ID.value: (
                nodes.str.get(NodeProp.NODE_ID).astype(str)
                + "_"
                + nodes.str.get(NodeProp.PARENT_NODE).astype(str)
            ),
            GEP.SOURCE.value: nodes.str[NodeProp.PARENT_NODE],
            GEP.TARGET.value: nodes.str[NodeProp.NODE_ID],
        }
    )

    graphedge_df = graphedge_df.dropna()

    return graphedge_df
