/**
 * @flow:admin-client-communications
 * E2E coverage for the manual client communications registry.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_CLIENT_COMMUNICATIONS } from '../helpers/flow-tags.js';
import { PANEL_BREAKPOINTS } from '../../config/responsive.js';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const documentReference = {
  id: 73,
  title: 'Alcance fase 2',
  status: 'published',
  project_id: 19,
  client_user_id: 501,
};

const outgoingMessage = {
  id: 801,
  thread_id: 41,
  channel: 'email',
  channel_display: 'Correo',
  direction: 'outgoing',
  direction_display: 'Saliente',
  status: 'sent',
  status_display: 'Enviado',
  subject: 'Alcance para aprobación',
  content: 'Te compartimos el alcance actualizado.',
  occurred_at: '2026-08-24T14:00:00Z',
  recorded_at: '2026-08-24T14:05:00Z',
  updated_at: '2026-08-24T14:05:00Z',
  source: 'manual',
  reply_to_id: null,
  has_reply: true,
  documents: [documentReference],
  date_corrections: [],
  created_by_name: 'Admin',
  voided_at: null,
  void_reason: '',
};

const incomingMessage = {
  ...outgoingMessage,
  id: 802,
  channel: 'whatsapp',
  channel_display: 'WhatsApp',
  direction: 'incoming',
  direction_display: 'Entrante',
  status: 'received',
  status_display: 'Recibido',
  subject: '',
  content: 'Está aprobado, pueden continuar.',
  occurred_at: '2026-08-24T15:10:00Z',
  recorded_at: '2026-08-24T15:12:00Z',
  reply_to_id: 801,
  has_reply: false,
  documents: [],
};

function listThread(overrides = {}) {
  return {
    id: 41,
    title: 'Aprobación de alcance',
    status: 'open',
    client_id: 7,
    client_name: 'Ana Proyecto',
    client_email: 'ana@example.com',
    project_id: 19,
    project_name: 'Portal de clientes',
    messages_count: 2,
    draft_count: 0,
    channels: ['email', 'whatsapp'],
    latest_message: {
      id: 802,
      direction: 'incoming',
      status: 'received',
      content: incomingMessage.content,
      occurred_at: incomingMessage.occurred_at,
    },
    last_activity_at: incomingMessage.occurred_at,
    closed_at: null,
    created_at: '2026-08-24T13:00:00Z',
    updated_at: '2026-08-24T15:12:00Z',
    ...overrides,
  };
}

function secondThread() {
  return listThread({
    id: 42,
    title: 'Coordinación de entrega',
    project_id: null,
    project_name: null,
    messages_count: 0,
    channels: [],
    latest_message: null,
  });
}

async function setupCommunicationsApi(page, {
  listFailure = false,
  messageFailure = false,
  onMessage = null,
} = {}) {
  let shouldFailList = listFailure;
  const state = {
    thread: { ...listThread(), messages: [outgoingMessage, incomingMessage] },
  };

  await mockApi(page, async ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') return authCheck;

    if (apiPath === 'communications/threads/' && method === 'GET') {
      if (shouldFailList) {
        return {
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'El registro no está disponible.' }),
        };
      }
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [
            listThread({
              messages_count: state.thread.messages.length,
              latest_message: state.thread.messages.at(-1),
            }),
            secondThread(),
          ],
          count: 2,
          page: 1,
          num_pages: 1,
        }),
      };
    }

    if (apiPath === 'communications/threads/41/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(state.thread),
      };
    }

    if (apiPath === 'communications/threads/41/messages/' && method === 'POST') {
      const payload = route.request().postDataJSON();
      if (onMessage) onMessage(payload);
      if (messageFailure) {
        return {
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'El hilo fue cerrado por otra sesión.' }),
        };
      }
      const created = {
        ...outgoingMessage,
        id: 803,
        channel: payload.channel,
        channel_display: payload.channel === 'email' ? 'Correo' : 'WhatsApp',
        direction: payload.direction,
        direction_display: payload.direction === 'incoming' ? 'Entrante' : 'Saliente',
        status: payload.status,
        status_display: payload.status === 'sent' ? 'Enviado' : 'Borrador',
        subject: payload.subject,
        content: payload.content,
        occurred_at: payload.occurred_at,
        reply_to_id: payload.reply_to,
        documents: [],
        has_reply: false,
      };
      state.thread.messages.push(created);
      state.thread.messages_count = state.thread.messages.length;
      state.thread.latest_message = created;
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(created),
      };
    }

    if (apiPath === 'documents/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([documentReference]),
      };
    }

    return null;
  });

  return {
    failList() {
      shouldFailList = true;
    },
  };
}

async function gotoCommunications(page) {
  // quality: allow-deep-link (the display outcome below covers entry through panel navigation)
  await page.goto('/panel/communications', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: 'Comunicaciones', exact: true }))
    .toBeVisible({ timeout: 30_000 });
}

async function enterCommunicationsThroughPanel(page) {
  await page.goto('/panel', { waitUntil: 'domcontentloaded' });
  if (page.viewportSize().width < PANEL_BREAKPOINTS.landscape) {
    await page.getByRole('button', { name: 'Abrir menú' }).click();
  }
  const link = page.getByRole('link', { name: 'Hilos con clientes', exact: true });
  await expect(link).toBeVisible({ timeout: 25_000 });
  await link.click();
  await expect(page.getByRole('heading', { name: 'Comunicaciones', exact: true }))
    .toBeVisible({ timeout: 30_000 });
}

async function openMainThread(page) {
  await page.getByTestId('communication-thread-41').click();
  await expect(page.getByRole('heading', { name: 'Aprobación de alcance', exact: true }))
    .toBeVisible();
}

test.describe('Admin Client Communications', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 9100, role: 'admin', is_staff: true },
    });
  });

  test('shows the bidirectional timeline and referenced documents', {
    tag: [
      ...ADMIN_CLIENT_COMMUNICATIONS,
      '@role:admin',
      '@outcome:display',
      '@responsive:communications',
    ],
  }, async ({ page }) => {
    await setupCommunicationsApi(page);
    await enterCommunicationsThroughPanel(page);

    await expect(page.getByTestId('communications-channel-scope'))
      .toContainText('el panel conserva el registro');
    await openMainThread(page);

    const timeline = page.getByTestId('communication-timeline');
    await expect(page.getByTestId('communication-message-801')
      .getByText('Te compartimos el alcance actualizado.', { exact: true }))
      .toBeVisible();
    await expect(page.getByTestId('communication-message-802')
      .getByText('Está aprobado, pueden continuar.', { exact: true }))
      .toBeVisible();
    await expect(timeline.getByRole('link', { name: /Alcance fase 2/ })).toBeVisible();
    await expect(page.getByTestId('communication-message-802')
      .getByRole('link', { name: /En respuesta.*Te compartimos el alcance actualizado/ }))
      .toHaveAttribute('href', '#communication-message-801');
    await expect(timeline.getByText('Respondido', { exact: true })).toBeVisible();
    await expect(timeline.getByText('Recibido', { exact: true })).toBeVisible();
  });

  test('registers an outgoing WhatsApp message as sent', {
    tag: [...ADMIN_CLIENT_COMMUNICATIONS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let submittedPayload = null;
    await setupCommunicationsApi(page, {
      onMessage: (payload) => { submittedPayload = payload; },
    });
    await gotoCommunications(page);
    await openMainThread(page);

    await page.getByTestId('communication-message-content')
      .fill('Confirmamos que el equipo inicia mañana.');
    await page.getByTestId('communication-register-sent').click();

    await expect.poll(() => submittedPayload).toMatchObject({
      channel: 'whatsapp',
      direction: 'outgoing',
      status: 'sent',
      content: 'Confirmamos que el equipo inicia mañana.',
    });
    await expect(page.getByTestId('communication-timeline')
      .getByText('Confirmamos que el equipo inicia mañana.')).toBeVisible();
    await expect(page.getByText('Mensaje registrado', { exact: true })).toBeVisible();
  });

  test('keeps the composer visible when the API rejects a message', {
    tag: [...ADMIN_CLIENT_COMMUNICATIONS, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    await setupCommunicationsApi(page, { messageFailure: true });
    await gotoCommunications(page);
    await openMainThread(page);

    const content = page.getByTestId('communication-message-content');
    await content.fill('Este texto no debe perderse.');
    await page.getByTestId('communication-register-sent').click();

    await expect(page.getByText('El hilo fue cerrado por otra sesión.', { exact: true }).first())
      .toBeVisible();
    await expect(content).toHaveValue('Este texto no debe perderse.');
  });

  test('shows a recoverable state when the thread list cannot load', {
    tag: [...ADMIN_CLIENT_COMMUNICATIONS, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    const api = await setupCommunicationsApi(page);
    await gotoCommunications(page);
    api.failList();
    const failedList = page.waitForResponse((response) => (
      response.url().includes('/api/communications/threads/')
      && response.request().method() === 'GET'
      && response.status() === 503
    ));
    const refresh = page.getByRole('button', { name: 'Actualizar hilos' });
    await refresh.click();
    await failedList;

    await expect(refresh).toBeEnabled();
    await expect(page.getByRole('alert').filter({ hasText: 'El registro no está disponible.' }))
      .toContainText('No se pudieron completar los cambios.');
  });
});
