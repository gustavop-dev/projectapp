/** R-mcp-01: MCP connector controls must remain touch-reachable, including token disclosure and active state. */
import { test, expect, assertResponsiveScenario } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { viewportUse } from '../helpers/viewports.js';
import { RESPONSIVE_PROFILES, batchForScenario, getResponsiveScenario } from './catalog-scenarios.js';

const json = (body) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
const connector = { slug: 'blog', name: 'Blog Publisher', description: 'Publica contenido fixture.', is_active: false, has_token: false, token_prefix: '', connection_status: 'error', recent_events: [], tools: [{ name: 'create_blog_post', description: 'Crea un post.' }] };
const scenario = getResponsiveScenario('frontend/pages/panel/mcps/index.vue');

async function setup(page) {
  await setAuthLocalStorage(page, { token: 'mcp-responsive-token', userAuth: { id: 1, role: 'admin', is_staff: true, is_superuser: true } });
  await mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'auth/check/') return json({ user: { username: 'admin', is_staff: true, is_superuser: true } });
    if (apiPath === 'mcp-connectors/' && method === 'GET') return json([connector]);
    if (apiPath === 'mcp-connectors/blog/generate-token/' && method === 'POST') return json({ connector_url: 'https://projectapp.test/api/mcp/blog/token/', token_prefix: 'token' });
    if (apiPath === 'mcp-connectors/blog/' && method === 'PATCH') return json({ ...connector, is_active: true });
    return null;
  });
}

for (const profile of RESPONSIVE_PROFILES) {
  test.describe(`mcp catalog · ${profile}`, { tag: [`@viewport:${profile}`] }, () => {
    test.use(viewportUse(profile));
    test('connector expands to expose its concrete tool without hover', { tag: ['@flow:admin-mcps', '@outcome:display', '@responsive:mcp', `@responsive-scenario:${scenario.catalogKey}`, `@responsive-batch:${batchForScenario(scenario.catalogKey)}`, `@viewport:${profile}`] }, async ({ page }, testInfo) => {
      await setup(page);
      // quality: allow-deep-link (the catalog connector management route is the fixture-specific inspection point)
      await page.goto(scenario.resolvedUrl, { waitUntil: 'domcontentloaded' });
      await page.getByTestId('mcp-card-header-blog').click();
      const priorityLocator = page.getByText('create_blog_post', { exact: true });
      await expect(priorityLocator).toHaveCount(1);
      await assertResponsiveScenario(page, testInfo, scenario, { profile, priorityLocator });
    });
  });
}

test.describe('mcp responsive special', () => {
  test.use(viewportUse('portrait'));
  test('connector dismisses its generated token dialog', { tag: ['@flow:admin-mcps', '@outcome:success', '@responsive-special:mcp', '@viewport:portrait', '@responsive-batch:mcp-special-1'] }, async ({ page }) => {
    await setup(page);
    // quality: allow-deep-link (the connector card is the responsive action surface under test)
    await page.goto('/en-us/panel/mcps', { waitUntil: 'domcontentloaded' });
    await page.getByTestId('mcp-card-header-blog').click();
    await page.getByTestId('mcp-generate-token-blog').click();
    await expect(page.getByTestId('mcp-token-url')).toContainText('/api/mcp/blog/token/');
    await page.getByTestId('mcp-token-close').click();
    await expect(page.getByTestId('mcp-token-modal')).toHaveCount(0);
  });

  test('connector exposes its active state after the touch toggle', { tag: ['@flow:admin-mcps', '@outcome:success', '@responsive-special:mcp', '@viewport:portrait', '@responsive-batch:mcp-special-1'] }, async ({ page }) => {
    await setup(page);
    // quality: allow-deep-link (the connector card is the responsive action surface under test)
    await page.goto('/en-us/panel/mcps', { waitUntil: 'domcontentloaded' });
    await page.getByTestId('mcp-card-header-blog').click();
    await page.getByTestId('mcp-toggle-blog').click();
    await expect(page.getByTestId('mcp-status-blog')).toHaveText('Activo');
  });
});
