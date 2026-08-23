import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_CLIENT_EMAIL_COPY_HISTORY,
  ADMIN_CLIENT_EMAIL_COPY_SETTINGS,
} from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const json = (body, status = 200) => ({
  status,
  contentType: 'application/json',
  body: JSON.stringify(body),
});

const authCheck = json({
  user: { username: 'admin', is_staff: true, is_superuser: true },
});

const defaults = {
  greeting: 'Hola',
  footer: 'Quedamos atentos.',
  config: { greeting: 'Hola {client_name}', footer: 'Quedamos atentos.', signer: 'carlos' },
  defaults: { greeting: 'Hola {client_name}', footer: 'Quedamos atentos.', signer: 'carlos' },
  available_signers: [{ key: 'carlos', name: 'Carlos', role: 'CTO' }],
  available_variables: ['client_name'],
};

const families = [
  { value: 'proposals', label: 'Propuestas' },
  { value: 'diagnostics', label: 'Diagnósticos' },
  { value: 'documents_manual', label: 'Documentos y correos manuales' },
  { value: 'collections', label: 'Cuentas de cobro' },
  { value: 'platform', label: 'Plataforma' },
];

const configuredRecipient = {
  id: 8,
  email: 'audit@projectapp.co',
  is_active: true,
  families: ['proposals', 'collections'],
  family_labels: ['Propuestas', 'Cuentas de cobro'],
};

const history = {
  results: [{
    id: 41,
    subject: 'Seguimiento contractual',
    recipient: 'client@example.com',
    status: 'sent',
    sent_at: '2026-08-23T10:00:00Z',
    metadata: { greeting: 'Hola Ana', sections: ['Adjuntamos el contrato.'] },
    copies: [{
      id: 42,
      recipient: 'audit@projectapp.co',
      status: 'failed',
      status_label: 'Fallido',
      error_message: 'SMTP timeout interno',
    }],
  }],
  total: 1,
  page: 1,
  has_next: false,
};

async function setupMocks(page, options = {}) {
  let rows = [...(options.recipients ?? [configuredRecipient])];
  const calls = [];
  await mockApi(page, async ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'panel/dashboard/') return json({});
    if (apiPath === 'emails/defaults/' && method === 'GET') return json(defaults);
    if (apiPath.startsWith('emails/history') && method === 'GET') return json(history);
    if (apiPath === 'emails/copy-recipients/' && method === 'GET') {
      return json({ results: rows, families, copy_mode: 'bcc' });
    }
    if (apiPath === 'emails/copy-recipients/' && method === 'POST') {
      const payload = route.request().postDataJSON();
      calls.push({ method, payload });
      if (options.createError) return json(options.createError, 400);
      const created = { id: 9, ...payload, family_labels: [] };
      rows = [...rows, created];
      return json(created, 201);
    }
    if (apiPath === 'emails/copy-recipients/8/' && method === 'PATCH') {
      const payload = route.request().postDataJSON();
      calls.push({ method, payload });
      if (options.patchFailure) return json(options.patchFailure, 503);
      rows = rows.map(row => row.id === 8 ? { ...row, ...payload } : row);
      return json(rows.find(row => row.id === 8));
    }
    if (apiPath === 'emails/copy-recipients/8/' && method === 'DELETE') {
      calls.push({ method });
      rows = rows.filter(row => row.id !== 8);
      return { status: 204, body: '' };
    }
    return null;
  });
  return calls;
}

async function navigateToEmails(page) {
  await page.goto('/panel', { waitUntil: 'domcontentloaded' });
  const navigation = page.getByRole('navigation', { name: 'Navegación del panel' });
  await navigation.getByRole('link', { name: 'Emails', exact: true }).click();
  await page.waitForURL(/\/panel\/emails(?:\?|$)/);
  await expect(page.getByRole('heading', { name: 'Emails' }))
    .toBeVisible({ timeout: 20_000 });
}

async function openConfiguration(page) {
  await navigateToEmails(page);
  await page.getByRole('tab', { name: 'Configuración' }).click();
  await expect(page.getByTestId('client-email-copy-settings')).toBeVisible();
}

test.beforeEach(async ({ page }) => {
  await setAuthLocalStorage(page, {
    token: 'e2e-admin-token',
    userAuth: { id: 8700, role: 'admin', is_staff: true, is_superuser: true },
  });
});

test('shows configured BCC families and the volume impact', {
  tag: [...ADMIN_CLIENT_EMAIL_COPY_SETTINGS, '@role:admin', '@outcome:display'],
}, async ({ page }) => {
  await setupMocks(page);
  await openConfiguration(page);

  const row = page.getByTestId('client-copy-row-8');
  await expect(row).toContainText('audit@projectapp.co');
  await expect(row.getByText('Activo')).toBeVisible();
  await expect(page.getByText(/volumen SMTP/)).toBeVisible();
  await expect(page.getByText(/copia de forma oculta/)).toBeVisible();
  await expect(page.getByTestId('client-copy-8-proposals')).toBeChecked();
  await expect(page.getByTestId('client-copy-8-diagnostics')).not.toBeChecked();
});

test('adds a recipient subscribed to every family', {
  tag: [...ADMIN_CLIENT_EMAIL_COPY_SETTINGS, '@role:admin', '@outcome:success'],
}, async ({ page }) => {
  const calls = await setupMocks(page, { recipients: [] });
  await openConfiguration(page);

  await page.getByTestId('client-copy-email').fill('new@projectapp.co');
  await page.getByTestId('client-copy-add').click();

  await expect(page.getByText('new@projectapp.co')).toBeVisible();
  const post = calls.find(call => call.method === 'POST');
  expect(post.payload.families).toEqual(families.map(item => item.value));
});

test('persists a changed family selection', {
  tag: [...ADMIN_CLIENT_EMAIL_COPY_SETTINGS, '@role:admin', '@outcome:success'],
}, async ({ page }) => {
  const calls = await setupMocks(page);
  await openConfiguration(page);

  await page.getByTestId('client-copy-8-diagnostics').check();
  await page.getByTestId('client-copy-save-8').click();

  await expect.poll(() => calls.find(call => call.method === 'PATCH'))
    .toBeTruthy();
  expect(calls.find(call => call.method === 'PATCH').payload.families)
    .toEqual(['proposals', 'diagnostics', 'collections']);
});

test('pauses a configured recipient', {
  tag: [...ADMIN_CLIENT_EMAIL_COPY_SETTINGS, '@role:admin', '@outcome:success'],
}, async ({ page }) => {
  const calls = await setupMocks(page);
  await openConfiguration(page);

  await page.getByTestId('client-copy-toggle-8').click();

  await expect(page.getByTestId('client-copy-row-8')).toContainText('Pausado');
  expect(calls.find(call => call.method === 'PATCH').payload)
    .toEqual({ is_active: false });
});

test('removes a configured recipient', {
  tag: [...ADMIN_CLIENT_EMAIL_COPY_SETTINGS, '@role:admin', '@outcome:success'],
}, async ({ page }) => {
  const calls = await setupMocks(page);
  await openConfiguration(page);

  await page.getByTestId('client-copy-delete-8').click();

  await expect(page.getByTestId('client-copy-row-8')).toHaveCount(0);
  expect(calls.some(call => call.method === 'DELETE')).toBe(true);
});

test('shows duplicate-address validation from the API', {
  tag: [...ADMIN_CLIENT_EMAIL_COPY_SETTINGS, '@role:admin', '@outcome:error'],
}, async ({ page }) => {
  await setupMocks(page, {
    createError: { email: ['Ese correo ya está en la lista.'] },
  });
  await openConfiguration(page);

  await page.getByTestId('client-copy-email').fill('audit@projectapp.co');
  await page.getByTestId('client-copy-add').click();

  await expect(page.getByText('Ese correo ya está en la lista.')).toBeVisible();
});

test('keeps the active state when the pause request fails', {
  tag: [...ADMIN_CLIENT_EMAIL_COPY_SETTINGS, '@role:admin', '@outcome:failure'],
}, async ({ page }) => {
  await setupMocks(page, {
    patchFailure: { detail: 'Servicio temporalmente no disponible.' },
  });
  await openConfiguration(page);

  await page.getByTestId('client-copy-toggle-8').click();

  await expect(page.getByText('Servicio temporalmente no disponible.'))
    .toBeVisible();
  await expect(page.getByTestId('client-copy-row-8')).toContainText('Activo');
});

test('shows a failed BCC attempt under its primary history row', {
  tag: [...ADMIN_CLIENT_EMAIL_COPY_HISTORY, '@role:admin', '@outcome:display'],
}, async ({ page }) => {
  await setupMocks(page);
  await navigateToEmails(page);
  await page.getByRole('tab', { name: 'Historial' }).click();

  await page.getByText('Seguimiento contractual').click();

  const copies = page.getByTestId('email-copy-list-41');
  await expect(copies).toContainText('audit@projectapp.co');
  await expect(copies).toContainText('Fallido');
  await expect(copies).toContainText('SMTP timeout interno');
});
