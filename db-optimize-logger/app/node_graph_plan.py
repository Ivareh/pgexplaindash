import numpy as np
import pandas as pd
from interface import (
    GrafanaEdgeEnum as GEE,
)
from interface import (
    GrafanaNodeEnum as GNE,
)
from interface import (
    NodeEnum,
)


def create_node_metrics_df(node_series: pd.Series) -> pd.DataFrame:
    node_metrics_df = pd.DataFrame(
        {
            NodeEnum.INDEX.value: node_series.str[NodeEnum.INDEX],
            NodeEnum.NODE_TYPE.value: node_series.str[NodeEnum.NODE_TYPE],
            NodeEnum.TIMING_MS.value: node_series.str[NodeEnum.TIMING_MS],
            "timing_pct": node_series.str.get(NodeEnum.TIMING_PROPORTION).astype(float)
            * 100,
            NodeEnum.NODE_TYPE_DETAIL.value: node_series.str[NodeEnum.NODE_TYPE_DETAIL],
            NodeEnum.ACTUAL_ROWS.value: node_series.str[NodeEnum.ACTUAL_ROWS],
            NodeEnum.TOTAL_COST.value: node_series.str[NodeEnum.TOTAL_COST],
            NodeEnum.ACTUAL_TOTAL_TIME.value: node_series.str[
                NodeEnum.ACTUAL_TOTAL_TIME
            ],
            NodeEnum.ACTUAL_STARTUP_TIME.value: node_series.str[
                NodeEnum.ACTUAL_STARTUP_TIME
            ],
            NodeEnum.NODE_TYPE_DETAIL.value: node_series.str[NodeEnum.NODE_TYPE_DETAIL],
            NodeEnum.DESCRIPTION.value: node_series.str[NodeEnum.DESCRIPTION],
        }
    )

    return node_metrics_df


def create_graphnode_table(node_series: pd.Series) -> pd.DataFrame:
    graphnode_df = pd.DataFrame(
        {
            GNE.ID.value: node_series.str[NodeEnum.NODE_ID],
            GNE.TITLE.value: (
                node_series.str.get(NodeEnum.INDEX).astype(str)
                + "  "
                + node_series.str.get(NodeEnum.NODE_TYPE).astype(str)
            ),
            GNE.MAINSTAT.value: node_series.str[NodeEnum.TIMING],
            GNE.SECONDARYSTAT.value: node_series.str[NodeEnum.NODE_TYPE_DETAIL],
            f"{GNE.DETAIL__.value}{NodeEnum.ACTUAL_ROWS.value}": node_series.str[
                NodeEnum.ACTUAL_ROWS
            ],
            f"{GNE.DETAIL__.value}{NodeEnum.ACTUAL_TOTAL_TIME.value}": node_series.str.get(
                NodeEnum.ACTUAL_TOTAL_TIME
            ).astype(str)
            + "ms",
            f"{GNE.DETAIL__.value}{NodeEnum.ACTUAL_STARTUP_TIME.value}": node_series.str.get(
                NodeEnum.ACTUAL_STARTUP_TIME
            ).astype(str)
            + "ms",
            f"{GNE.DETAIL__.value}{NodeEnum.TOTAL_COST.value}": node_series.str[
                NodeEnum.TOTAL_COST
            ],
            f"{GNE.DETAIL__.value}{NodeEnum.DESCRIPTION.value}": node_series.str[
                NodeEnum.DESCRIPTION
            ],
            GNE.NODERADIUS.value: 50,
            GNE.COLOR.value: node_series.str[NodeEnum.TIMING_COLOR],
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

    # **here’s the magic**: swap EVERY normal space for a NBSP
    #   NBSP is Unicode U+00A0, which browsers will render and not collapse.
    full_prefix_nbsp = full_prefix.str.replace(" ", "\u00a0")

    # now append your node label/type
    level_divider_str = full_prefix_nbsp + node_types

    return pd.concat([node_series, level_divider_str], axis=1).reset_index()
