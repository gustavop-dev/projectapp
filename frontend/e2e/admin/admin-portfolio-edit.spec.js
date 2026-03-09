/**
 * E2E tests for admin portfolio work editing.
 *
 * Covers: load existing work with all fields, edit title and save,
 * SEO section shows meta fields, view-in-public link, content_json populated.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PORTFOLIO_EDIT } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const existingWork = {
  id: 1,
  title_es: 'Proyecto Existente',
  title_en: 'Existing Project',
  slug: 'proyecto-existente',
  excerpt_es: 'Tagline ES.',
  excerpt_en: 'Tagline EN.',
  project_url: 'https://existing-project.com',
  cover_image_url: '',
  cover_image_display: '',
  content_json_es: { problem: { title: 'El Desafío', description: 'Descripción del problema.' } },
  content_json_en: {},
  order: 1,
  is_published: true,
  meta_title_es: 'SEO Título ES',
  meta_title_en: 'SEO Title EN',
  meta_description_es: 'Meta desc ES.',
  meta_description_en: 'Meta desc EN.',
  meta_keywords_es: 'keyword1, keyword2',
  meta_keywords_en: 'keyword1, keyword2',
  published_at: '2026-03-01T12:00:00Z',
  created_at: '2026-03-01T10:00:00Z',
};

const updatedWork = { ...existingWork, title_es: 'Proyecto Actualizado' };

function setupMock(page) {
  return mockApi(page, async ({ apiPath, route }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'portfolio/admin/1/detail/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(existingWork) };
    }
    if (apiPath === 'portfolio/admin/1/update/' && route.request().method() === 'PATCH') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(updatedWork) };
    }
    return null;
  });
}

test.describe('Admin Portfolio Edit', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 9400, role: 'admin', is_staff: true } });
  });

  test('loads existing work and populates all fields', {
    tag: [...ADMIN_PORTFOLIO_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/portfolio/1/edit');
    await page.waitForLoadState('networkidle');

    const esGroup = page.getByRole('group', { name: 'Español' });
    await expect(esGroup.locator('label:has-text("Título (ES)")').locator('..').locator('input')).toHaveValue('Proyecto Existente');
    await expect(esGroup.locator('label:has-text("Tagline (ES)")').locator('..').locator('input')).toHaveValue('Tagline ES.');

    const enGroup = page.getByRole('group', { name: 'English' });
    await expect(enGroup.locator('label:has-text("Title (EN)")').locator('..').locator('input')).toHaveValue('Existing Project');

    await expect(page.locator('label:has-text("Slug")').locator('..').locator('input')).toHaveValue('proyecto-existente');
  });

  test('edits title and saves successfully', {
    tag: [...ADMIN_PORTFOLIO_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/portfolio/1/edit');
    await page.waitForLoadState('networkidle');

    const esGroup = page.getByRole('group', { name: 'Español' });
    await esGroup.locator('label:has-text("Título (ES)")').locator('..').locator('input').fill('Proyecto Actualizado');
    await page.getByRole('button', { name: /Guardar cambios/ }).click();

    await expect(page.getByText('Proyecto guardado correctamente')).toBeVisible();
  });

  test('SEO section shows meta fields', {
    tag: [...ADMIN_PORTFOLIO_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/portfolio/1/edit');
    await page.waitForLoadState('networkidle');

    const seoGroup = page.getByRole('group', { name: 'SEO' });
    await expect(seoGroup.locator('label:has-text("Meta título (ES)")').locator('..').locator('input')).toHaveValue('SEO Título ES');
    await expect(seoGroup.locator('label:has-text("Meta title (EN)")').locator('..').locator('input')).toHaveValue('SEO Title EN');
  });

  test('view-in-public link has correct href', {
    tag: [...ADMIN_PORTFOLIO_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/portfolio/1/edit');
    await page.waitForLoadState('networkidle');

    const link = page.getByText('Ver en público');
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute('href', '/portfolio-works/proyecto-existente');
  });

  test('shows content_json_es populated in textarea', {
    tag: [...ADMIN_PORTFOLIO_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/portfolio/1/edit');
    await page.waitForLoadState('networkidle');

    const jsonTextarea = page.getByRole('group', { name: 'Español' }).getByPlaceholder('"problem"');
    await expect(jsonTextarea).toBeVisible();
    const value = await jsonTextarea.inputValue();
    expect(value).toContain('El Desafío');
  });
});
