import numpy as np
import pandas as pd

from app.interface import (
    GrafanaEdgeEnum as GEE,
)
from app.interface import (
    GrafanaNodeEnum as GNE,
)
from app.interface import (
    NodeEnum,
)


def create_graphnode_table(node_series: pd.Series) -> pd.DataFrame:
    graphnode_df = pd.DataFrame(
        {
            GNE.ID.value: node_series.str[NodeEnum.NODE_ID],
            GNE.TITLE.value: node_series.str[NodeEnum.NODE_TYPE],
            GNE.MAINSTAT.value: node_series.str[NodeEnum.TIMING],
            GNE.SECONDARYSTAT.value: node_series.str[NodeEnum.NODE_TYPE_DETAIL],
            f"{GNE.DETAIL__.value}{NodeEnum.ACTUAL_ROWS.value}": node_series.str[
                NodeEnum.ACTUAL_ROWS
            ],
            f"{GNE.DETAIL__.value}{NodeEnum.ACTUAL_TOTAL_TIME.value}": node_series.str[
                NodeEnum.ACTUAL_TOTAL_TIME
            ],
            f"{GNE.DETAIL__.value}{NodeEnum.ACTUAL_STARTUP_TIME.value}": node_series.str[
                NodeEnum.ACTUAL_STARTUP_TIME
            ],
            f"{GNE.DETAIL__.value}{NodeEnum.TOTAL_COST.value}": node_series.str[
                NodeEnum.TOTAL_COST
            ],
            f"{GNE.DETAIL__.value}{NodeEnum.DESCRIPTION.value}": node_series.str[
                NodeEnum.DESCRIPTION
            ],
        }
    )

    return graphnode_df


def create_graphedge_table(node_series: pd.Series) -> pd.DataFrame:
    graphedge_df = pd.DataFrame(
        {
            GEE.ID.value: (
                node_series.str.get(NodeEnum.NODE_ID).astype(str)
                + "_"
                + node_series.str.get(NodeEnum.PARENT_NODE).astype(str)
            ),
            GEE.SOURCE.value: node_series.str[NodeEnum.PARENT_NODE],
            GEE.TARGET.value: node_series.str[NodeEnum.NODE_ID],
        }
    )

    graphedge_df = graphedge_df.dropna()

    return graphedge_df


def create_level_divider(node_series: pd.Series) -> pd.DataFrame:
    indexes = node_series.str[NodeEnum.INDEX].astype(int)
    is_last_child = node_series.str[NodeEnum.IS_LAST_CHILD].astype(bool)
    node_types = node_series.str.get(NodeEnum.NODE_TYPE).astype(str)

    base_prefix = np.where(indexes == 0, "", np.where(is_last_child, "└ ", "├ "))

    def build_depth_prefix(depth_val, branches):
        parts = []
        for level in range(0, depth_val - 1):
            if level in branches:
                parts.append("│   ")
            else:
                parts.append("    ")
        return "".join(parts)

    depth_prefix = node_series.apply(
        lambda node: build_depth_prefix(node[NodeEnum.DEPTH], node[NodeEnum.BRANCHES])
    )

    # Combine components
    full_prefix = depth_prefix + base_prefix
    level_divider_str = '"' + full_prefix + node_types + '"'

    return pd.concat([node_series, level_divider_str], axis=1).reset_index()
