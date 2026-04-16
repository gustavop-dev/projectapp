/**
 * E2E tests for admin Web App Diagnostics — send initial and send final flows.
 *
 * Covers: edit page renders 4 tabs; status-conditional action buttons
 * trigger the correct API transition endpoints.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DIAGNOSTIC_SEND_INITIAL, ADMIN_DIAGNOSTIC_SEND_FINAL } from '../helpers/flow-tags.js';

const authOk = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function buildMockDiagnostic(overrides = {}) {
  return {
    id: 7,
    uuid: '7777-8888-9999-aaaa',
    title: 'Diagnóstico — TechCorp',
    status: 'draft',
    language: 'es',
    client: { name: 'TechCorp', email: 'tech@corp.com' },
    client_name: 'TechCorp',
    investment_amount: null,
    currency: 'COP',
    payment_terms: {},
    duration_label: '',
    size_category: '',
    radiography: {},
    view_count: 0,
    last_viewed_at: null,
    documents: [],
    attachments: [],
    public_url: '/diagnostic/7777-8888-9999-aaaa',
    ...overrides,
  };
}

function buildHandler(diagnostic, overrides = {}) {
  return async ({ apiPath, method }) => {
    if (apiPath === 'auth/check/') return authOk;
    if (apiPath === `diagnostics/${diagnostic.id}/detail/`) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(diagnostic),
      };
    }
    for (const [path, response] of Object.entries(overrides)) {
      if (apiPath === path && (!response.method || response.method === method)) {
        return response;
      }
    }
    return null;
  };
}

test.describe('Admin Diagnostic — Send Flows', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('edit page renders all 6 navigation tabs', {
    tag: [...ADMIN_DIAGNOSTIC_SEND_INITIAL, '@role:admin'],
  }, async ({ page }) => {
    const diagnostic = buildMockDiagnostic();
    await mockApi(page, buildHandler(diagnostic));

    await page.goto('/panel/diagnostics/7/edit');
    await expect(page.getByRole('button', { name: 'Resumen' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('button', { name: 'Pricing' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Radiografía' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Plantillas' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Correos' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Documentos' })).toBeVisible();
  });

  test('"Enviar Doc 1 al cliente" button POSTs to send-initial/ in DRAFT state', {
    tag: [...ADMIN_DIAGNOSTIC_SEND_INITIAL, '@role:admin'],
  }, async ({ page }) => {
    const diagnostic = buildMockDiagnostic({ status: 'draft' });
    let sendCalled = false;

    await mockApi(page, buildHandler(diagnostic, {
      'diagnostics/7/send-initial/': {
        method: 'POST',
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(buildMockDiagnostic({ status: 'sent' })),
        _handler: () => { sendCalled = true; },
      },
    }));

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === 'diagnostics/7/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(diagnostic) };
      }
      if (apiPath === 'diagnostics/7/send-initial/' && method === 'POST') {
        sendCalled = true;
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(buildMockDiagnostic({ status: 'sent' })),
        };
      }
      return null;
    });

    await page.goto('/panel/diagnostics/7/edit');
    await expect(page.getByRole('button', { name: /enviar doc 1/i })).toBeVisible({ timeout: 15000 });
    await page.getByRole('button', { name: /enviar doc 1/i }).click();
    await page.getByRole('button', { name: 'Enviar', exact: true }).click();

    await expect(() => expect(sendCalled).toBe(true)).toPass({ timeout: 5000 });
  });

  test('"Marcar en análisis" button POSTs to mark-in-analysis/ when initial has been sent', {
    tag: [...ADMIN_DIAGNOSTIC_SEND_INITIAL, '@role:admin'],
  }, async ({ page }) => {
    const diagnostic = buildMockDiagnostic({
      status: 'sent',
      initial_sent_at: '2026-04-16T10:00:00Z',
      final_sent_at: null,
    });
    let called = false;

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === 'diagnostics/7/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(diagnostic) };
      }
      if (apiPath === 'diagnostics/7/mark-in-analysis/' && method === 'POST') {
        called = true;
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(buildMockDiagnostic({ status: 'negotiating' })),
        };
      }
      return null;
    });

    await page.goto('/panel/diagnostics/7/edit');
    await expect(page.getByRole('button', { name: /marcar en análisis/i })).toBeVisible({ timeout: 15000 });
    await page.getByRole('button', { name: /marcar en análisis/i }).click();
    await page.getByRole('button', { name: 'Confirmar', exact: true }).click();

    await expect(() => expect(called).toBe(true)).toPass({ timeout: 5000 });
  });

  test('"Enviar diagnóstico final" button POSTs to send-final/ in NEGOTIATING state', {
    tag: [...ADMIN_DIAGNOSTIC_SEND_FINAL, '@role:admin'],
  }, async ({ page }) => {
    const diagnostic = buildMockDiagnostic({ status: 'negotiating' });
    let called = false;

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === 'diagnostics/7/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(diagnostic) };
      }
      if (apiPath === 'diagnostics/7/send-final/' && method === 'POST') {
        called = true;
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(buildMockDiagnostic({
            status: 'sent', final_sent_at: '2026-04-16T10:00:00Z',
          })),
        };
      }
      return null;
    });

    await page.goto('/panel/diagnostics/7/edit');
    await expect(page.getByRole('button', { name: /enviar diagnóstico final/i })).toBeVisible({ timeout: 15000 });
    await page.getByRole('button', { name: /enviar diagnóstico final/i }).click();
    await page.getByRole('button', { name: 'Enviar', exact: true }).click();

    await expect(() => expect(called).toBe(true)).toPass({ timeout: 5000 });
  });
});
