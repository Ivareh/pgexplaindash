import { EmbeddedScene, SceneFlexLayout, SceneFlexItem, PanelBuilders } from '@grafana/scenes';

export function explainScene() {
  return new EmbeddedScene({
    body: new SceneFlexLayout({
      children: [
        new SceneFlexItem({
          width: '100%',
          height: 300,
          body: PanelBuilders.text()
            .setTitle('Explain panel')
            .setOption('content', 'Check out explain queries in depth here!')
            .build(),
        }),
      ],
    }),
  });
}
