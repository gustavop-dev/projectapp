/**
 * E2E tests for JSON import warnings displayed in the post-creation modal
 * when the imported JSON contains unmapped section keys.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_JSON_IMPORT_WARNINGS } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockCreatedWithWarnings = {
  id: 77,
  uuid: '77777777-7777-7777-7777-777777777777',
  title: 'Propuesta con Warnings',
  client_name: 'Ana Test',
  status: 'draft',
  sections: [],
  requirement_groups: [],
  warnings: [
    'Sección "customSection" no tiene mapping conocido y fue ignorada.',
    'Sección "legacyField" no tiene mapping conocido y fue ignorada.',
  ],
};

const validJson = JSON.stringify({
  general: { clientName: 'Ana Test' },
  executiveSummary: { paragraphs: ['Resumen.'] },
  customSection: { data: 'unmapped' },
  legacyField: { data: 'unmapped' },
});

test.describe('Admin Proposal JSON Import Warnings', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8500, role: 'admin', is_staff: true },
    });
  });

  test('post-creation modal shows warnings for unmapped JSON keys', {
    tag: [...ADMIN_PROPOSAL_JSON_IMPORT_WARNINGS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'proposals/create-from-json/') {
        return { status: 201, contentType: 'application/json', body: JSON.stringify(mockCreatedWithWarnings) };
      }
      return null;
    });

    await page.goto('/panel/proposals/create');

    await page.getByRole('button', { name: 'Importar JSON' }).click();
    const textarea = page.getByPlaceholder(/general/);
    await textarea.fill(validJson);
    await textarea.dispatchEvent('input');

    await expect(page.getByText('Ana Test')).toBeVisible();

    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().includes('proposals/create-from-json/')),
      page.getByRole('button', { name: /Crear desde JSON/i }).click(),
    ]);
    await response.finished();

    await expect(page.getByText('Propuesta creada')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/Advertencias del JSON/i)).toBeVisible();
    await expect(page.getByText(/customSection/)).toBeVisible();
    await expect(page.getByText(/legacyField/)).toBeVisible();
  });

  test('post-creation modal hides warnings section when no warnings exist', {
    tag: [...ADMIN_PROPOSAL_JSON_IMPORT_WARNINGS, '@role:admin'],
  }, async ({ page }) => {
    const mockClean = { ...mockCreatedWithWarnings, warnings: [] };

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'proposals/create-from-json/') {
        return { status: 201, contentType: 'application/json', body: JSON.stringify(mockClean) };
      }
      return null;
    });

    await page.goto('/panel/proposals/create');

    await page.getByRole('button', { name: 'Importar JSON' }).click();
    const textarea = page.getByPlaceholder(/general/);
    await textarea.fill(JSON.stringify({ general: { clientName: 'Ana Test' }, executiveSummary: { paragraphs: ['OK'] } }));
    await textarea.dispatchEvent('input');

    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().includes('proposals/create-from-json/')),
      page.getByRole('button', { name: /Crear desde JSON/i }).click(),
    ]);
    await response.finished();

    await expect(page.getByText('Propuesta creada')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/Advertencias del JSON/i)).not.toBeVisible();
  });
});
