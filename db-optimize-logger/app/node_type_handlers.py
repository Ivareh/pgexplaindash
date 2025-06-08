from abc import ABC, abstractmethod
from typing import Any

from interface import (
    NodeEnum as NE,
)
from interface import (
    NodeTypeEnum,
)


class NodeTypeHandler(ABC):
    def __init__(self, node_type_enum: NodeTypeEnum):
        self.node_type_enum = node_type_enum

    @abstractmethod
    def node_type_detail(self, node_data: dict[str, Any]) -> str:
        """Produces a secondary title for the node type"""
        pass

    def node_type_description(self) -> str:
        info = NODE_TYPE_INFO[self.node_type_enum]

        return info[NE.DESCRIPTION.value]


class DefaultNodeTypeHandler(NodeTypeHandler):
    def node_type_detail(self, node_data: dict[str, Any]) -> str:
        return ""


class JoinNodeTypeHandler(NodeTypeHandler):
    def node_type_detail(self, node_data: dict[str, Any]) -> str:
        join_type = node_data[NE.JOIN_TYPE]
        cond = None
        if NE.HASH_COND in node_data and node_data[NE.HASH_COND] is not None:
            cond = node_data[NE.HASH_COND]
        if NE.MERGE_COND in node_data and node_data[NE.MERGE_COND] is not None:
            cond = node_data[NE.MERGE_COND]

        return f"{join_type} join on {cond}"


class SeqScanNodeTypeHandler(NodeTypeHandler):
    def node_type_detail(self, node_data: dict[str, Any]) -> str:
        relation_name = node_data[NE.RELATION_NAME]
        alias = node_data[NE.ALIAS] if node_data[NE.ALIAS] else relation_name

        return f"on {relation_name} as {alias}"


class IndexScanNodeTypeHandler(NodeTypeHandler):
    def node_type_detail(
        self,
        node_data: dict[str, Any],
    ) -> str:
        relation_name = (node_data[NE.RELATION_NAME],)
        alias = node_data[NE.ALIAS] if node_data[NE.ALIAS] else relation_name
        index_name = node_data[NE.INDEX_NAME]

        return f"on {relation_name} as {alias} using {index_name}"


class HashAggregateNodeTypeHandler(NodeTypeHandler):
    def node_type_detail(
        self,
        node_data: dict[str, Any],
    ) -> str:
        group_key = node_data[NE.GROUP_KEY]

        return f"by {group_key}"


class NodeTypeService:
    def __init__(self, node_type_enum: NodeTypeEnum):
        self.node_type_enum = node_type_enum
        self.node_type_handler = self.find_node_type_handler(node_type_enum)

    def _get_node_type_handler_class(
        self,
        node_type_enum: NodeTypeEnum,
    ) -> type[NodeTypeHandler]:
        """Returns the handler class for the given node type enum"""
        info: dict[str, Any] = NODE_TYPE_INFO[node_type_enum]
        handler_class = info["handler"]
        if handler_class is None or not isinstance(
            handler_class, type(NodeTypeHandler)
        ):
            raise ValueError(
                f"Node type enum: {node_type_enum} is not associated with a valid node type handler class"
            )
        return handler_class

    def find_node_type_handler(self, node_type_enum: NodeTypeEnum) -> NodeTypeHandler:
        """Finds handler of node type enum and returns an instance of it"""
        handler_class = self._get_node_type_handler_class(node_type_enum)
        return handler_class(node_type_enum)

    def create_node_type_detail(self, node_data: dict[str, Any]) -> str:
        type_detail = self.node_type_handler.node_type_detail(node_data=node_data)

        return type_detail

    def get_description(self) -> str:
        description = self.node_type_handler.node_type_description()

        return description


# Per-node metadata: descriptions + any additional fields to track
# NB: Descriptions needs improvement
NODE_TYPE_INFO: dict[NodeTypeEnum, dict[str, Any]] = {
    NodeTypeEnum.Result: {
        NE.DESCRIPTION.value: "Result Node evaluates target list expressions or filters without scanning children.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.ProjectSet: {
        NE.DESCRIPTION.value: "ProjectSet Node emits one output row per element of a set-returning function.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.ModifyTable: {
        NE.DESCRIPTION.value: "ModifyTable Node drives INSERT/UPDATE/DELETE/MERGE operations.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.Insert: {
        NE.DESCRIPTION.value: "INSERT operation under a ModifyTable node.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.Update: {
        NE.DESCRIPTION.value: "UPDATE operation under a ModifyTable node.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.Delete: {
        NE.DESCRIPTION.value: "DELETE operation under a ModifyTable node.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.Merge: {
        NE.DESCRIPTION.value: "MERGE operation under a ModifyTable node.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.Append: {
        NE.DESCRIPTION.value: "Append Node concatenates multiple subplans serially.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.MergeAppend: {
        NE.DESCRIPTION.value: "MergeAppend Node merges sorted inputs from multiple subplans.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.RecursiveUnion: {
        NE.DESCRIPTION.value: "RecursiveUnion Node implements recursive CTE processing.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.BitmapAnd: {
        NE.DESCRIPTION.value: "BitmapAnd Node combines bitmaps from multiple BitmapIndexScans.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.BitmapOr: {
        NE.DESCRIPTION.value: "BitmapOr Node unions bitmaps from multiple BitmapIndexScans.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.NestedLoop: {
        NE.DESCRIPTION.value: "Nested Loop Join Node iterates join by probing inner plan per outer row.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.MergeJoin: {
        NE.DESCRIPTION.value: "Merge Join Node merges two sorted inputs on join keys.",
        "handler": JoinNodeTypeHandler,
    },
    NodeTypeEnum.HashJoin: {
        NE.DESCRIPTION.value: "Hash Join Node hashes the inner side then probes with outer side.",
        "handler": JoinNodeTypeHandler,
    },
    NodeTypeEnum.SeqScan: {
        NE.DESCRIPTION.value: "Seq Scan Node scans the entire table sequentially.",
        "handler": SeqScanNodeTypeHandler,
    },
    NodeTypeEnum.SampleScan: {
        NE.DESCRIPTION.value: "Sample Scan Node reads a random sample of table rows.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.Gather: {
        NE.DESCRIPTION.value: "Gather Node collects tuples from parallel worker scans.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.GatherMerge: {
        NE.DESCRIPTION.value: "Gather Merge Node merges sorted streams from parallel workers.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.IndexScan: {
        NE.DESCRIPTION.value: "Index Scan Node traverses an index to find matching table rows.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.IndexOnlyScan: {
        NE.DESCRIPTION.value: "Index Only Scan Node retrieves data directly from an index without reading the heap.",
        "handler": IndexScanNodeTypeHandler,
    },
    NodeTypeEnum.BitmapIndexScan: {
        NE.DESCRIPTION.value: "Bitmap Index Scan Node builds a bitmap of matching tuples from an index.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.BitmapHeapScan: {
        NE.DESCRIPTION.value: "Bitmap Heap Scan Node fetches heap rows referenced by a bitmap.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.TidScan: {
        NE.DESCRIPTION.value: "Tid Scan Node fetches table rows by TID list.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.TidRangeScan: {
        NE.DESCRIPTION.value: "Tid Range Scan Node fetches rows within a range of TIDs.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.SubqueryScan: {
        NE.DESCRIPTION.value: "Subquery Scan Node treats a subplan like a scanned table.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.FunctionScan: {
        NE.DESCRIPTION.value: "Function Scan Node treats a set-returning function as a table.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.TableFuncScan: {
        NE.DESCRIPTION.value: "Table Function Scan Node calls a table-valued function.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.ValuesScan: {
        NE.DESCRIPTION.value: "Values Scan Node returns the rows from a VALUES list.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.CteScan: {
        NE.DESCRIPTION.value: "CTE Scan Node reads from a previously computed CTE result.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.NamedTuplestoreScan: {
        NE.DESCRIPTION.value: "Named Tuplestore Scan Node reads from a tuplestore by name.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.WorkTableScan: {
        NE.DESCRIPTION.value: "WorkTable Scan Node reads tuples from a work table.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.ForeignScan: {
        NE.DESCRIPTION.value: "Foreign Scan Node reads/writes via a foreign data wrapper.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.CustomScan: {
        NE.DESCRIPTION.value: "Custom Scan Node for extension-provided plan nodes.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.Materialize: {
        NE.DESCRIPTION.value: "Materialize Node buffers all tuples from its child.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.Memoize: {
        NE.DESCRIPTION.value: "Memoize Node caches child results for repeated calls.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.Sort: {
        NE.DESCRIPTION.value: "Sort Node orders its input by one or more keys.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.IncrementalSort: {
        NE.DESCRIPTION.value: "Incremental Sort Node reuses existing order when possible.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.Group: {
        NE.DESCRIPTION.value: "Group Node collapses adjacent identical grouping-key tuples.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.Aggregate: {
        NE.DESCRIPTION.value: "Aggregate Node computes aggregates (e.g. SUM, AVG) over groups.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.WindowAgg: {
        NE.DESCRIPTION.value: "WindowAgg Node computes window functions over partitioned input.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.Unique: {
        NE.DESCRIPTION.value: "Unique Node filters out duplicate consecutive rows.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.SetOp: {
        NE.DESCRIPTION.value: "SetOp Node computes UNION/INTERSECT/EXCEPT over sorted or hashed input.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.LockRows: {
        NE.DESCRIPTION.value: "LockRows Node re-scans its child and applies row-level locks.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.Limit: {
        NE.DESCRIPTION.value: "Limit Node stops after a fixed number of rows, with optional OFFSET.",
        "handler": DefaultNodeTypeHandler,
    },
    NodeTypeEnum.Hash: {
        NE.DESCRIPTION.value: "Hash Node builds a hash table from its input for join or aggregate use.",
        "handler": DefaultNodeTypeHandler,
    },
}
