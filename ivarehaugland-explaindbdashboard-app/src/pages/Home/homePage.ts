import { SceneAppPage } from '@grafana/scenes';
import { prefixRoute } from '../../utils/utils.routing';
import { ROUTES } from '../../constants';
import { overallMetricsScene } from './overallMetricsScene';
import { perQueryMetricScene } from './perQueryMetricsScene';

const getOverallMetScene = () => {
  return overallMetricsScene();
};

const getPerQueryScene = () => {
  return perQueryMetricScene();
};

export const homePage = new SceneAppPage({
  title: 'Explain queries main page',
  url: prefixRoute(ROUTES.Home),
  routePath: `${ROUTES.Home}/*`,
  subTitle: 'Get overall metrics and drilldown to per query metrics',
  getScene: () => getOverallMetScene(),
  tabs: [
    new SceneAppPage({
      title: 'Overall Metrics',
      url: prefixRoute(ROUTES.Home),
      routePath: '/',
      getScene: getOverallMetScene,
    }),
    new SceneAppPage({
      title: 'Per Query Metrics',
      url: prefixRoute(`${ROUTES.Home}/per-query-metrics`),
      getScene: getPerQueryScene,
      routePath: '/per-query-metrics',
    }),
  ],
});
