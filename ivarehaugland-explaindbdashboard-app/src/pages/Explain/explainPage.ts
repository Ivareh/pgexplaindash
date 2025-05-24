import { SceneAppPage } from '@grafana/scenes';
import { explainScene } from './explainScene';
import { prefixRoute } from '../../utils/utils.routing';
import { ROUTES } from '../../constants';

export const explainPage = new SceneAppPage({
  title: 'Explain query in depth',
  url: prefixRoute(ROUTES.Explain),
  routePath: ROUTES.Explain,
  getScene: explainScene,
});
