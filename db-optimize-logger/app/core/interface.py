from enum import StrEnum


class WarningEnum(StrEnum):
    WARNING = "\033[93m"
    RESET = "\033[0m"


class PlanEnum(StrEnum):
    EXECUTION_TIME = "Execution Time"
    PLANNING_TIME = "Planning Time"
    TRIGGERS = "Triggers"
    PLAN = "Plan"

    # computed by dol
    NODES = "nodes"


# Check out for Node Types: https://github.com/postgres/postgres/blob/master/src/backend/commands/explain.c#L137
class NodeEnum(StrEnum):
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
    JOIN_FILTER = "Join Filter"
    INDEX_NAME = "Index Name"
    HASH_COND = "Hash Cond"
    MERGE_COND = "Merge Cond"
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
    DESCRIPTION = "description"
    NODE_TYPE_DETAIL = "node_type_detail"
    INDEX = "index"  # line index of node in plan (not same as INDEX_NAME)
    NODE_ID = "node_id"
    PARENT_NODE = "parent_node"

    TIMING = "timing"  # timing string with milliseconds and percent. Calculated with total actual time subtracted by startup time
    TIMING_MS = "timing_ms"  #  timing in milliseconds
    TIMING_PROPORTION = "timing_proportion"  # node timing proportion of whole plan
    TIMING_COLOR = "timing_color"

    IS_LAST_CHILD = "is_last_child"
    IS_SUBPLAN = "is_subplan"
    DEPTH = "depth"  # depth/layer number
    BRANCHES = "branches"  # list with indexes of branches


class NodeTypeEnum(StrEnum):
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


class GrafanaNodeEnum(StrEnum):
    "Docs: https://grafana.com/docs/grafana/latest/panels-visualizations/visualizations/node-graph/#nodes-data-frame-structure"

    # Required
    ID = "id"

    # Optional
    TITLE = "title"
    MAINSTAT = "mainstat"  # property: timing (total - startup time)
    SECONDARYSTAT = "secondarystat"  # property: rows
    DETAIL__ = "detail__"  # add desired prop suffix
    NODERADIUS = "nodeRadius"
    COLOR = "color"
    # Todo: add "highlighted" for important paths


class GrafanaEdgeEnum(StrEnum):
    "Docs: https://grafana.com/docs/grafana/latest/panels-visualizations/visualizations/node-graph/#edges-data-frame-structure"

    # Required
    ID = "id"
    SOURCE = "source"
    TARGET = "target"
