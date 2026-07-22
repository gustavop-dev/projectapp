/**
 * E2E tests for the admin document send-email flow.
 *
 * @flow:admin-document-send-email
 * Covers: opening SendDocumentEmailModal from the actions sheet with the
 *         document preselected, sending the branded email (POST
 *         /api/emails/send/ with document_ids), the 429 rate-limited
 *         branch and the generic send-error branch keeping the modal open.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_SEND_EMAIL } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDocuments = [
  {
    id: 1, title: 'Contrato de Servicios', status: 'published',
    client_name: 'ACME Corp', created_at: '2026-03-01T10:00:00Z',
  },
  {
    id: 2, title: 'Propuesta Técnica', status: 'draft',
    client_name: null, created_at: '2026-03-05T14:00:00Z',
  },
];

const emailDefaults = { greeting: 'Hola,', footer: 'Saludos cordiales', subject: '' };

function baseRoutes(apiPath) {
  if (apiPath === 'auth/check/') return authCheck;
  if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocuments) };
  if (apiPath === 'document-folders/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  if (apiPath === 'document-tags/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  if (apiPath === 'emails/defaults/') return { status: 200, contentType: 'application/json', body: JSON.stringify(emailDefaults) };
  return null;
}

async function openSendEmailModal(page) {
  await page.goto('/panel/documents');
  await page.getByRole('row', { name: /Contrato de Servicios/i }).locator('button[title="Acciones"]').click();
  await page.getByRole('button', { name: /Enviar por correo/i }).click();
  await expect(page.getByRole('heading', { name: 'Enviar por correo' })).toBeVisible();
}

test.describe('Admin Document Send Email', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('sends the branded email with the document preselected', {
    tag: [...ADMIN_DOCUMENT_SEND_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    let sendBody = null;
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'emails/send/' && method === 'POST') {
        sendBody = route.request().postData() || '';
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ message: 'ok' }) };
      }
      return baseRoutes(apiPath);
    });
    await openSendEmailModal(page);

    await expect(page.getByPlaceholder('Asunto del correo')).toHaveValue('Contrato de Servicios');
    await expect(page.getByText('Contrato de Servicios.pdf')).toBeVisible();

    await page.getByPlaceholder('correo@ejemplo.com').fill('cliente@acme.com');
    await page.getByPlaceholder('Escribe el contenido de esta sección...').fill('Adjunto el contrato firmado.');
    await page.getByRole('button', { name: 'Enviar', exact: true }).click();

    await expect(page.getByText('Correo enviado a cliente@acme.com.')).toBeVisible();
    expect(sendBody).toContain('cliente@acme.com');
    expect(sendBody).toContain('document_ids');
  });

  test('shows the rate-limited message when the backend answers 429', {
    tag: [...ADMIN_DOCUMENT_SEND_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'emails/send/' && method === 'POST') {
        return { status: 429, contentType: 'application/json', body: JSON.stringify({ error: 'Demasiados envíos. Intenta de nuevo en unos minutos.' }) };
      }
      return baseRoutes(apiPath);
    });
    await openSendEmailModal(page);

    await page.getByPlaceholder('correo@ejemplo.com').fill('cliente@acme.com');
    await page.getByPlaceholder('Escribe el contenido de esta sección...').fill('Contenido');
    await page.getByRole('button', { name: 'Enviar', exact: true }).click();

    await expect(page.getByText('Demasiados envíos. Intenta de nuevo en unos minutos.')).toBeVisible();
  });

  test('keeps the modal open with an inline error on send failure', {
    tag: [...ADMIN_DOCUMENT_SEND_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'emails/send/' && method === 'POST') {
        return { status: 500, contentType: 'application/json', body: '{}' };
      }
      return baseRoutes(apiPath);
    });
    await openSendEmailModal(page);

    await page.getByPlaceholder('correo@ejemplo.com').fill('cliente@acme.com');
    await page.getByPlaceholder('Escribe el contenido de esta sección...').fill('Contenido');
    await page.getByRole('button', { name: 'Enviar', exact: true }).click();

    await expect(page.getByText('No se pudo enviar el correo.')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Enviar por correo' })).toBeVisible();
  });
});
