import pluginJson from './plugin.json';

export const PLUGIN_BASE_URL = `/a/${pluginJson.id}`;

export enum ROUTES {
  Home = 'home',
}

export const DATASOURCE_REF = {
  uid: 'dol-loki',
  type: 'Loki',
};
