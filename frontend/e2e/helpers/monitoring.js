import { mockApi } from './api.js';

export const monitoringCaseTitle = 'Consulta N+1 en catálogo de Mimittos';
export const monitoringServerTitle = 'Espacio libre bajo el umbral';
export const monitoringReportTitle = 'Informe semanal de rendimiento';

const json = (body, status = 200) => ({
  status,
  contentType: 'application/json',
  body: JSON.stringify(body),
});

export function monitoringCase({ state = 'pending', title = monitoringCaseTitle, kind = 'project', activities = [] } = {}) {
  const resource = kind === 'server'
    ? { id: 2, name: 'VPS de producción', kind: 'server' }
    : { id: 1, name: 'Mimittos', kind: 'project' };
  return {
    id: kind === 'server' ? 72 : 71,
    title,
    resource,
    source_name: kind === 'server' ? 'Healthcheck' : 'Silk',
    severity: kind === 'server' ? 'critical' : 'warning',
    state,
    condition: 'active',
    first_seen_at: '2026-09-19T10:00:00Z',
    last_seen_at: '2026-09-19T10:05:00Z',
    detections: 3,
    version: 3,
    evidence: kind === 'server' ? { metric: 'disk_free', value: 8, unit: '%' } : { rule: 'n_plus_one', query_count: 12 },
    activities: { results: activities, count: activities.length, page: 1, page_size: 25 },
    deliveries: { results: [], count: 0, page: 1, page_size: 25 },
  };
}

export function installMonitoringMock(page, options = {}) {
  const state = {
    detail: monitoringCase(),
    requests: [],
    ...(options.state || {}),
  };
  const catalog = {
    resources: [
      { id: 1, name: 'Mimittos', kind: 'project' },
      { id: 2, name: 'VPS de producción', kind: 'server' },
    ],
    sources: [
      { id: 11, resource: 1, resource_name: 'Mimittos', name: 'Silk', health: 'current', last_seen_at: '2026-09-19T10:05:00Z', last_error: '' },
      { id: 12, resource: 2, resource_name: 'VPS de producción', name: 'Healthcheck', health: 'stale', last_seen_at: '2026-09-19T09:00:00Z', last_error: 'Sin espacio suficiente' },
    ],
  };
  const report = {
    id: 91,
    title: monitoringReportTitle,
    resource: { id: 1, name: 'Mimittos', kind: 'project' },
    source_name: 'Silk',
    observed_at: '2026-09-18T09:00:00Z',
    text: '# Rendimiento\nSe detectaron 12 consultas N+1.',
  };

  return mockApi(page, async ({ apiPath, method, route }) => {
    if (apiPath === 'auth/check/' && method === 'GET') {
      return json({ user: { username: 'admin', is_staff: true, is_superuser: true } });
    }
    if (apiPath === 'panel/dashboard/' && method === 'GET') {
      return json({ finance: null, proposals: { total_proposals: 0, by_status: {}, recent: [] }, additional_modules: {}, operations: {}, attention: [] });
    }
    if (apiPath === 'monitoring/catalog/' && method === 'GET') return options.catalogFailure ? json({ detail: 'falló' }, 500) : json(catalog);
    if (apiPath === 'monitoring/cases/' && method === 'GET') {
      if (options.listFailure) return json({ detail: 'falló' }, 500);
      const kind = new URL(route.request().url()).searchParams.get('kind');
      const record = kind === 'server' ? monitoringCase({ title: monitoringServerTitle, kind: 'server' }) : state.detail;
      return json({ results: [record], count: 1, page: 1, page_size: 25, total_pages: 1 });
    }
    if (apiPath === 'monitoring/reports/' && method === 'GET') {
      if (options.reportsFailure) return json({ detail: 'falló' }, 500);
      return json({ results: [report], count: 1, page: 1, page_size: 25, total_pages: 1 });
    }
    if (apiPath === 'monitoring/cases/71/' && method === 'GET') return options.detailFailure ? json({ detail: 'falló' }, 500) : json(state.detail);
    if (apiPath === 'monitoring/reports/91/' && method === 'GET') return json(report);
    if (apiPath === 'monitoring/cases/71/state/' && method === 'POST') {
      const payload = route.request().postDataJSON();
      state.requests.push({ apiPath, payload });
      if (options.stateFailure) return json({ detail: 'falló' }, 500);
      if (options.stateConflict) return json({ detail: 'conflicto' }, 409);
      state.detail = { ...state.detail, state: payload.state, version: state.detail.version + 1 };
      return json(state.detail);
    }
    if (apiPath === 'monitoring/cases/71/notes/' && method === 'POST') {
      const payload = route.request().postDataJSON();
      state.requests.push({ apiPath, payload });
      if (options.noteFailure) return json({ detail: 'falló' }, 500);
      if (options.noteValidation) return json({ text: ['La nota no es válida.'] }, 400);
      const activity = { id: state.detail.activities.count + 1, actor_name: 'admin', text: payload.text, created_at: '2026-09-19T10:06:00Z', from_state: '', to_state: '' };
      state.detail = { ...state.detail, activities: { ...state.detail.activities, results: [activity, ...state.detail.activities.results], count: state.detail.activities.count + 1 } };
      return json(activity, 201);
    }
    return null;
  }).then(() => state);
}
