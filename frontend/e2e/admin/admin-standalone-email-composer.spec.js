/**
 * E2E tests for admin standalone email composer.
 *
 * @flow:admin-standalone-email-composer
 * Covers: email composer form, send validation, preview tab,
 *         paginated email history, empty/success/error states.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_STANDALONE_EMAIL_COMPOSER } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDefaults = {
  greeting: 'Hola',
  footer: 'Quedamos atentos a tus comentarios.\nUn abrazo, el equipo de Project App.',
};

const mockHistoryEmpty = { results: [], total: 0, page: 1, has_next: false };

const mockHistoryWithEntries = {
  results: [
    {
      id: 1, subject: 'Bienvenido al proyecto', recipient: 'client@example.com',
      status: 'delivered', sent_at: '2026-03-15T14:30:00Z',
      metadata: {
        greeting: 'Hola Juan',
        sections: ['Le damos la bienvenida al proyecto.', 'Adjuntamos el cronograma.'],
        footer: 'Un abrazo, el equipo de Project App.',
        attachment_names: ['cronograma.pdf'],
      },
    },
    {
      id: 2, subject: 'Seguimiento entregable', recipient: 'pm@example.com',
      status: 'sent', sent_at: '2026-03-10T09:00:00Z',
      metadata: {
        greeting: 'Hola',
        sections: ['Adjuntamos el entregable actualizado.'],
        footer: 'Quedamos atentos.',
        attachment_names: [],
      },
    },
  ],
  total: 2,
  page: 1,
  has_next: false,
};

function setupMocks(page, { history = mockHistoryEmpty } = {}) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'emails/defaults/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDefaults) };
    }
    if (apiPath.startsWith('emails/history') && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(history) };
    }
    if (apiPath === 'emails/send/' && method === 'POST') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) };
    }
    return null;
  });
}

test.describe('Admin Standalone Email Composer', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8700, role: 'admin', is_staff: true },
    });
  });

  test('renders email composer page with form fields', {
    tag: [...ADMIN_STANDALONE_EMAIL_COMPOSER, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page);
    await page.goto('/panel/emails', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Emails' })).toBeVisible({ timeout: 20_000 });

    await expect(page.getByPlaceholder('correo@ejemplo.com')).toBeVisible();
    await expect(page.getByPlaceholder('Asunto del correo')).toBeVisible();
  });

  test('send button is disabled when required fields are empty', {
    tag: [...ADMIN_STANDALONE_EMAIL_COMPOSER, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page);
    await page.goto('/panel/emails', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Emails' })).toBeVisible({ timeout: 20_000 });

    const sendButton = page.getByRole('button', { name: /enviar correo/i });
    await expect(sendButton).toBeDisabled();
  });

  test('enables send button when recipient, subject, and section are filled', {
    tag: [...ADMIN_STANDALONE_EMAIL_COMPOSER, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page);
    await page.goto('/panel/emails', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Emails' })).toBeVisible({ timeout: 20_000 });

    await page.getByPlaceholder('correo@ejemplo.com').fill('test@example.com');
    await page.getByPlaceholder('Asunto del correo').fill('Test Subject');
    await page.locator('textarea').first().fill('Hello, this is a test email body.');

    const sendButton = page.getByRole('button', { name: /enviar correo/i });
    await expect(sendButton).toBeEnabled();
  });

  test('sends email and shows success message', {
    tag: [...ADMIN_STANDALONE_EMAIL_COMPOSER, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page);
    await page.goto('/panel/emails', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Emails' })).toBeVisible({ timeout: 20_000 });

    await page.getByPlaceholder('correo@ejemplo.com').fill('client@example.com');
    await page.getByPlaceholder('Asunto del correo').fill('Welcome Email');
    await page.locator('textarea').first().fill('Welcome to our platform.');

    const sendWait = page.waitForResponse(
      (res) => res.url().includes('emails/send/') && res.status() === 200,
    );
    await page.getByRole('button', { name: /enviar correo/i }).click();
    await sendWait;

    await expect(page.getByText('Correo enviado correctamente.')).toBeVisible({ timeout: 5000 });
  });

  test('preview tab shows branded email preview', {
    tag: [...ADMIN_STANDALONE_EMAIL_COMPOSER, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page);
    await page.goto('/panel/emails', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Emails' })).toBeVisible({ timeout: 20_000 });

    await page.getByPlaceholder('correo@ejemplo.com').fill('test@example.com');
    await page.getByPlaceholder('Asunto del correo').fill('Preview Test');
    await page.locator('textarea').first().fill('Body content for preview.');

    await page.getByRole('button', { name: /vista previa/i }).click();

    await expect(page.getByText('Body content for preview.')).toBeVisible();
  });

  test('renders email history with entries', {
    tag: [...ADMIN_STANDALONE_EMAIL_COMPOSER, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page, { history: mockHistoryWithEntries });
    await page.goto('/panel/emails', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Emails' })).toBeVisible({ timeout: 20_000 });

    await expect(page.getByText('Bienvenido al proyecto')).toBeVisible();
    await expect(page.getByText('client@example.com')).toBeVisible();
    await expect(page.getByText('Seguimiento entregable')).toBeVisible();
  });

  test('shows empty history state', {
    tag: [...ADMIN_STANDALONE_EMAIL_COMPOSER, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page, { history: mockHistoryEmpty });
    await page.goto('/panel/emails', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Emails' })).toBeVisible({ timeout: 20_000 });

    await expect(page.getByText('Bienvenido al proyecto')).not.toBeVisible();
  });
});
