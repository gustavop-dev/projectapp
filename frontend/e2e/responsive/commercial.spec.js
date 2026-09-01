/** R-commercial-01: commercial catalog routes must retain an actionable record, not just a page heading, at every responsive profile. */
import { test, expect, assertResponsiveScenario } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { viewportUse } from '../helpers/viewports.js';
import { RESPONSIVE_PROFILES, batchForScenario, getResponsiveScenario } from './catalog-scenarios.js';

const json = (body) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
const proposal = { id: 1, uuid: 'commercial-responsive-proposal', title: 'Propuesta de implementación', client_name: 'Acme Comercial', client_email: 'acme@test.com', status: 'draft', total_investment: 5000000, currency: 'COP', sections: [] };
const diagnostic = { id: 1, title: 'Diagnóstico responsive', client_name: 'Acme Comercial', client_email: 'acme@test.com', status: 'draft', uuid: 'diagnostic-1', sections: [] };
const hourPackage = { id: 1, name_es: 'Paquete 20 horas', name_en: '20 hour package', nationality: 'COL', currency: 'COP', hours: 20, hourly_rate: '100000.00', discount_percent: 0, is_active: true };
const moduleFixture = { id: 1, name: 'Analítica comercial', slug: 'analitica-comercial', category: 'analytics', description: 'Módulo con una acción visible.' };

async function setupCommercial(page) {
  await setAuthLocalStorage(page, { token: 'commercial-responsive-token', userAuth: { id: 9001, role: 'admin', is_staff: true, is_superuser: true } });
  await mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'auth/check/') return json({ user: { username: 'admin', is_staff: true, is_superuser: true } });
    if (apiPath === 'proposals/' && method === 'GET') return json([proposal]);
    if (apiPath === 'proposals/1/' || apiPath === 'proposals/1/detail/') return json(proposal);
    if (apiPath === 'diagnostics/' && method === 'GET') return json({ results: [diagnostic], count: 1, page: 1, num_pages: 1, meta: {} });
    if (apiPath === 'diagnostics/1/' || apiPath === 'diagnostics/1/detail/') return json(diagnostic);
    if (apiPath === 'hour-packages/admin/' && method === 'GET') return json([hourPackage]);
    if (apiPath === 'hour-packages/admin/1/' && method === 'GET') return json(hourPackage);
    if (apiPath === 'additional-modules/' && method === 'GET') return json([moduleFixture]);
    if (apiPath.startsWith('accounts/saved-filter-tabs') || apiPath.includes('client-profiles/search')) return json([]);
    if (apiPath.includes('defaults')) return json({});
    return null;
  });
}

const visualKeys = [
  'frontend/pages/panel/additional-modules/index.vue', 'frontend/pages/panel/proposals/index.vue', 'frontend/pages/panel/proposals/create.vue', 'frontend/pages/panel/proposals/[id]/edit.vue', 'frontend/pages/panel/defaults.vue', 'frontend/pages/panel/hour-packages/index.vue', 'frontend/pages/panel/hour-packages/create.vue', 'frontend/pages/panel/hour-packages/[id]/edit.vue', 'frontend/pages/panel/diagnostics/index.vue', 'frontend/pages/panel/diagnostics/create.vue', 'frontend/pages/panel/diagnostics/[id]/edit.vue',
].map(getResponsiveScenario);
const flowForScenario = {
  'frontend/pages/panel/additional-modules/index.vue': 'admin-additional-modules-manage',
  'frontend/pages/panel/proposals/index.vue': 'admin-proposal-actions-modal',
  'frontend/pages/panel/proposals/create.vue': 'admin-proposal-create',
  'frontend/pages/panel/proposals/[id]/edit.vue': 'admin-proposal-edit',
  'frontend/pages/panel/defaults.vue': 'admin-proposal-defaults-config',
  'frontend/pages/panel/hour-packages/index.vue': 'admin-hour-packages-list',
  'frontend/pages/panel/hour-packages/create.vue': 'admin-hour-packages-create',
  'frontend/pages/panel/hour-packages/[id]/edit.vue': 'admin-hour-packages-edit',
  'frontend/pages/panel/diagnostics/index.vue': 'admin-diagnostic-list',
  'frontend/pages/panel/diagnostics/create.vue': 'admin-diagnostic-create',
  'frontend/pages/panel/diagnostics/[id]/edit.vue': 'admin-diagnostic-edit',
};

async function exerciseCommercialView(page, scenario) {
  await setupCommercial(page);
  // quality: allow-deep-link (the exact catalog route and fixture id are the behavior under responsive inspection)
  await page.goto(scenario.resolvedUrl, { waitUntil: 'domcontentloaded' });
  const entry = {
    'frontend/pages/panel/additional-modules/index.vue': { action: () => page.getByTestId('additional-module-new').click(), value: 'Analítica comercial' },
    'frontend/pages/panel/proposals/index.vue': { action: () => page.getByTestId('proposal-actions-1').click(), value: 'Propuesta de implementación' },
    'frontend/pages/panel/proposals/create.vue': { action: () => page.getByRole('button', { name: 'Manual' }).click(), value: 'Nueva Propuesta' },
    'frontend/pages/panel/proposals/[id]/edit.vue': { action: () => page.getByTestId('edit-email-preview-select').click(), value: 'Propuesta de implementación' },
    'frontend/pages/panel/defaults.vue': { action: () => page.getByTestId('defaults-mode-diagnostic').click(), value: 'Valores por Defecto' },
    'frontend/pages/panel/hour-packages/index.vue': { action: () => page.getByRole('link', { name: /Nuevo paquete/i }).click(), value: 'Paquete 20 horas' },
    'frontend/pages/panel/hour-packages/create.vue': { action: () => page.getByLabel('Nombre (ES)').fill('Paquete responsive'), value: 'Paquete responsive' },
    'frontend/pages/panel/hour-packages/[id]/edit.vue': { action: () => page.getByLabel('Horas', { exact: true }).fill('24'), value: '24' },
    'frontend/pages/panel/diagnostics/index.vue': { action: () => page.getByTestId('diagnostic-actions-1').click(), value: 'Diagnóstico responsive' },
    'frontend/pages/panel/diagnostics/create.vue': { action: () => page.getByPlaceholder(/buscar/i).fill('Acme'), value: 'Acme Comercial' },
    'frontend/pages/panel/diagnostics/[id]/edit.vue': { action: () => page.getByTestId('diagnostic-edit-title').fill('Diagnóstico responsive editado'), value: 'Diagnóstico responsive editado' },
  }[scenario.catalogKey];
  await entry.action();
  const content = page.getByText(entry.value, { exact: true });
  await expect(content).toHaveCount(1);
  return content;
}

for (const profile of RESPONSIVE_PROFILES) {
  test.describe(`commercial catalog · ${profile}`, { tag: [`@viewport:${profile}`] }, () => {
    test.use(viewportUse(profile));
    for (const scenario of visualKeys) {
      test(`${scenario.label} preserves its actionable commercial fixture`, { tag: [`@flow:${flowForScenario[scenario.catalogKey]}`, '@outcome:display', '@responsive:commercial', `@responsive-scenario:${scenario.catalogKey}`, `@responsive-batch:${batchForScenario(scenario.catalogKey)}`, `@viewport:${profile}`] }, async ({ page }, testInfo) => {
        const priorityLocator = await exerciseCommercialView(page, scenario);
        await expect(priorityLocator).toHaveCount(1);
        await assertResponsiveScenario(page, testInfo, scenario, { profile, priorityLocator });
      });
    }
  });
}

test.describe('commercial responsive special', () => {
  test.use(viewportUse('compact'));
  test('proposal row actions remain available without hover in the compact list', { tag: ['@flow:admin-proposal-actions-modal', '@outcome:success', '@responsive-special:commercial', '@viewport:compact', '@responsive-batch:commercial-special-1'] }, async ({ page }) => {
    await setupCommercial(page);
    // quality: allow-deep-link (catalog scenario covers the list route; this pins the compact action sheet)
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });
    await page.getByRole('button', { name: 'Acciones de Propuesta de implementación', exact: true }).click();
    const dialog = page.getByRole('dialog', { name: 'Propuesta de implementación', exact: true });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole('link', { name: /^Ver preview\b/ })).toHaveAttribute('href', '/proposal/commercial-responsive-proposal?preview=1');
  });
});
