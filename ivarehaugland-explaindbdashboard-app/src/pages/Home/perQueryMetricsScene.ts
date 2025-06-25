import {
  VizPanel,
  QueryVariable,
  EmbeddedScene,
  PanelBuilders,
  SceneControlsSpacer,
  SceneFlexItem,
  SceneFlexLayout,
  SceneQueryRunner,
  SceneRefreshPicker,
  SceneTimePicker,
  SceneTimeRange,
  SceneVariableSet,
  VariableValueSelectors,
  SceneDataTransformer,
} from '@grafana/scenes';
import { DATASOURCE_REF } from '../../constants';
import { ThresholdsMode } from '@grafana/schema';

export function perQueryMetricScene() {
  const timeRange = new SceneTimeRange({
    from: 'now-72h',
    to: 'now',
  });

  const queryNameVariable = new QueryVariable({
    datasource: DATASOURCE_REF,
    name: 'query_name',
    label: 'query_name',
    value: 'query_name',
    query: {
      refId: 'A',
      label: 'query_name',
    },
  });

  // Query runner definition, using Grafana built-in TestData datasource
  const queryRunner = new SceneQueryRunner({
    datasource: DATASOURCE_REF,
    queries: [
      {
        datasource: DATASOURCE_REF,
        direction: 'backward',
        editorMode: 'builder',
        queryType: 'range',
        refId: 'A',
      },
    ],
  });

  const nodeGraphNodePlanRunner = new SceneQueryRunner({
    datasource: DATASOURCE_REF,
    queries: [
      {
        ...queryRunner.state.queries[0],
        refId: 'Nodes',
        expr: '{job="vector"} |= `graph_node_logger` |= `$query_name` |= `mainstat`',
      },
      {
        ...queryRunner.state.queries[0],
        refId: 'Edges',
        expr: '{job="vector"} |= `graph_node_logger` |= `$query_name` |= `source`',
      },
    ],
  });

  const graphNodePlanTransformRunner = (runner: SceneQueryRunner) => {
    return new SceneDataTransformer({
      $data: runner,
      transformations: [
        {
          id: 'extractFields',
          options: {
            delimiter: ',',
            replace: true,
            source: 'Line',
          },
        },
        {
          id: 'extractFields',
          options: {
            delimiter: ',',
            keepTime: false,
            replace: true,
            source: 'message',
          },
        },
        {
          id: 'extractFields',
          options: {
            delimiter: ',',
            format: 'kvp',
            source: 'node',
          },
        },
        {
          id: 'extractFields',
          options: {
            delimiter: ',',
            format: 'kvp',
            source: 'edge',
          },
        },
        {
          id: 'filterFieldsByName',
          options: {
            include: {
              names: [
                'id',
                'title',
                'mainstat',
                'secondarystat',
                'detail__Actual Total Time',
                'detail__Actual Startup Time',
                'source',
                'target',
              ],
              pattern: '^(?!(edge)|(node)|(query_name)).*',
            },
          },
        },
        {
          id: 'renameByRegex',
          options: {
            regex: 'mainstat',
            renamePattern: 'Timing',
          },
        },
        {
          id: 'renameByRegex',
          options: {
            regex: 'secondarystat',
            renamePattern: 'Detail',
          },
        },
        {
          id: 'renameByRegex',
          options: {
            regex: 'title',
            renamePattern: 'Node Type',
          },
        },
        {
          id: 'renameByRegex',
          options: {
            regex: '^detail__(.*)$',
            renamePattern: '$1',
          },
        },
        {
          id: 'filterFieldsByName',
          options: {},
        },
      ],
    });
  };

  const executionOrderTreesRunner = new SceneQueryRunner({
    datasource: DATASOURCE_REF,
    queries: [
      {
        ...queryRunner.state.queries[0],
        expr: `{job="vector"} |= \`explain_logger\`|= \`$query_name\` |= \`level_divide\``,
      },
    ],
  });

  const executionOrderTreesData = new SceneDataTransformer({
    $data: executionOrderTreesRunner,
    transformations: [
      {
        id: 'extractFields',
        options: {
          delimiter: ',',
          format: 'json',
          jsonPaths: [],
          keepTime: false,
          replace: false,
          source: 'Line',
        },
      },
      {
        id: 'extractFields',
        options: {
          delimiter: ',',
          format: 'json',
          replace: true,
          source: 'message',
        },
      },
      {
        disabled: true,
        id: 'formatString',
        options: {
          outputFormat: 'Substring',
          stringField: 'index',
          substringEnd: 0,
          substringStart: 0,
        },
      },
    ],
  });

  const nodeMetricsRunner = new SceneQueryRunner({
    datasource: DATASOURCE_REF,
    queries: [
      {
        ...queryRunner.state.queries[0],
        expr: `{job="vector"} |= \`graph_node_logger\` != \`source\` or \`target\` or \`mainstat\` |= \`$query_name\``,
      },
    ],
  });

  const nodeMetricsData = new SceneDataTransformer({
    $data: nodeMetricsRunner,
    transformations: [
      {
        id: 'extractFields',
        options: {
          delimiter: ',',
          keepTime: false,
          replace: true,
          source: 'Line',
        },
      },
      {
        id: 'extractFields',
        options: {
          delimiter: ',',
          replace: true,
          source: 'message',
        },
      },
      {
        id: 'extractFields',
        options: {
          delimiter: ',',
          replace: true,
          source: 'node',
        },
      },
      {
        id: 'filterFieldsByName',
        options: {
          include: {
            pattern: '^(?!(edge|description)).*',
          },
        },
      },
      {
        disabled: true,
        id: 'renameByRegex',
        options: {
          regex: '^detail__(.*)$',
          renamePattern: '$1',
        },
      },
      {
        id: 'convertFieldType',
        options: {
          conversions: [
            {
              destinationType: 'number',
              targetField: 'timing_ms',
            },
            {
              destinationType: 'number',
              targetField: 'timing_pct',
            },
            {
              destinationType: 'number',
              targetField: 'Actual Rows',
            },
            {
              destinationType: 'number',
              targetField: 'Total Cost',
            },
            {
              destinationType: 'number',
              targetField: 'Actual Total Time',
            },
            {
              destinationType: 'number',
              targetField: 'Actual Startup Time',
            },
          ],
          fields: {},
        },
      },
    ],
  });

  const queryStmtRunner = new SceneQueryRunner({
    datasource: DATASOURCE_REF,
    queries: [
      {
        ...queryRunner.state.queries[0],
        expr: `{job="vector"} |= \`explain_logger\` |= \`$query_name\` |= \`db_name\` != \`level_divide\` | json | line_format \`{{.message_sql}}\``,
      },
    ],
  });

  const totalExecutionRunner = new SceneQueryRunner({
    datasource: DATASOURCE_REF,
    queries: [
      {
        ...queryRunner.state.queries[0],
        expr: `{job="vector"} |= \`explain_logger\` |= \`$query_name\` != \`level_divide\` |= \`total_exc_time\` | json | keep message_total_exc_time, message_query_name | line_format \`{{.message_total_exc_time}} {{.message_query_name}}\``,
      },
    ],
  });

  const totalExecutionData = new SceneDataTransformer({
    $data: totalExecutionRunner,
    transformations: [
      {
        id: 'extractFields',
        options: {
          delimiter: ',',
          replace: true,
          source: 'labels',
        },
      },
      {
        id: 'convertFieldType',
        options: {
          conversions: [
            {
              destinationType: 'number',
              targetField: 'message_total_exc_time',
            },
          ],
          fields: {},
        },
      },
    ],
  });

  const planRawRunner = new SceneQueryRunner({
    datasource: DATASOURCE_REF,
    queries: [
      {
        ...queryRunner.state.queries[0],
        expr: `{ job="vector" } |= \`"source_type":"explain_file_json"\` |= \`$query_name\` | json`,
      },
    ],
  });

  const planRawData = new SceneDataTransformer({
    $data: planRawRunner,
    transformations: [
      {
        id: 'filterFieldsByName',
        options: {
          include: {
            pattern: 'Line|Time',
          },
        },
      },
      {
        disabled: true,
        id: 'extractFields',
        options: {
          delimiter: ',',
          keepTime: true,
          replace: true,
          source: 'Line',
        },
      },
    ],
  });

  return new EmbeddedScene({
    $timeRange: timeRange,
    $variables: new SceneVariableSet({ variables: [queryNameVariable] }),
    body: new SceneFlexLayout({
      wrap: 'wrap',
      direction: 'row',
      children: [
        new SceneFlexItem({
          width: 2000,
          minWidth: 400,
          minHeight: 800,
          body: PanelBuilders.nodegraph()
            // Title is using variable value
            .setTitle('Execution Plan Graph for $query_name')
            .setData(graphNodePlanTransformRunner(nodeGraphNodePlanRunner))
            .build(),
        }),
        new SceneFlexItem({
          minWidth: 300,
          minHeight: 600,
          body: new VizPanel({
            $data: executionOrderTreesData,
            pluginId: 'pgillich-tree-panel',
            pluginVersion: '0.1.9',
            title: 'Level Order Tree for $query_name',
            fieldConfig: {
              defaults: {},
              overrides: [],
            },
            options: {
              VariableSort: 3,
              expandLevel: 0,
              orderLevels: 'asc',
              rootName: 'Level order tree',
              serieColumn: 'serieColumn',
              showItemCount: true,
              treeFieldTemplateEngine: 'simple',
              treeFields: '${level_divide}',
            },
          }),
        }),
        new SceneFlexItem({
          width: 1100,
          minWidth: 400,
          minHeight: 800,
          body: new VizPanel({
            $data: nodeMetricsData,
            pluginId: 'table',
            title: 'Node Metrics for $query_name',
            fieldConfig: {
              defaults: {
                custom: {
                  align: 'auto',
                  cellOptions: {
                    type: 'auto',
                    wrapText: true,
                  },
                  inspect: true,
                },
                mappings: [],
                thresholds: {
                  mode: 'absolute' as ThresholdsMode,
                  steps: [
                    {
                      color: 'green',
                      value: 0,
                    },
                    {
                      color: 'red',
                      value: 80,
                    },
                  ],
                },
                color: {
                  mode: 'thresholds',
                },
                links: [],
              },
              overrides: [
                {
                  matcher: {
                    id: 'byName',
                    options: 'query_name',
                  },
                  properties: [
                    {
                      id: 'custom.width',
                      value: 382,
                    },
                  ],
                },
                {
                  matcher: {
                    id: 'byName',
                    options: 'db_name',
                  },
                  properties: [
                    {
                      id: 'custom.width',
                      value: 123,
                    },
                  ],
                },
                {
                  matcher: {
                    id: 'byName',
                    options: 'timing_pct',
                  },
                  properties: [
                    {
                      id: 'unit',
                      value: 'percent',
                    },
                    {
                      id: 'custom.width',
                      value: 90,
                    },
                  ],
                },
                {
                  matcher: {
                    id: 'byRegexp',
                    options: '(.*)(timing_ms|Time)(.*)',
                  },
                  properties: [
                    {
                      id: 'unit',
                      value: 'ms',
                    },
                  ],
                },
                {
                  matcher: {
                    id: 'byName',
                    options: 'Node Type',
                  },
                  properties: [
                    {
                      id: 'custom.width',
                      value: 89,
                    },
                  ],
                },
                {
                  matcher: {
                    id: 'byName',
                    options: 'timing_ms',
                  },
                  properties: [
                    {
                      id: 'custom.width',
                      value: 90,
                    },
                  ],
                },
                {
                  matcher: {
                    id: 'byName',
                    options: 'Actual Startup Time',
                  },
                  properties: [
                    {
                      id: 'custom.width',
                      value: 154,
                    },
                  ],
                },
                {
                  matcher: {
                    id: 'byName',
                    options: 'Actual Total Time',
                  },
                  properties: [
                    {
                      id: 'custom.width',
                      value: 135,
                    },
                  ],
                },
                {
                  matcher: {
                    id: 'byName',
                    options: 'Total Cost',
                  },
                  properties: [
                    {
                      id: 'custom.width',
                      value: 86,
                    },
                  ],
                },
                {
                  matcher: {
                    id: 'byName',
                    options: 'Actual Rows',
                  },
                  properties: [
                    {
                      id: 'custom.width',
                      value: 102,
                    },
                  ],
                },
                {
                  matcher: {
                    id: 'byName',
                    options: 'index',
                  },
                  properties: [
                    {
                      id: 'custom.width',
                      value: 54,
                    },
                  ],
                },
                {
                  matcher: {
                    id: 'byName',
                    options: 'node_type_detail',
                  },
                  properties: [
                    {
                      id: 'custom.width',
                      value: 280,
                    },
                  ],
                },
              ],
            },
            options: {
              showHeader: true,
              cellHeight: 'sm',
              footer: {
                show: false,
                reducer: ['sum'],
                countRows: false,
                fields: '',
              },
              sortBy: [
                {
                  desc: false,
                  displayName: 'index',
                },
              ],
            },
          }),
        }),
        new SceneFlexItem({
          width: 400,
          minWidth: 400,
          minHeight: 400,
          body: new VizPanel({
            $data: totalExecutionData,
            pluginId: 'gauge',
            title: 'Total Execution Time for $query_name',
            fieldConfig: {
              defaults: {
                custom: {
                  align: 'auto',
                  cellOptions: {
                    type: 'auto',
                    wrapText: true,
                  },
                  inspect: true,
                },
                mappings: [],
                thresholds: {
                  mode: 'absolute' as ThresholdsMode,
                  steps: [
                    {
                      color: 'green',
                      value: 0,
                    },
                    {
                      color: 'red',
                      value: 80,
                    },
                  ],
                },
                color: {
                  mode: 'thresholds',
                },
                links: [],
                unit: 'ms',
              },
              overrides: [],
            },
            options: {
              displayMode: 'lcd',
              legend: {
                calcs: [],
                displayMode: 'list',
                placement: 'bottom',
                showLegend: false,
              },
              maxVizHeight: 300,
              minVizHeight: 16,
              minVizWidth: 8,
              namePlacement: 'top',
              orientation: 'horizontal',
              reduceOptions: {
                calcs: [],
                values: true,
              },
              showUnfilled: true,
              sizing: 'auto',
              valueMode: 'color',
            },
          }),
        }),
        new SceneFlexItem({
          width: 1000,
          minWidth: 400,
          minHeight: 600,
          body: PanelBuilders.logs()
            // Title is using variable value
            .setTitle('SQL Statement for $query_name')
            .setData(queryStmtRunner)
            .setOption('wrapLogMessage', true)
            .build(),
        }),
        new SceneFlexItem({
          width: 1130,
          minWidth: 400,
          minHeight: 800,
          body: new VizPanel({
            $data: planRawData,
            pluginId: 'logs',
            title: 'Plan Raw for $query_name',
            options: {
              showLabels: false,
              showCommonLabels: false,
              wrapLogMessage: false,
              prettifyLogMessage: true,
              enableLogDetails: true,
              enableInfiniteScrolling: true,
              dedupStrategy: 'none',
              sortOrder: 'Descending',
            },
          }),
        }),
      ],
    }),
    controls: [
      new VariableValueSelectors({}),
      new SceneControlsSpacer(),
      new SceneTimePicker({ isOnCanvas: true }),
      new SceneRefreshPicker({
        intervals: ['5s', '1m', '1h'],
        isOnCanvas: true,
      }),
    ],
  });
}
