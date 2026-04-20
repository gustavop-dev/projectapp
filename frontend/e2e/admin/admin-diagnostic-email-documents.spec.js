/**
 * E2E tests for admin Web App Diagnostics — Correos tab (email composer)
 * and Documentos tab (attachment management).
 *
 * Covers: email tab renders composer + history; documents tab renders upload
 * form and send-to-client button behaviour.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_DIAGNOSTIC_EMAIL,
  ADMIN_DIAGNOSTIC_DOCUMENTS,
} from '../helpers/flow-tags.js';

const DIAG_ID = 11;

const authOk = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const emailDefaults = {
  recipient_email: 'client@example.com',
  subject: 'TechCorp, seguimiento de tu diagnóstico — Project App',
  greeting: 'Hola TechCorp',
  sections: [''],
  footer: 'Quedamos atentos a tus comentarios.',
};

const emptyHistory = { results: [], total: 0, page: 1, has_next: false };

function buildDiagnostic(overrides = {}) {
  return {
    id: DIAG_ID,
    uuid: 'diag-email-test-uuid-1234',
    title: 'Diagnóstico — TechCorp',
    status: 'draft',
    language: 'es',
    client: { name: 'TechCorp', email: 'client@example.com' },
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
    public_url: `/diagnostic/diag-email-test-uuid-1234`,
    ...overrides,
  };
}

function baseHandler(diagnostic, extra = {}) {
  return async ({ apiPath, method }) => {
    if (apiPath === 'auth/check/') return authOk;
    if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(diagnostic) };
    }
    if (apiPath === `diagnostics/${DIAG_ID}/email/defaults/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(emailDefaults) };
    }
    if (apiPath === `diagnostics/${DIAG_ID}/email/history/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(emptyHistory) };
    }
    if (apiPath === `diagnostics/${DIAG_ID}/attachments/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    for (const [path, response] of Object.entries(extra)) {
      if (apiPath === path && (!response.method || response.method === method)) {
        return response;
      }
    }
    return null;
  };
}

// ── Email composer tab ────────────────────────────────────────────────────────

test.describe('Admin Diagnostic — Correos tab', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 9100, role: 'admin', is_staff: true },
    });
  });

  test('Correos tab is visible on the edit page', {
    tag: [...ADMIN_DIAGNOSTIC_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(buildDiagnostic()));
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await expect(page.getByRole('button', { name: 'Correos' })).toBeVisible({ timeout: 15000 });
  });

  test('email composer renders recipient, subject, and sections fields', {
    tag: [...ADMIN_DIAGNOSTIC_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(buildDiagnostic()));
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);

    await page.getByRole('button', { name: 'Correos' }).click();

    await expect(page.locator('input[type="email"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('input[placeholder*="Asunto"]')).toBeVisible();
    await expect(page.getByText('Secciones del correo')).toBeVisible();
    await expect(page.getByText('Agregar sección')).toBeVisible();
  });

  test('email defaults populate recipient and subject on mount', {
    tag: [...ADMIN_DIAGNOSTIC_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(buildDiagnostic()));
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);

    await page.getByRole('button', { name: 'Correos' }).click();

    const recipientInput = page.locator('input[type="email"]');
    await expect(recipientInput).toHaveValue('client@example.com', { timeout: 10000 });
  });

  test('email history section renders after tab loads', {
    tag: [...ADMIN_DIAGNOSTIC_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(buildDiagnostic()));
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);

    await page.getByRole('button', { name: 'Correos' }).click();

    await expect(page.getByText('Historial de correos')).toBeVisible({ timeout: 10000 });
  });

  test('send button is disabled when sections textarea is empty', {
    tag: [...ADMIN_DIAGNOSTIC_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(buildDiagnostic()));
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);

    await page.getByRole('button', { name: 'Correos' }).click();

    await expect(page.getByRole('button', { name: /Enviar correo/i })).toBeDisabled({ timeout: 10000 });
  });

  test('POST to email/send/ is called when form is filled and send is clicked', {
    tag: [...ADMIN_DIAGNOSTIC_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    let sendCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      const base = await baseHandler(buildDiagnostic())({ apiPath, method });
      if (base) return base;
      if (apiPath === `diagnostics/${DIAG_ID}/email/send/` && method === 'POST') {
        sendCalled = true;
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ message: 'sent' }) };
      }
      return null;
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('button', { name: 'Correos' }).click();

    await page.locator('textarea').first().fill('Este es el cuerpo del correo de seguimiento.');
    await page.getByRole('button', { name: /Enviar correo/i }).click();

    await expect(() => expect(sendCalled).toBe(true)).toPass({ timeout: 5000 });
  });

  test('NDA checkbox is visible in the email composer', {
    tag: [...ADMIN_DIAGNOSTIC_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(buildDiagnostic({ status: 'sent' })));
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);

    await page.getByRole('button', { name: 'Correos' }).click();

    await expect(
      page.getByLabel(/Adjuntar acuerdo de confidencialidad/i),
    ).toBeVisible({ timeout: 10000 });
  });

  test('checking NDA checkbox includes attach_confidentiality in the POST body', {
    tag: [...ADMIN_DIAGNOSTIC_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    let capturedBody = '';
    await mockApi(page, async ({ apiPath, method, route }) => {
      const base = await baseHandler(buildDiagnostic({ status: 'sent' }))({ apiPath, method });
      if (base) return base;
      if (apiPath === `diagnostics/${DIAG_ID}/email/send/` && method === 'POST') {
        capturedBody = route.request().postData() || '';
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ message: 'sent' }) };
      }
      return null;
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('button', { name: 'Correos' }).click();

    await page.locator('textarea').first().fill('Contenido del correo de seguimiento.');
    await page.getByLabel(/Adjuntar acuerdo de confidencialidad/i).check();
    await page.getByRole('button', { name: /Enviar correo/i }).click();

    await expect(() => expect(capturedBody).toContain('attach_confidentiality')).toPass({ timeout: 5000 });
  });
});

// ── Documents tab ─────────────────────────────────────────────────────────────

test.describe('Admin Diagnostic — Documentos tab', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 9100, role: 'admin', is_staff: true },
    });
  });

  test('Documentos tab is visible on the edit page', {
    tag: [...ADMIN_DIAGNOSTIC_DOCUMENTS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(buildDiagnostic()));
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await expect(page.getByRole('button', { name: 'Documentos' })).toBeVisible({ timeout: 15000 });
  });

  test('documents tab renders upload form and send-to-client section', {
    tag: [...ADMIN_DIAGNOSTIC_DOCUMENTS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(buildDiagnostic()));
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);

    await page.getByRole('button', { name: 'Documentos' }).click();

    await expect(page.getByText('Enviar documentos al cliente')).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('heading', { name: 'Documentos adjuntos' })).toBeVisible();
  });

  test('send-to-client button is disabled when no attachments are selected', {
    tag: [...ADMIN_DIAGNOSTIC_DOCUMENTS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler(buildDiagnostic()));
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);

    await page.getByRole('button', { name: 'Documentos' }).click();

    await expect(page.getByRole('button', { name: /Enviar al cliente/i })).toBeDisabled({ timeout: 10000 });
  });

  test('attachment checkbox enables send-to-client button when checked', {
    tag: [...ADMIN_DIAGNOSTIC_DOCUMENTS, '@role:admin'],
  }, async ({ page }) => {
    const att = {
      id: 1,
      title: 'Anexo técnico',
      document_type: 'legal_annex',
      document_type_display: 'Anexo legal',
      file_url: '/media/test.pdf',
      created_at: '2026-04-16T10:00:00Z',
    };
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
        return {
          status: 200, contentType: 'application/json',
          body: JSON.stringify(buildDiagnostic({ attachments: [att] })),
        };
      }
      if (apiPath === `diagnostics/${DIAG_ID}/attachments/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([att]) };
      }
      return null;
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('button', { name: 'Documentos' }).click();

    await page.getByRole('checkbox').first().check();

    await expect(page.getByRole('button', { name: /Enviar al cliente/i })).toBeEnabled({ timeout: 10000 });
  });

  test('selecting NDA checkbox sends documents:["confidentiality_agreement"] in the POST body', {
    tag: [...ADMIN_DIAGNOSTIC_DOCUMENTS, '@role:admin'],
  }, async ({ page }) => {
    const ndaAtt = {
      id: 42,
      title: 'Acuerdo de Confidencialidad',
      document_type: 'confidentiality_agreement',
      document_type_display: 'Acuerdo de Confidencialidad',
      file: '/media/nda.pdf',
      file_url: '/media/nda.pdf',
      is_generated: true,
      created_at: '2026-04-16T10:00:00Z',
    };
    let sendBody = null;
    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
        return {
          status: 200, contentType: 'application/json',
          body: JSON.stringify(buildDiagnostic({ status: 'negotiating', attachments: [ndaAtt] })),
        };
      }
      if (apiPath === `diagnostics/${DIAG_ID}/attachments/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([ndaAtt]) };
      }
      if (apiPath === `diagnostics/${DIAG_ID}/attachments/send/` && method === 'POST') {
        sendBody = route.request().postDataJSON();
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ message: 'sent' }) };
      }
      return null;
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('button', { name: 'Documentos' }).click();

    await page.getByRole('checkbox', { name: /Acuerdo de Confidencialidad/i }).check();
    await page.getByRole('button', { name: /Enviar al cliente/i }).click();

    await page.getByRole('button', { name: /Enviar documentos/i }).click();

    await expect(() => expect(sendBody).not.toBeNull()).toPass({ timeout: 5000 });
    expect(sendBody.documents).toContain('confidentiality_agreement');
    expect(sendBody.attachment_ids).toEqual([]);
  });
});
