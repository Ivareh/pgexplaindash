from enum import StrEnum

# Check out for Node Types: https://github.com/postgres/postgres/blob/master/src/backend/commands/explain.c#L137


class NodeProp(StrEnum):
    # plan property keys
    NODE_TYPE = "Node Type"
    ACTUAL_ROWS = "Actual Rows"
    PLAN_ROWS = "Plan Rows"
    PLAN_WIDTH = "Plan Width"
    ROWS_REMOVED_BY_FILTER = "Rows Removed by Filter"
    ROWS_REMOVED_BY_JOIN_FILTER = "Rows Removed by Join Filter"
    ACTUAL_STARTUP_TIME = "Actual Startup Time"
    ACTUAL_TOTAL_TIME = "Actual Total Time"
    ACTUAL_LOOPS = "Actual Loops"
    STARTUP_COST = "Startup Cost"
    TOTAL_COST = "Total Cost"
    PLANS = "Plans"
    RELATION_NAME = "Relation Name"
    SCHEMA = "Schema"
    ALIAS = "Alias"
    GROUP_KEY = "Group Key"
    SORT_KEY = "Sort Key"
    SORT_METHOD = "Sort Method"
    SORT_SPACE_TYPE = "Sort Space Type"
    SORT_SPACE_USED = "Sort Space Used"
    JOIN_TYPE = "Join Type"
    INDEX_NAME = "Index Name"
    HASH_CONDITION = "Hash Cond"
    PARENT_RELATIONSHIP = "Parent Relationship"
    SUBPLAN_NAME = "Subplan Name"
    PARALLEL_AWARE = "Parallel Aware"
    WORKERS = "Workers"
    WORKERS_PLANNED = "Workers Planned"
    WORKERS_LAUNCHED = "Workers Launched"
    SHARED_HIT_BLOCKS = "Shared Hit Blocks"
    SHARED_READ_BLOCKS = "Shared Read Blocks"
    SHARED_DIRTIED_BLOCKS = "Shared Dirtied Blocks"
    SHARED_WRITTEN_BLOCKS = "Shared Written Blocks"
    TEMP_READ_BLOCKS = "Temp Read Blocks"
    TEMP_WRITTEN_BLOCKS = "Temp Written Blocks"
    LOCAL_HIT_BLOCKS = "Local Hit Blocks"
    LOCAL_READ_BLOCKS = "Local Read Blocks"
    LOCAL_DIRTIED_BLOCKS = "Local Dirtied Blocks"
    LOCAL_WRITTEN_BLOCKS = "Local Written Blocks"
    IO_READ_TIME = "I/O Read Time"
    IO_WRITE_TIME = "I/O Write Time"
    OUTPUT = "Output"
    HEAP_FETCHES = "Heap Fetches"
    WAL_RECORDS = "WAL Records"
    WAL_BYTES = "WAL Bytes"
    WAL_FPI = "WAL FPI"
    FULL_SORT_GROUPS = "Full-sort Groups"
    PRE_SORTED_GROUPS = "Pre-sorted Groups"
    PRESORTED_KEY = "Presorted Key"
    FILTER = "Filter"
    STRATEGY = "Strategy"
    PARTIAL_MODE = "Partial Mode"
    OPERATION = "Operation"

    # computed by dol
    NODE_ID = "node_id"
    PARENT_NODE = "parent_node"
    TIMING = "timing"  # total actual time subtracted by startup time


class NodeType(StrEnum):
    Result = "Result"
    ProjectSet = "ProjectSet"
    ModifyTable = "ModifyTable"
    Insert = "Insert"
    Update = "Update"
    Delete = "Delete"
    Merge = "Merge"
    Append = "Append"
    MergeAppend = "Merge Append"
    RecursiveUnion = "Recursive Union"
    BitmapAnd = "BitmapAnd"
    BitmapOr = "BitmapOr"
    NestedLoop = "Nested Loop"
    MergeJoin = "Merge Join"
    HashJoin = "Hash Join"
    SeqScan = "Seq Scan"
    SampleScan = "Sample Scan"
    Gather = "Gather"
    GatherMerge = "Gather Merge"
    IndexScan = "Index Scan"
    IndexOnlyScan = "Index Only Scan"
    BitmapIndexScan = "Bitmap Index Scan"
    BitmapHeapScan = "Bitmap Heap Scan"
    TidScan = "Tid Scan"
    TidRangeScan = "Tid Range Scan"
    SubqueryScan = "Subquery Scan"
    FunctionScan = "Function Scan"
    TableFuncScan = "Table Function Scan"
    ValuesScan = "Values Scan"
    CteScan = "CTE Scan"
    NamedTuplestoreScan = "Named Tuplestore Scan"
    WorkTableScan = "WorkTable Scan"
    ForeignScan = "Foreign Scan"
    CustomScan = "Custom Scan"
    Materialize = "Materialize"
    Memoize = "Memoize"
    Sort = "Sort"
    IncrementalSort = "Incremental Sort"
    Group = "Group"
    Aggregate = "Aggregate"
    WindowAgg = "WindowAgg"
    Unique = "Unique"
    SetOp = "SetOp"
    LockRows = "LockRows"
    Limit = "Limit"
    Hash = "Hash"


# Per-node metadata: descriptions + any additional fields to track
NODE_TYPE_INFO: dict[NodeType, dict] = {
    NodeType.Result: {
        "description": "Result Node evaluates target list expressions or filters without scanning children.",
        "fields": [],  # No extra fields
    },
    NodeType.ProjectSet: {
        "description": "ProjectSet Node emits one output row per element of a set-returning function.",
        "fields": [],  # No extra fields
    },
    NodeType.ModifyTable: {
        "description": "ModifyTable Node drives INSERT/UPDATE/DELETE/MERGE operations.",
        "fields": [
            "operation",  # INSERT, UPDATE, DELETE, MERGE
            "table",  # Name of the target table
            "alias",  # Optional alias used in the plan
        ],
    },
    NodeType.Insert: {
        "description": "INSERT operation under a ModifyTable node.",
        "fields": [],
    },
    NodeType.Update: {
        "description": "UPDATE operation under a ModifyTable node.",
        "fields": [],
    },
    NodeType.Delete: {
        "description": "DELETE operation under a ModifyTable node.",
        "fields": [],
    },
    NodeType.Merge: {
        "description": "MERGE operation under a ModifyTable node.",
        "fields": [],
    },
    NodeType.Append: {
        "description": "Append Node concatenates multiple subplans serially.",
        "fields": [],
    },
    NodeType.MergeAppend: {
        "description": "MergeAppend Node merges sorted inputs from multiple subplans.",
        "fields": [],
    },
    NodeType.RecursiveUnion: {
        "description": "RecursiveUnion Node implements recursive CTE processing.",
        "fields": [],
    },
    NodeType.BitmapAnd: {
        "description": "BitmapAnd Node combines bitmaps from multiple BitmapIndexScans.",
        "fields": [],
    },
    NodeType.BitmapOr: {
        "description": "BitmapOr Node unions bitmaps from multiple BitmapIndexScans.",
        "fields": [],
    },
    NodeType.NestedLoop: {
        "description": "Nested Loop Join Node iterates join by probing inner plan per outer row.",
        "fields": [
            "join_type",  # e.g. inner, left, right, full
            "on",  # join condition
        ],
    },
    NodeType.MergeJoin: {
        "description": "Merge Join Node merges two sorted inputs on join keys.",
        "fields": [
            "join_type",  # join type
            "on",  # join condition
        ],
    },
    NodeType.HashJoin: {
        "description": "Hash Join Node hashes the inner side then probes with outer side.",
        "fields": [
            "join_type",  # join type
            "on",  # join condition
        ],
    },
    NodeType.SeqScan: {
        "description": "Seq Scan Node scans the entire table sequentially.",
        "fields": [
            "table",  # name of the table
            "alias",  # table alias, if any
        ],
    },
    NodeType.SampleScan: {
        "description": "Sample Scan Node reads a random sample of table rows.",
        "fields": [
            "table",  # name of the table
            "alias",  # alias used in the plan
            "method",  # sampling method (e.g., SYSTEM or BERNOULLI)
        ],
    },
    NodeType.Gather: {
        "description": "Gather Node collects tuples from parallel worker scans.",
        "fields": [
            "workers",  # number of workers used
        ],
    },
    NodeType.GatherMerge: {
        "description": "Gather Merge Node merges sorted streams from parallel workers.",
        "fields": [
            "workers",  # number of workers used
        ],
    },
    NodeType.IndexScan: {
        "description": "Index Scan Node traverses an index to find matching table rows.",
        "fields": [
            "table",  # name of the table
            "index",  # name of the index used
            "alias",  # alias used in the plan
        ],
    },
    NodeType.IndexOnlyScan: {
        "description": "Index Only Scan Node retrieves data directly from an index without reading the heap.",
        "fields": [
            "table",  # table name
            "index",  # index name
            "alias",  # alias used in the plan
        ],
    },
    NodeType.BitmapIndexScan: {
        "description": "Bitmap Index Scan Node builds a bitmap of matching tuples from an index.",
        "fields": [
            "index",  # index used
        ],
    },
    NodeType.BitmapHeapScan: {
        "description": "Bitmap Heap Scan Node fetches heap rows referenced by a bitmap.",
        "fields": [
            "table",  # table name
            "using",  # bitmap source
        ],
    },
    NodeType.TidScan: {
        "description": "Tid Scan Node fetches table rows by TID list.",
        "fields": [
            "table",  # table name
            "tids",  # list of tuple IDs
        ],
    },
    NodeType.TidRangeScan: {
        "description": "Tid Range Scan Node fetches rows within a range of TIDs.",
        "fields": [
            "table",  # table name
            "range",  # tid range
        ],
    },
    NodeType.SubqueryScan: {
        "description": "Subquery Scan Node treats a subplan like a scanned table.",
        "fields": [
            "subquery_name",  # subquery or CTE name
            "alias",  # alias used
        ],
    },
    NodeType.FunctionScan: {
        "description": "Function Scan Node treats a set-returning function as a table.",
        "fields": [
            "function",  # function name
            "alias",  # alias used
        ],
    },
    NodeType.TableFuncScan: {
        "description": "Table Function Scan Node calls a table-valued function.",
        "fields": [
            "function",  # table function name
            "alias",  # alias used
        ],
    },
    NodeType.ValuesScan: {
        "description": "Values Scan Node returns the rows from a VALUES list.",
        "fields": [
            "values_list",  # list of values used
        ],
    },
    NodeType.CteScan: {
        "description": "CTE Scan Node reads from a previously computed CTE result.",
        "fields": [
            "cte_name",  # name of the CTE
            "alias",  # alias used
        ],
    },
    NodeType.NamedTuplestoreScan: {
        "description": "Named Tuplestore Scan Node reads from a tuplestore by name.",
        "fields": [
            "name",  # name of tuplestore
            "alias",  # alias used
        ],
    },
    NodeType.WorkTableScan: {
        "description": "WorkTable Scan Node reads tuples from a work table.",
        "fields": [
            "worktable_id",  # ID or name of worktable
        ],
    },
    NodeType.ForeignScan: {
        "description": "Foreign Scan Node reads/writes via a foreign data wrapper.",
        "fields": [
            "operation",  # Select, Insert, Update, Delete
            "server",  # foreign server
            "table",  # table name
        ],
    },
    NodeType.CustomScan: {
        "description": "Custom Scan Node for extension-provided plan nodes.",
        "fields": [
            "custom_name",  # name of the custom scan method
        ],
    },
    NodeType.Materialize: {
        "description": "Materialize Node buffers all tuples from its child.",
        "fields": [],
    },
    NodeType.Memoize: {
        "description": "Memoize Node caches child results for repeated calls.",
        "fields": [],
    },
    NodeType.Sort: {
        "description": "Sort Node orders its input by one or more keys.",
        "fields": [
            "sort_keys",  # list of sort expressions
        ],
    },
    NodeType.IncrementalSort: {
        "description": "Incremental Sort Node reuses existing order when possible.",
        "fields": [
            "sort_keys",  # list of sort expressions
        ],
    },
    NodeType.Group: {
        "description": "Group Node collapses adjacent identical grouping-key tuples.",
        "fields": [
            "group_keys",  # group by keys
        ],
    },
    NodeType.Aggregate: {
        "description": "Aggregate Node computes aggregates (e.g. SUM, AVG) over groups.",
        "fields": [
            "strategy",  # Plain, Sorted, Hashed, Mixed
            "partial_mode",  # Simple, Partial, Finalize
        ],
    },
    NodeType.WindowAgg: {
        "description": "WindowAgg Node computes window functions over partitioned input.",
        "fields": [
            "partition_keys",  # PARTITION BY expressions
            "order_keys",  # ORDER BY expressions
        ],
    },
    NodeType.Unique: {
        "description": "Unique Node filters out duplicate consecutive rows.",
        "fields": [
            "on",  # expressions to apply uniqueness
        ],
    },
    NodeType.SetOp: {
        "description": "SetOp Node computes UNION/INTERSECT/EXCEPT over sorted or hashed input.",
        "fields": [
            "strategy",  # Sorted or Hashed
            "cmd",  # UNION, INTERSECT, etc.
        ],
    },
    NodeType.LockRows: {
        "description": "LockRows Node re-scans its child and applies row-level locks.",
        "fields": [
            "lock_mode",  # FOR UPDATE, FOR SHARE, etc.
        ],
    },
    NodeType.Limit: {
        "description": "Limit Node stops after a fixed number of rows, with optional OFFSET.",
        "fields": [
            "limit",  # LIMIT count
            "offset",  # OFFSET value
        ],
    },
    NodeType.Hash: {
        "description": "Hash Node builds a hash table from its input for join or aggregate use.",
        "fields": [],
    },
}


class GrafanaNodeProp(StrEnum):
    "Docs: https://grafana.com/docs/grafana/latest/panels-visualizations/visualizations/node-graph/#nodes-data-frame-structure"

    # Required
    ID = "id"

    # Optional
    TITLE = "title"
    MAINSTAT = "mainstat"  # property: timing (total - startup time)
    SECONDARYSTAT = "secondarystat"  # property: rows
    SOURCE = "source"  # for edge dataset
    DETAIL__ = "detail__"  # add desired prop suffix
    # Todo: add "highlighted" for important paths


class GrafanaEdgeProp(StrEnum):
    "Docs: https://grafana.com/docs/grafana/latest/panels-visualizations/visualizations/node-graph/#edges-data-frame-structure"

    # Required
    ID = "id"
    SOURCE = "source"
    TARGET = "target"
