/**
 * E2E tests for admin portfolio work creation.
 *
 * Covers: Manual mode (form render, fill and submit), JSON import mode
 * (tab switch, template download button, paste valid JSON, paste invalid JSON, submit).
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PORTFOLIO_CREATE } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
const createdWork = { id: 10, title_es: 'Nuevo Proyecto', title_en: 'New Project', slug: 'nuevo-proyecto', is_published: false };
const jsonTemplate = {
  title_es: 'Plantilla', title_en: 'Template',
  project_url: 'https://example.com',
  content_json_es: { problem: { title: 'P', description: 'D' }, solution: { title: 'S', description: 'D' }, results: { title: 'R', description: 'D' } },
};

function setupMock(page) {
  return mockApi(page, async ({ apiPath, route }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'portfolio/admin/create/' && route.request().method() === 'POST') {
      return { status: 201, contentType: 'application/json', body: JSON.stringify(createdWork) };
    }
    if (apiPath === 'portfolio/admin/create-from-json/' && route.request().method() === 'POST') {
      return { status: 201, contentType: 'application/json', body: JSON.stringify(createdWork) };
    }
    if (apiPath === 'portfolio/admin/json-template/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(jsonTemplate) };
    }
    return null;
  });
}

test.describe('Admin Portfolio Create', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 9300, role: 'admin', is_staff: true } });
  });

  test('renders form with Manual/JSON tabs', {
    tag: [...ADMIN_PORTFOLIO_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/portfolio/create');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('button', { name: 'Manual' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Importar JSON' })).toBeVisible();
    await expect(page.locator('legend').filter({ hasText: 'Español' })).toBeVisible();
    await expect(page.locator('legend').filter({ hasText: 'English' })).toBeVisible();
  });

  test('manual mode: fills fields and submits successfully', {
    tag: [...ADMIN_PORTFOLIO_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/portfolio/create');
    await page.waitForLoadState('networkidle');

    await page.getByPlaceholder('Título del proyecto en español').fill('Proyecto E2E');
    await page.getByPlaceholder('Project title in English').fill('E2E Project');
    await page.getByPlaceholder('https://example.com').fill('https://e2e-project.com');

    await page.getByRole('button', { name: 'Crear Proyecto' }).click();
    await page.waitForLoadState('networkidle');
  });

  test('switches to JSON import tab and shows template download', {
    tag: [...ADMIN_PORTFOLIO_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/portfolio/create');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: 'Importar JSON' }).click();

    await expect(page.getByText('Plantilla JSON')).toBeVisible();
    await expect(page.getByText('Pegar o subir JSON')).toBeVisible();
    await expect(page.getByRole('button', { name: /Descargar Plantilla/ })).toBeVisible();
  });

  test('JSON mode: paste valid JSON shows preview and submit button', {
    tag: [...ADMIN_PORTFOLIO_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/portfolio/create');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: 'Importar JSON' }).click();

    const validJson = JSON.stringify({
      title_es: 'Proyecto JSON',
      title_en: 'JSON Project',
      project_url: 'https://json-project.com',
      content_json_es: { problem: { title: 'P', description: 'D' } },
    });
    const jsonTextarea = page.getByPlaceholder(/title_es/);
    await jsonTextarea.fill(validJson);
    await jsonTextarea.dispatchEvent('input');

    await expect(page.getByText('Proyecto JSON')).toBeVisible();
    await expect(page.getByRole('button', { name: /Crear desde JSON/ })).toBeVisible();
  });

  test('JSON mode: paste invalid JSON shows error', {
    tag: [...ADMIN_PORTFOLIO_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/portfolio/create');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: 'Importar JSON' }).click();
    const jsonTextarea = page.getByPlaceholder(/title_es/);
    await jsonTextarea.fill('{ invalid json }');
    await jsonTextarea.dispatchEvent('input');

    await expect(page.getByText('JSON inválido')).toBeVisible();
  });
});
