/**
 * E2E tests for the public-facing Web App Diagnostic view.
 *
 * Covers: INITIAL_SENT shows 1 document, FINAL_SENT shows 3 document tabs,
 * and responding with 'accept' posts to the respond endpoint.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { DIAGNOSTIC_PUBLIC_VIEW } from '../helpers/flow-tags.js';

const TEST_UUID = 'aaaa-1111-bbbb-2222';

function buildDoc(overrides = {}) {
  return {
    id: overrides.id || 1,
    doc_type: 'initial_proposal',
    title: 'Propuesta de Diagnóstico',
    rendered_md: '## Índice\n\nContenido de prueba.',
    is_ready: true,
    order: overrides.order || 1,
    ...overrides,
  };
}

function buildPublicDiagnostic(overrides = {}) {
  return {
    uuid: TEST_UUID,
    client_name: 'TechCorp',
    status: 'initial_sent',
    documents: [buildDoc()],
    ...overrides,
  };
}

test.describe('Diagnostic Public View', () => {
  test.setTimeout(60_000);

  test('INITIAL_SENT state shows only one document — no tab nav rendered', {
    tag: [...DIAGNOSTIC_PUBLIC_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const diagnostic = buildPublicDiagnostic({ status: 'initial_sent', documents: [buildDoc()] });

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `diagnostics/public/${TEST_UUID}/`) {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(diagnostic),
        };
      }
      if (apiPath === `diagnostics/public/${TEST_UUID}/track/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({}) };
      }
      return null;
    });

    await page.goto(`/diagnostic/${TEST_UUID}`);
    await expect(page.getByText('TechCorp')).toBeVisible({ timeout: 15000 });
    // Single doc: no tab navigation buttons rendered (nav only appears when docs.length > 1)
    await expect(page.getByRole('button', { name: 'Propuesta de Diagnóstico' })).not.toBeVisible();
  });

  test('FINAL_SENT state with 3 documents shows tab navigation', {
    tag: [...DIAGNOSTIC_PUBLIC_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const diagnostic = buildPublicDiagnostic({
      status: 'final_sent',
      documents: [
        buildDoc({ id: 1, title: 'Propuesta de Diagnóstico', order: 1 }),
        buildDoc({ id: 2, doc_type: 'technical_proposal', title: 'Propuesta Técnica', order: 2 }),
        buildDoc({ id: 3, doc_type: 'sizing_annex', title: 'Anexo de Dimensionamiento', order: 3 }),
      ],
    });

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `diagnostics/public/${TEST_UUID}/`) {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(diagnostic),
        };
      }
      if (apiPath === `diagnostics/public/${TEST_UUID}/track/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({}) };
      }
      return null;
    });

    await page.goto(`/diagnostic/${TEST_UUID}`);
    await expect(page.getByText('TechCorp')).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('button', { name: 'Propuesta de Diagnóstico' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Propuesta Técnica' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Anexo de Dimensionamiento' })).toBeVisible();
  });

  test('clicking "Aceptar propuesta" POSTs accept decision and shows acceptance footer', {
    tag: [...DIAGNOSTIC_PUBLIC_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const diagnostic = buildPublicDiagnostic({ status: 'final_sent', documents: [buildDoc()] });
    let respondCalled = false;

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === `diagnostics/public/${TEST_UUID}/`) {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(diagnostic),
        };
      }
      if (apiPath === `diagnostics/public/${TEST_UUID}/track/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({}) };
      }
      if (apiPath === `diagnostics/public/${TEST_UUID}/respond/` && method === 'POST') {
        respondCalled = true;
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...diagnostic, status: 'accepted' }),
        };
      }
      return null;
    });

    await page.goto(`/diagnostic/${TEST_UUID}`);
    await expect(page.getByRole('button', { name: /aceptar propuesta/i })).toBeVisible({ timeout: 15000 });
    await page.getByRole('button', { name: /aceptar propuesta/i }).click();

    await expect(() => expect(respondCalled).toBe(true)).toPass({ timeout: 5000 });
    await expect(page.getByText(/confirmamos tu aceptación/i)).toBeVisible({ timeout: 5000 });
  });
});
