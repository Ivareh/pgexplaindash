import {
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
  VizPanel,
  behaviors,
} from '@grafana/scenes';
import { DATASOURCE_REF } from '../../constants';

export function homeScene() {
  const timeRange = new SceneTimeRange({
    from: 'now-6h',
    to: 'now',
  });

  const queryIdVariable = new QueryVariable({
    datasource: DATASOURCE_REF,
    name: 'query_id',
    label: 'query_id',
    value: 'file',
    isMulti: true,
    regex: `(.*)(?:\.json)`,
    query: {
      refId: 'LokiVariableQueryEditor-VariableQuery',
      label: 'file',
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

  const explainTextRunner = new SceneQueryRunner({
    datasource: DATASOURCE_REF,
    queries: [
      {
        ...queryRunner.state.queries[0],
        expr: `{job="vector"} |= \`"logger":"explain_analyze_text"\` | json | line_format \` {{ .message_query_id }} {{ .message_explain_text }}\``,
      },
    ],
  });

  const lineTimeRunner = new SceneQueryRunner({
    datasource: DATASOURCE_REF,
    queries: [
      {
        ...queryRunner.state.queries[0],
        expr: `{job="vector"} |= \`explain_file_json\` |= \`$query_id\``,
      },
    ],
  });

  const lineTimeData = new SceneDataTransformer({
    $data: lineTimeRunner,
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
          source: 'message',
        },
      },
      {
        id: 'filterFieldsByName',
        options: {
          byVariable: false,
          include: {
            pattern: '.*(Total Time|Execution Time)',
          },
        },
      },
    ],
  });

  const lineTimePanel = new SceneFlexItem({
    $behaviors: [
      new behaviors.ActWhenVariableChanged({
        variableName: 'query_id',
        onChange: (variable) => {
          // Set value hidden of the component using this behavior if variable is a list
          const newValue = (variable as any).getValue?.() ?? variable.state;

          // 4) Determine if it’s a “list” (i.e. an array of values)
          const isOne = Array.isArray(newValue) && newValue.length !== 1;

          // 5) Toggle the hidden flag on the flex item
          lineTimePanel.setState({ isHidden: isOne });
        },
      }),
    ],
    minWidth: 300,
    minHeight: 800,
    body: new VizPanel({
      $data: lineTimeData,
      pluginId: 'bargauge',
      title: 'Line time metrics',
      fieldConfig: {
        defaults: {
          mappings: [],
          color: {
            mode: 'continuous-GrYlRd',
          },
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
  });

  const totalExecutionRunner = new SceneQueryRunner({
    datasource: DATASOURCE_REF,
    queries: [
      {
        ...queryRunner.state.queries[0],
        expr: `{job="vector"} |= \`explain_file_json\``,
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
          source: 'message',
        },
      },
      {
        id: 'filterFieldsByName',
        options: {
          byVariable: false,
          include: {
            pattern: '.*(Execution Time|file)',
          },
        },
      },
      {
        id: 'calculateField',
        options: {},
      },
      {
        id: 'filterFieldsByName',
        options: {
          include: {
            pattern: 'Total|file',
          },
        },
      },
    ],
  });

  return new EmbeddedScene({
    $timeRange: timeRange,
    $variables: new SceneVariableSet({
      variables: [queryIdVariable],
    }),
    body: new SceneFlexLayout({
      wrap: 'wrap',
      direction: 'row',
      children: [
        new SceneFlexItem({
          width: 1400,
          minWidth: 400,
          minHeight: 800,
          body: PanelBuilders.logs()
            // Title is using variable value
            .setTitle('Explain analyze text logs')
            .setData(explainTextRunner)
            .build(),
        }),
        lineTimePanel,
        new SceneFlexItem({
          minWidth: 300,
          minHeight: 600,
          body: new VizPanel({
            $data: totalExecutionData,
            pluginId: 'gauge',
            title: 'Total execution times',
            fieldConfig: {
              defaults: {
                mappings: [],
                color: {
                  mode: 'continuous-GrYlRd',
                },
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
