import React from 'react';
import { SceneApp, useSceneApp } from '@grafana/scenes';
import { AppRootProps } from '@grafana/data';
import { config } from '@grafana/runtime';
import { Alert } from '@grafana/ui';
import { DATASOURCE_REF } from '../../constants';
import { PluginPropsContext } from '../../utils/utils.plugin';
import { homePage } from '../../pages/Home/homePage';

function getSceneApp() {
  return new SceneApp({
    pages: [homePage],
    urlSyncOptions: {
      updateUrlOnInit: true,
      createBrowserHistorySteps: true,
    },
  });
}

function AppWithScenes() {
  const scene = useSceneApp(getSceneApp);

  return (
    <>
      {!config.datasources[DATASOURCE_REF.uid] && (
        <Alert title={`Missing ${DATASOURCE_REF.uid} datasource`}>
          These demos depend on <b>testdata</b> datasource: <code>{JSON.stringify(DATASOURCE_REF)}</code>. See{' '}
          <a href="https://github.com/grafana/grafana/tree/main/devenv#set-up-your-development-environment">
            https://github.com/grafana/grafana/tree/main/devenv#set-up-your-development-environment
          </a>{' '}
          for more details.
        </Alert>
      )}

      <scene.Component model={scene} />
    </>
  );
}

function App(props: AppRootProps) {
  return (
    <PluginPropsContext.Provider value={props}>
      <AppWithScenes />
    </PluginPropsContext.Provider>
  );
}

export default App;
