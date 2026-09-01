/** R-content-01: content tools must keep a concrete post, work or public-card action usable across responsive profiles. */
import { test, expect, assertResponsiveScenario } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { viewportUse } from '../helpers/viewports.js';
import { RESPONSIVE_PROFILES, batchForScenario, getResponsiveScenario } from './catalog-scenarios.js';

const json = (body) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
const post = { id: 1, title_es: 'Post responsive', title_en: 'Responsive post', slug: 'post-responsive', excerpt_es: 'Resumen concreto', excerpt_en: 'Concrete summary', content_es: '<p>Contenido fixture</p>', content_en: '<p>Fixture content</p>', category: 'ai', is_published: true, calendar_status: 'published', date: '2026-09-01' };
const work = { id: 1, title_es: 'Proyecto responsive', title_en: 'Responsive project', slug: 'proyecto-responsive', description_es: 'Trabajo fixture', description_en: 'Fixture work', is_published: true, order: 1, content_json_es: {}, content_json_en: {}, created_at: '2026-09-01T00:00:00Z' };
const card = { id: 1, name: 'Tarjeta responsive', destination_type: 'url', destination: 'https://projectapp.test' };
const tree = { id: 1, name: 'Linktree responsive', handle: 'responsive', display_name: 'ProjectApp', buttons: [] };
const keys = ['frontend/pages/panel/blog/index.vue', 'frontend/pages/panel/blog/create.vue', 'frontend/pages/panel/blog/[id]/edit.vue', 'frontend/pages/panel/blog/calendar.vue', 'frontend/pages/panel/linkedin/index.vue', 'frontend/pages/panel/portfolio/index.vue', 'frontend/pages/panel/portfolio/create.vue', 'frontend/pages/panel/portfolio/[id]/edit.vue', 'frontend/pages/panel/qr-cards/index.vue', 'frontend/pages/panel/linktrees/index.vue', 'frontend/pages/panel/linktrees/[id]/edit.vue'].map(getResponsiveScenario);
const flows = {
  'frontend/pages/panel/blog/index.vue': 'admin-blog-list', 'frontend/pages/panel/blog/create.vue': 'admin-blog-create', 'frontend/pages/panel/blog/[id]/edit.vue': 'admin-blog-edit', 'frontend/pages/panel/blog/calendar.vue': 'admin-blog-calendar', 'frontend/pages/panel/linkedin/index.vue': 'admin-blog-linkedin-publish', 'frontend/pages/panel/portfolio/index.vue': 'admin-portfolio-list', 'frontend/pages/panel/portfolio/create.vue': 'admin-portfolio-create', 'frontend/pages/panel/portfolio/[id]/edit.vue': 'admin-portfolio-edit', 'frontend/pages/panel/qr-cards/index.vue': 'admin-qr-cards', 'frontend/pages/panel/linktrees/index.vue': 'admin-linktrees', 'frontend/pages/panel/linktrees/[id]/edit.vue': 'admin-linktrees',
};

async function setup(page) {
  await setAuthLocalStorage(page, { token: 'content-responsive-token', userAuth: { id: 1, role: 'admin', is_staff: true, is_superuser: true } });
  await mockApi(page, async ({ apiPath, method, route }) => {
    if (apiPath === 'auth/check/') return json({ user: { username: 'admin', is_staff: true, is_superuser: true } });
    if (apiPath.startsWith('blog/admin/calendar')) {
      const start = new URL(route.request().url()).searchParams.get('start');
      return json([{ ...post, date: start || post.date }]);
    }
    if (apiPath.startsWith('blog/admin/')) return json(apiPath.split('/').filter(Boolean).length > 3 ? post : { results: [post], count: 1, page: 1, total_pages: 1 });
    if (apiPath === 'portfolio/admin/' && method === 'GET') return json([work]);
    if (apiPath === 'portfolio/admin/1/detail/' && method === 'GET') return json(work);
    if (apiPath === 'portfolio/admin/create/' && method === 'POST') return json(work);
    if (apiPath === 'portfolio/admin/1/update/' && method === 'PATCH') return json(work);
    if (apiPath.includes('qr-cards')) return json([card]);
    if (apiPath.includes('linktrees')) return json(apiPath.split('/').filter(Boolean).length > 3 ? tree : [tree]);
    if (apiPath.includes('linkedin')) return json({ connected: true, posts: [post] });
    if (method === 'PATCH' || method === 'POST') return json({ ...post, ...work });
    return null;
  });
}

async function exercise(page, scenario) {
  await setup(page);
  // quality: allow-deep-link (each catalog editor has a fixture-resolved route; the following UI action proves it mounted)
  await page.goto(scenario.resolvedUrl, { waitUntil: 'domcontentloaded' });
  const entries = {
    'frontend/pages/panel/blog/index.vue': { action: () => page.getByRole('link', { name: 'Post responsive' }).click(), result: () => page.getByRole('heading', { name: 'Editar Blog Post', exact: true }), assert: (locator) => expect(locator).toHaveText('Editar Blog Post') },
    'frontend/pages/panel/blog/create.vue': { action: () => page.getByRole('button', { name: 'Importar JSON', exact: true }).click(), result: () => page.getByRole('heading', { name: 'Pegar o subir JSON', exact: true }), assert: (locator) => expect(locator).toHaveText('Pegar o subir JSON') },
    'frontend/pages/panel/blog/[id]/edit.vue': { action: () => page.getByRole('button', { name: 'Vista previa', exact: true }).click(), result: () => page.getByRole('heading', { name: 'Post responsive', level: 1, exact: true }), assert: (locator) => expect(locator).toHaveText('Post responsive') },
    'frontend/pages/panel/blog/calendar.vue': { action: () => page.getByRole('link', { name: /^Post responsive/ }).click(), result: () => page.getByRole('heading', { name: 'Editar Blog Post', exact: true }), assert: (locator) => expect(locator).toHaveText('Editar Blog Post') },
    'frontend/pages/panel/linkedin/index.vue': { action: () => page.getByRole('button', { name: 'Nuevo post', exact: true }).click(), result: () => page.getByRole('heading', { name: 'Nuevo post', exact: true }), assert: (locator) => expect(locator).toHaveText('Nuevo post') },
    'frontend/pages/panel/portfolio/index.vue': { action: () => page.getByRole('link', { name: 'Proyecto responsive' }).click(), result: () => page.getByRole('heading', { name: 'Editar Proyecto', exact: true }), assert: (locator) => expect(locator).toHaveText('Editar Proyecto') },
    'frontend/pages/panel/portfolio/create.vue': { action: () => page.getByPlaceholder('Título del proyecto en español').fill('Proyecto responsive'), result: () => page.getByPlaceholder('Título del proyecto en español'), assert: (locator) => expect(locator).toHaveValue('Proyecto responsive') },
    'frontend/pages/panel/portfolio/[id]/edit.vue': { action: () => page.getByRole('group', { name: 'Español' }).locator('label:has-text("Título (ES)")').locator('..').locator('input').fill('Proyecto responsive editado'), result: () => page.getByRole('group', { name: 'Español' }).locator('label:has-text("Título (ES)")').locator('..').locator('input'), assert: (locator) => expect(locator).toHaveValue('Proyecto responsive editado') },
    'frontend/pages/panel/qr-cards/index.vue': { action: () => page.getByTestId('qr-card-new').click(), result: () => page.getByTestId('qr-card-form').getByRole('heading', { name: 'Nueva tarjeta', exact: true }), assert: (locator) => expect(locator).toHaveText('Nueva tarjeta') },
    'frontend/pages/panel/linktrees/index.vue': { action: () => page.getByTestId('linktree-new').click(), result: () => page.getByTestId('linktree-form'), assert: (locator) => expect(locator).toContainText('Nuevo linktree') },
    'frontend/pages/panel/linktrees/[id]/edit.vue': { action: () => page.getByTestId('linktree-add-button').click(), result: () => page.getByTestId('linktree-button-row-0'), assert: (locator) => expect(locator).toContainText('Etiqueta') },
  }[scenario.catalogKey];
  await entries.action();
  const priorityLocator = entries.result();
  await entries.assert(priorityLocator);
  return priorityLocator;
}

for (const profile of RESPONSIVE_PROFILES) {
  test.describe(`content catalog · ${profile}`, { tag: [`@viewport:${profile}`] }, () => {
    test.use(viewportUse(profile));
    for (const scenario of keys) {
      test(`${scenario.label} keeps concrete content reachable after its action`, { tag: [`@flow:${flows[scenario.catalogKey]}`, '@outcome:display', '@responsive:content', `@responsive-scenario:${scenario.catalogKey}`, `@responsive-batch:${batchForScenario(scenario.catalogKey)}`, `@viewport:${profile}`] }, async ({ page }, testInfo) => {
        const priorityLocator = await exercise(page, scenario);
        await expect(priorityLocator).toHaveCount(1);
        await assertResponsiveScenario(page, testInfo, scenario, { profile, priorityLocator });
      });
    }
  });
}
