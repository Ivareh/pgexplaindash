import {
  EmbeddedScene,
  SceneControlsSpacer,
  SceneFlexItem,
  SceneFlexLayout,
  SceneQueryRunner,
  SceneRefreshPicker,
  SceneTimePicker,
  SceneTimeRange,
  VariableValueSelectors,
  SceneDataTransformer,
  VizPanel,
} from '@grafana/scenes';
import { DATASOURCE_REF } from '../../constants';
import { ThresholdsMode } from '@grafana/schema';

export function overallMetricsScene() {
  const timeRange = new SceneTimeRange({
    from: 'now-72h',
    to: 'now',
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

  const totalExecutionRunner = new SceneQueryRunner({
    datasource: DATASOURCE_REF,
    queries: [
      {
        ...queryRunner.state.queries[0],
        expr: `{job="vector"} |= \`explain_logger\` != \`level_divide\` |= \`total_exc_time\` | json | keep message_total_exc_time, message_query_name | line_format \`{{.message_total_exc_time}} {{.message_query_name}}\``,
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

  const allQueriesTableRunner = new SceneQueryRunner({
    datasource: DATASOURCE_REF,
    queries: [
      {
        ...queryRunner.state.queries[0],
        expr: `{job="vector"} |= \`explain_logger\` |= \`db_name\` != \`level_divide\``,
      },
    ],
  });

  const allQueriesData = new SceneDataTransformer({
    $data: allQueriesTableRunner,
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
          replace: true,
          source: 'message',
        },
      },
      {
        id: 'sortBy',
        options: {
          fields: {},
          sort: [
            {
              field: 'total_exc_time',
            },
          ],
        },
      },
    ],
  });

  const allDatabasesRunner = new SceneQueryRunner({
    datasource: DATASOURCE_REF,
    queries: [
      {
        ...queryRunner.state.queries[0],
        expr: `{job="vector"} |= \`db_logger\` |= \`db_name\` != \`level_divide\``,
      },
    ],
  });

  const allDatabasesData = new SceneDataTransformer({
    $data: allDatabasesRunner,
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
        id: 'organize',
        options: {
          excludeByName: {},
          includeByName: {},
          indexByName: {
            db_description: 1,
            db_name: 0,
            db_url: 2,
          },
          renameByName: {},
        },
      },
    ],
  });

  return new EmbeddedScene({
    $timeRange: timeRange,
    body: new SceneFlexLayout({
      wrap: 'wrap',
      direction: 'row',
      children: [
        new SceneFlexItem({
          minWidth: 300,
          minHeight: 600,
          body: new VizPanel({
            $data: totalExecutionData,
            pluginId: 'gauge',
            title: 'Total Execution Times',
            fieldConfig: {
              defaults: {
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
                  mode: 'continuous-GrYlRd',
                },
                links: [
                  {
                    title: '',
                    url: 'http://localhost:3000/a/ivarehaugland-explaindbdashboard-app/home/per-query-metrics?from=now-72h&to=now&timezone=browser&var-query_name=${__data.fields.message_query_name}',
                  },
                ],
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
              orientation: 'auto',
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
          width: 1700,
          minWidth: 400,
          minHeight: 800,
          body: new VizPanel({
            $data: allQueriesData,
            pluginId: 'table',
            title: 'All Queries',
            fieldConfig: {
              defaults: {
                custom: {
                  align: 'auto',
                  cellOptions: {
                    type: 'auto',
                  },
                  inspect: true,
                },
                mappings: [],
                thresholds: {
                  mode: 'absolute' as ThresholdsMode, // ignore
                  steps: [
                    {
                      color: 'green',
                      value: 1,
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
                links: [
                  {
                    title: '',
                    url: 'http://localhost:3000/a/ivarehaugland-explaindbdashboard-app/home/per-query-metrics?from=now-72h&to=now&timezone=browser&var-query_name=${__data.fields.query_name}',
                  },
                ],
                unit: 'ms',
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
                      value: 199,
                    },
                  ],
                },
                {
                  matcher: {
                    id: 'byName',
                    options: 'sql',
                  },
                  properties: [
                    {
                      id: 'custom.width',
                      value: 1054,
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
                  desc: true,
                  displayName: 'total_exc_time',
                },
              ],
            },
          }),
        }),
        new SceneFlexItem({
          minWidth: 300,
          minHeight: 600,
          body: new VizPanel({
            $data: allDatabasesData,
            pluginId: 'table',
            title: 'All Databases',
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
              overrides: [
                {
                  matcher: {
                    id: 'byName',
                    options: 'db_url',
                  },
                  properties: [
                    {
                      id: 'custom.width',
                      value: 349,
                    },
                  ],
                },
                {
                  matcher: {
                    id: 'byName',
                    options: 'db_description',
                  },
                  properties: [
                    {
                      id: 'custom.width',
                      value: 1054,
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
              ],
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
              orientation: 'auto',
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
