/**
 * E2E tests for the platform client document portal.
 *
 * Covers three P1 client flows on /platform/documents:
 *   @flow:platform-client-document-portal  — list main contract + annexes, download PDF, empty state
 *   @flow:platform-client-email-validation — request 6-digit OTP, confirm, error path, already-verified
 *   @flow:platform-client-document-sign    — click-to-accept sign, unverified-email gate, already-signed
 *
 * API base is /api/accounts/ (usePlatformApi), so store calls map to `accounts/*` paths.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import {
  PLATFORM_CLIENT_DOCUMENT_PORTAL,
  PLATFORM_CLIENT_EMAIL_VALIDATION,
  PLATFORM_CLIENT_DOCUMENT_SIGN,
} from '../helpers/flow-tags.js';
import { setPlatformAuth, mockPlatformClient } from '../helpers/platform-auth.js';

const MAIN_UUID = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
const ANNEX_UUID = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb';

const json = (body) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

const mainDoc = (overrides = {}) => ({
  uuid: MAIN_UUID,
  title: 'Contrato de Servicios',
  requires_signature: true,
  signed: false,
  signed_at: null,
  ...overrides,
});

const annexDoc = () => ({
  uuid: ANNEX_UUID,
  title: 'Anexo Técnico',
  requires_signature: false,
});

/**
 * @param {object} opts
 * @param {boolean} [opts.emailVerified] initial email-verified state from the documents payload
 * @param {boolean} [opts.mainSigned] whether the main document is already signed
 * @param {boolean} [opts.empty] return no documents (empty-state branch)
 * @param {object}  [opts.confirm] override for the email-confirm response (e.g. { status: 400, detail })
 */
function setupMocks(page, opts = {}) {
  const { emailVerified = true, mainSigned = false, empty = false, confirm } = opts;
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return json(mockPlatformClient);
    if (apiPath === 'accounts/notifications/unread-count/' && method === 'GET') return json({ unread_count: 0 });
    if (apiPath === 'accounts/projects/' && method === 'GET') return json([]);

    if (apiPath === 'accounts/documents/' && method === 'GET') {
      return json({
        documents: empty ? [] : [mainDoc({ signed: mainSigned, signed_at: mainSigned ? '2026-07-04T10:00:00Z' : null }), annexDoc()],
        email: mockPlatformClient.email,
        email_verified: emailVerified,
      });
    }
    if (apiPath === `accounts/documents/${MAIN_UUID}/pdf/` && method === 'GET') {
      return { status: 200, contentType: 'application/pdf', body: '%PDF-1.4 fake-e2e-pdf' };
    }
    if (apiPath === 'accounts/email/verify/request/' && method === 'POST') {
      return json({ detail: 'Te enviamos un código a tu correo.' });
    }
    if (apiPath === 'accounts/email/verify/confirm/' && method === 'POST') {
      if (confirm) return { status: confirm.status, contentType: 'application/json', body: JSON.stringify({ detail: confirm.detail }) };
      return json({ detail: 'Correo validado.' });
    }
    if (apiPath === `accounts/documents/${MAIN_UUID}/sign/` && method === 'POST') {
      return json(mainDoc({ signed: true, signed_at: '2026-07-04T10:00:00Z' }));
    }
    return null;
  });
}

test.describe('Platform Client Document Portal', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
  });

  test('lists the main contract first and its annexes', {
    tag: [...PLATFORM_CLIENT_DOCUMENT_PORTAL, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { emailVerified: true });
    await page.goto('/platform/documents', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Mis documentos' })).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('Documento principal')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Contrato de Servicios' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Anexos' })).toBeVisible();
    await expect(page.getByText('Anexo Técnico')).toBeVisible();
  });

  test('downloads the main document PDF', {
    tag: [...PLATFORM_CLIENT_DOCUMENT_PORTAL, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { emailVerified: true });
    await page.goto('/platform/documents', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Contrato de Servicios' })).toBeVisible({ timeout: 30000 });

    const [pdfResponse] = await Promise.all([
      page.waitForResponse((r) => r.url().includes(`documents/${MAIN_UUID}/pdf/`)),
      page.getByRole('button', { name: 'Descargar PDF' }).click(),
    ]);
    expect(pdfResponse.status()).toBe(200);
  });

  test('shows empty state when the client has no documents', {
    tag: [...PLATFORM_CLIENT_DOCUMENT_PORTAL, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { emailVerified: true, empty: true });
    await page.goto('/platform/documents', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Todavía no tienes documentos disponibles.')).toBeVisible({ timeout: 30000 });
  });
});

test.describe('Platform Client Email Validation', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
  });

  test('sends a code then confirms and shows the validated banner', {
    tag: [...PLATFORM_CLIENT_EMAIL_VALIDATION, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { emailVerified: false });
    await page.goto('/platform/documents', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Valida tu correo electrónico' })).toBeVisible({ timeout: 30000 });

    await page.getByRole('button', { name: 'Enviar código' }).click();
    await page.getByPlaceholder('Código de 6 dígitos').fill('123456');
    await page.getByRole('button', { name: 'Validar correo' }).click();

    await expect(page.getByText('Tu correo está validado. Ya puedes firmar tus documentos.')).toBeVisible();
  });

  test('shows an error when the code is invalid', {
    tag: [...PLATFORM_CLIENT_EMAIL_VALIDATION, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, {
      emailVerified: false,
      confirm: { status: 400, detail: 'El código ingresado no es válido.' },
    });
    await page.goto('/platform/documents', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Valida tu correo electrónico' })).toBeVisible({ timeout: 30000 });
    await page.getByRole('button', { name: 'Enviar código' }).click();
    await page.getByPlaceholder('Código de 6 dígitos').fill('000000');
    await page.getByRole('button', { name: 'Validar correo' }).click();

    await expect(page.getByText('El código ingresado no es válido.')).toBeVisible();
  });

  test('shows the validated banner and no card when email is already verified', {
    tag: [...PLATFORM_CLIENT_EMAIL_VALIDATION, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { emailVerified: true });
    await page.goto('/platform/documents', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Tu correo está validado. Ya puedes firmar tus documentos.')).toBeVisible({ timeout: 30000 });
    await expect(page.getByRole('heading', { name: 'Valida tu correo electrónico' })).not.toBeVisible();
  });
});

test.describe('Platform Client Document Sign', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
  });

  test('signs the main document via the confirmation modal', {
    tag: [...PLATFORM_CLIENT_DOCUMENT_SIGN, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { emailVerified: true, mainSigned: false });
    await page.goto('/platform/documents', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Contrato de Servicios' })).toBeVisible({ timeout: 30000 });

    await page.getByRole('button', { name: 'Aceptar y firmar' }).click();
    await expect(page.getByRole('heading', { name: 'Firmar documento' })).toBeVisible();

    await page.getByRole('checkbox').check();
    await Promise.all([
      page.waitForResponse((r) => r.url().includes(`documents/${MAIN_UUID}/sign/`)),
      page.getByRole('button', { name: 'Confirmar firma' }).click(),
    ]);

    await expect(page.getByText(/Firmado el/)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Aceptar y firmar' })).not.toBeVisible();
  });

  test('sign button is disabled until the email is verified', {
    tag: [...PLATFORM_CLIENT_DOCUMENT_SIGN, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { emailVerified: false, mainSigned: false });
    await page.goto('/platform/documents', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Contrato de Servicios' })).toBeVisible({ timeout: 30000 });

    await expect(page.getByRole('button', { name: 'Aceptar y firmar' })).toBeDisabled();
  });

  test('already-signed document shows the signed state and hides the sign button', {
    tag: [...PLATFORM_CLIENT_DOCUMENT_SIGN, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { emailVerified: true, mainSigned: true });
    await page.goto('/platform/documents', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Contrato de Servicios' })).toBeVisible({ timeout: 30000 });

    await expect(page.getByText(/Firmado el/)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Aceptar y firmar' })).not.toBeVisible();
  });
});
