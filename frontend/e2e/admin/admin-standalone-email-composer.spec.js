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
import { ADMIN_STANDALONE_EMAIL_COMPOSER, ADMIN_STANDALONE_EMAIL_DEFAULTS } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDefaults = {
  greeting: 'Hola',
  footer: 'Quedamos atentos a tus comentarios.\nUn abrazo, el equipo de Project App.',
  config: {
    greeting: 'Hola {client_name}',
    footer: 'Quedamos atentos a tus comentarios.\nUn abrazo, el equipo de Project App.',
    signer: 'vanessa',
  },
  defaults: {
    greeting: 'Hola {client_name}',
    footer: 'Quedamos atentos a tus comentarios.\nUn abrazo, el equipo de Project App.',
    signer: 'vanessa',
  },
  is_customized: false,
  available_signers: [
    { key: 'gustavo', name: 'Gustavo Pérez', role: 'CEO · ProjectApp.' },
    { key: 'vanessa', name: 'Vanessa Rodríguez', role: 'Asistente Comercial · ProjectApp.' },
  ],
  available_variables: ['client_name', 'title'],
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
  return mockApi(page, async ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'emails/defaults/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDefaults) };
    }
    if (apiPath === 'emails/defaults/' && method === 'PUT') {
      const payload = route.request().postDataJSON() || {};
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...mockDefaults,
          config: { ...mockDefaults.config, ...payload },
          is_customized: true,
        }),
      };
    }
    if (apiPath === 'emails/preview/' && method === 'POST') {
      // Echo the composed sections back as the server-rendered branded html.
      const payload = route.request().postDataJSON() || {};
      const sectionsHtml = (payload.sections || []).map((s) => `<p>${s.text}</p>`).join('');
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          subject: payload.subject || '',
          html_preview: `<!doctype html><html><body>${sectionsHtml}<div>team@projectapp.co</div></body></html>`,
        }),
      };
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
    await page.getByPlaceholder('Escribe el contenido de esta sección...').fill('Hello, this is a test email body.');

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
    await page.getByPlaceholder('Escribe el contenido de esta sección...').fill('Welcome to our platform.');

    const sendWait = page.waitForResponse(
      (res) => res.url().includes('emails/send/') && res.status() === 200,
    );
    await page.getByRole('button', { name: /enviar correo/i }).click();
    await sendWait;

    await expect(page.getByText('Correo enviado correctamente.')).toBeVisible({ timeout: 5000 });
  });

  test('preview tab fetches the server-rendered template into an iframe', {
    tag: [...ADMIN_STANDALONE_EMAIL_COMPOSER, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page);
    await page.goto('/panel/emails', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Emails' })).toBeVisible({ timeout: 20_000 });

    await page.getByPlaceholder('correo@ejemplo.com').fill('test@example.com');
    await page.getByPlaceholder('Asunto del correo').fill('Preview Test');
    await page.getByPlaceholder('Escribe el contenido de esta sección...').fill('Body content for preview.');

    const previewWait = page.waitForResponse(
      (res) => res.url().includes('emails/preview/') && res.status() === 200,
    );
    await page.getByRole('button', { name: /vista previa/i }).click();
    await previewWait;

    const frame = page.frameLocator('iframe[title="Vista previa del correo"]');
    await expect(frame.getByText('Body content for preview.')).toBeVisible();
    await expect(frame.getByText('team@projectapp.co')).toBeVisible();
  });

  test('markdown toggle sends the section flagged as markdown', {
    tag: [...ADMIN_STANDALONE_EMAIL_COMPOSER, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page);
    await page.goto('/panel/emails', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Emails' })).toBeVisible({ timeout: 20_000 });

    await page.getByPlaceholder('correo@ejemplo.com').fill('test@example.com');
    await page.getByPlaceholder('Asunto del correo').fill('Markdown Test');
    await page.getByPlaceholder('Escribe el contenido de esta sección...').fill('Texto **con** markdown');
    await page.getByRole('switch', { name: 'Activar Markdown en esta sección' }).click();

    const previewRequest = page.waitForRequest(
      (req) => req.url().includes('emails/preview/') && req.method() === 'POST',
    );
    await page.getByRole('button', { name: /vista previa/i }).click();
    const request = await previewRequest;

    expect(request.postDataJSON().sections).toEqual([
      { text: 'Texto **con** markdown', markdown: true },
    ]);
  });

  test('renders email history with entries in the Historial tab', {
    tag: [...ADMIN_STANDALONE_EMAIL_COMPOSER, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page, { history: mockHistoryWithEntries });
    await page.goto('/panel/emails', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Emails' })).toBeVisible({ timeout: 20_000 });

    await page.getByRole('tab', { name: 'Historial' }).click();

    await expect(page.getByText('Bienvenido al proyecto')).toBeVisible();
    await expect(page.getByText('client@example.com')).toBeVisible();
    await expect(page.getByText('Seguimiento entregable')).toBeVisible();
  });

  test('shows empty history state in the Historial tab', {
    tag: [...ADMIN_STANDALONE_EMAIL_COMPOSER, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page, { history: mockHistoryEmpty });
    await page.goto('/panel/emails', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Emails' })).toBeVisible({ timeout: 20_000 });

    await page.getByRole('tab', { name: 'Historial' }).click();

    await expect(page.getByText('No se han enviado correos aún.')).toBeVisible();
    await expect(page.getByText('Bienvenido al proyecto')).not.toBeVisible();
  });

  test('defaults tab shows the config form prefilled from the API', {
    tag: [...ADMIN_STANDALONE_EMAIL_DEFAULTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page);
    await page.goto('/panel/emails', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Emails' })).toBeVisible({ timeout: 20_000 });

    await page.getByRole('tab', { name: 'Valores por defecto' }).click();

    await expect(page.getByPlaceholder('Hola {client_name}')).toHaveValue('Hola {client_name}');
    await expect(page.getByPlaceholder('Texto de cierre...')).toHaveValue(mockDefaults.config.footer);
    await expect(page.getByRole('combobox')).toHaveValue('vanessa');
    await expect(page.getByText('Variables disponibles:')).toBeVisible();
  });

  test('saving defaults sends a PUT with greeting, footer and signer', {
    tag: [...ADMIN_STANDALONE_EMAIL_DEFAULTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page);
    await page.goto('/panel/emails', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Emails' })).toBeVisible({ timeout: 20_000 });

    await page.getByRole('tab', { name: 'Valores por defecto' }).click();

    await page.getByPlaceholder('Hola {client_name}').fill('Buen día {client_name}');
    await page.getByRole('combobox').selectOption('gustavo');

    const putRequest = page.waitForRequest(
      (req) => req.url().includes('emails/defaults/') && req.method() === 'PUT',
    );
    await page.getByRole('button', { name: 'Guardar valores' }).click();
    const request = await putRequest;

    const body = request.postDataJSON();
    expect(body.greeting).toBe('Buen día {client_name}');
    expect(body.signer).toBe('gustavo');
    await expect(page.getByText('Valores por defecto guardados')).toBeVisible({ timeout: 5000 });
  });

  test('opens the defaults tab directly from a ?tab=defaults URL', {
    tag: [...ADMIN_STANDALONE_EMAIL_DEFAULTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page);
    await page.goto('/panel/emails?tab=defaults', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Emails' })).toBeVisible({ timeout: 20_000 });

    await expect(page.getByRole('button', { name: 'Guardar valores' })).toBeVisible();
    await expect(page.getByPlaceholder('correo@ejemplo.com')).not.toBeVisible();
  });
});
