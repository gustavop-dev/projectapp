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

const compactListMessage = `Confirmamos que el alcance incluye la revisión de accesibilidad,
  las pruebas de aceptación y el acompañamiento de salida para todo el equipo responsable,
  con una secuencia adicional que sólo corresponde leer dentro del hilo.`;

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

function additionalThread(id, title, overrides = {}) {
  return listThread({
    id,
    title,
    project_id: id + 100,
    project_name: `Proyecto ${id}`,
    messages_count: 1,
    channels: ['email'],
    latest_message: {
      id: id + 800,
      direction: 'outgoing',
      status: 'sent',
      content: `Seguimiento breve del hilo ${id}.`,
      occurred_at: '2026-08-23T14:00:00Z',
    },
    last_activity_at: '2026-08-23T14:00:00Z',
    ...overrides,
  });
}

function communicationFacets(projectName = 'Portal de clientes') {
  return {
    total: 5,
    navigation_total: 5,
    without_project_count: 1,
    projects: [{
      id: 19,
      name: projectName,
      client_id: 7,
      count: 4,
      unavailable: false,
    }],
    clients: [{
      id: 7,
      name: 'Ana Proyecto',
      count: 5,
      unavailable: false,
    }],
    filters: {
      status: { open: 5, closed: 0 },
      channel: { email: 4, whatsapp: 1 },
      direction: { outgoing: 4, incoming: 1 },
      message_status: { draft: 1, sent: 3, received: 1, failed: 0 },
    },
  };
}

async function setupCommunicationsApi(page, {
  listFailure = false,
  messageFailure = false,
  onMessage = null,
  onListRequest = null,
  onSavedView = null,
  projectName = 'Portal de clientes',
} = {}) {
  let shouldFailList = listFailure;
  const state = {
    thread: {
      ...listThread({ project_name: projectName }),
      messages: [outgoingMessage, incomingMessage],
    },
  };

  await mockApi(page, async ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') return authCheck;

    if (apiPath === 'communications/threads/' && method === 'GET') {
      if (onListRequest) onListRequest(route.request().url());
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
              project_name: projectName,
              messages_count: state.thread.messages.length,
              latest_message: {
                ...state.thread.messages.at(-1),
                content: compactListMessage,
              },
            }),
            secondThread(),
            additionalThread(43, 'Seguimiento de implementación', { draft_count: 1 }),
            additionalThread(44, 'Revisión de contenidos'),
            additionalThread(45, 'Cierre de publicación'),
          ],
          count: 5,
          page: 1,
          num_pages: 1,
          facets: communicationFacets(projectName),
        }),
      };
    }

    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      if (method === 'POST' && apiPath === 'accounts/saved-filter-tabs/') {
        const payload = route.request().postDataJSON();
        if (onSavedView) onSavedView(payload);
        return {
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 901,
            ...payload,
            base_filters: payload.filters,
            builtin_key: '',
            order: 0,
            is_seeded: false,
          }),
        };
      }
      if (method === 'PATCH') {
        const payload = route.request().postDataJSON();
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ id: 901, view: 'communication', ...payload }),
        };
      }
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
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
  await page.getByTestId('communication-thread-row-41').click();
  await expect(page).toHaveURL(/(?:\?|&)thread=41(?:&|$)/);
  await expect(page.locator('[data-modal-kind="workspace"]')).toBeVisible();
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
      .toContainText('conserva el registro manual');
    await expect(page.getByTestId('communications-channel-scope'))
      .not.toContainText(/fase posterior|envío automático/i);

    if (page.viewportSize().width < PANEL_BREAKPOINTS.landscape) {
      await expect(page.getByTestId('communications-navigation-drawer-trigger')).toBeVisible();
    } else {
      const navigation = page.getByTestId('communications-navigation-panel');
      await expect(navigation).toContainText('Portal de clientes');
      await expect(navigation).toContainText('Sin proyecto');
    }
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

    await page.getByRole('button', { name: 'Cerrar detalle del hilo' }).click();
    await expect(page).not.toHaveURL(/(?:\?|&)thread=/);
    await expect(page.getByTestId('communication-thread-row-41')).toBeVisible();
  });

  test('summarizes compact thread cards without horizontal scrolling', {
    tag: [
      ...ADMIN_CLIENT_COMMUNICATIONS,
      '@role:admin',
      '@outcome:display',
      '@responsive:communications',
    ],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display — this scenario validates the initial compact list density and clipping contract)
    // quality: allow-deep-link (communications navigation is covered separately; this scenario isolates the responsive list render)
    await page.setViewportSize({ width: 412, height: 915 });
    await setupCommunicationsApi(page);
    await gotoCommunications(page);

    const list = page.getByTestId('communication-thread-list');
    const cards = list.locator('[data-testid^="communication-thread-row-"]');
    const mainCard = page.getByTestId('communication-thread-row-41');
    const excerpt = page.getByTestId('communication-thread-excerpt-41');

    await expect(cards).toHaveCount(5);
    await expect(mainCard).toContainText('Aprobación de alcance');
    await expect(mainCard).toContainText('Ana Proyecto · Portal de clientes');
    await expect(mainCard).toContainText('WhatsApp');
    await expect(mainCard).toContainText('2 mensajes');
    await expect(page.getByTestId('communication-thread-row-43')).toContainText('1 borrador');
    await expect(excerpt).toContainText('Cliente: Confirmamos que el alcance');
    await expect(excerpt).not.toContainText(compactListMessage);
    await expect(page.getByText('Hilo', { exact: true })).toHaveCount(0);

    const excerptLayout = await excerpt.evaluate((element) => {
      const style = getComputedStyle(element);
      return {
        height: element.getBoundingClientRect().height,
        lineHeight: Number.parseFloat(style.lineHeight),
        overflow: style.overflow,
        whiteSpace: style.whiteSpace,
      };
    });
    expect(excerptLayout.height).toBeLessThanOrEqual(excerptLayout.lineHeight + 1);
    expect(excerptLayout.overflow).toBe('hidden');
    expect(excerptLayout.whiteSpace).toBe('nowrap');
    await expect.poll(() => list.evaluate((element) => getComputedStyle(element).overflowX))
      .toBe('hidden');
    const pageOverflow = await page.evaluate(() => (
      Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)
      - document.documentElement.clientWidth
    ));
    expect(pageOverflow).toBeLessThanOrEqual(1);

    const visibleCards = await cards.evaluateAll((elements) => elements.filter((element) => {
      const rect = element.getBoundingClientRect();
      return rect.top < window.innerHeight && rect.bottom > 0;
    }).length);
    expect(visibleCards).toBeGreaterThan(1);
  });

  test('restores the selected order on a later visit', {
    tag: [
      ...ADMIN_CLIENT_COMMUNICATIONS,
      '@role:admin',
      '@outcome:success',
      '@responsive:communications',
    ],
  }, async ({ page }) => {
    const listRequests = [];
    await setupCommunicationsApi(page, {
      onListRequest: (url) => listRequests.push(url),
    });
    await gotoCommunications(page);

    const oldestOrder = page.getByTestId('communications-order-oldest');
    await oldestOrder.click();
    await expect(oldestOrder).toHaveAttribute('aria-selected', 'true');
    await expect(page).toHaveURL(/order=oldest/);
    await expect.poll(() => listRequests.some((url) => url.includes('order=oldest'))).toBe(true);
    await expect.poll(() => page.evaluate(() => (
      window.localStorage.getItem('panel.communications.order')
    ))).toBe('oldest');

    const laterVisitRequestIndex = listRequests.length;
    await gotoCommunications(page);

    await expect(page.getByTestId('communications-order-oldest'))
      .toHaveAttribute('aria-selected', 'true');
    await expect(page.getByTestId('communications-order-control')).toContainText('Orden:');
    await expect.poll(() => listRequests
      .slice(laterVisitRequestIndex)
      .some((url) => url.includes('order=oldest'))).toBe(true);
  });

  test('navigates by client, combines message statuses and saves the view', {
    tag: [...ADMIN_CLIENT_COMMUNICATIONS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const listRequests = [];
    let savedPayload = null;
    await setupCommunicationsApi(page, {
      onListRequest: (url) => listRequests.push(url),
      onSavedView: (payload) => { savedPayload = payload; },
    });
    await gotoCommunications(page);

    await page.getByTestId('communications-navigation-without-project').click();
    await expect(page).toHaveURL(/project=none/);
    await page.getByTestId('communications-mode-client').click();
    await expect(page).toHaveURL(/by=client/);
    await expect(page).not.toHaveURL(/project=/);
    await page.getByTestId('communications-navigation-client-7').click();
    await expect(page).toHaveURL(/client=7/);

    await page.getByTestId('communications-filter-toggle').click();
    await page.getByTestId('communications-message-status-filter').click();
    const statusDialog = page.getByRole('dialog', { name: 'Estado del mensaje' });
    await statusDialog.locator('input[value="draft"]').check();
    await statusDialog.locator('input[value="sent"]').check();
    await page.keyboard.press('Escape');

    await expect.poll(() => listRequests.at(-1)).toContain('message_status=draft%2Csent');
    await page.getByTestId('filter-tabs-create').click();
    await page.getByTestId('filter-tabs-input').fill('Borradores y enviados');
    await page.getByTestId('filter-tabs-confirm').click();

    await expect.poll(() => savedPayload).toMatchObject({
      view: 'communication',
      name: 'Borradores y enviados',
      filters: {
        by: 'client',
        client: '7',
        message_status: ['draft', 'sent'],
      },
    });
    await expect(page.getByTestId('filter-tabs-tab-901')).toBeVisible();

    await page.getByRole('button', { name: 'Todas', exact: true }).click();
    await expect(page).not.toHaveURL(/client=7/);
    await page.getByTestId('filter-tabs-tab-901').click();
    await expect(page).toHaveURL(/client=7/);
    await expect(page).toHaveURL(/message_status=draft(?:%2C|,)sent/);
  });

  test('searches the thread list by project name', {
    tag: [...ADMIN_CLIENT_COMMUNICATIONS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const listRequests = [];
    await setupCommunicationsApi(page, {
      onListRequest: (url) => listRequests.push(url),
    });
    await gotoCommunications(page);

    await page.getByRole('textbox', { name: 'Buscar comunicaciones' })
      .fill('Portal de clientes');

    await expect(page).toHaveURL(/q=Portal(?:\+|%20)de(?:\+|%20)clientes/);
    await expect.poll(() => listRequests.at(-1)).toMatch(
      /q=Portal(?:\+|%20)de(?:\+|%20)clientes/,
    );
    await expect(page.getByTestId('communication-thread-row-41')).toBeVisible();
  });

  test('keeps the manual notice dismissed until help reopens it', {
    tag: [...ADMIN_CLIENT_COMMUNICATIONS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await setupCommunicationsApi(page);
    // quality: allow-deep-link (panel entry is covered by the timeline display outcome)
    await gotoCommunications(page);

    await page.getByRole('button', { name: 'Cerrar alerta' }).click();
    await expect(page.getByTestId('communications-channel-scope')).toHaveCount(0);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('communications-channel-scope')).toHaveCount(0);

    await page.getByTestId('communications-show-help').click();
    await expect(page.getByTestId('communications-channel-scope')).toBeVisible();
  });

  test('persists the resized project navigation width', {
    tag: [...ADMIN_CLIENT_COMMUNICATIONS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const longProjectName = 'Portal de clientes con seguimiento contractual ampliado';
    await page.setViewportSize({ width: 1440, height: 900 });
    await setupCommunicationsApi(page, { projectName: longProjectName });
    await gotoCommunications(page);

    const handle = page.getByTestId('communications-navigation-resize-handle');
    const projectName = page.getByTestId('communications-navigation-project-19')
      .locator('span[title]');
    await expect(projectName).toHaveAttribute('title', longProjectName);
    await expect(handle).toHaveAttribute('aria-valuenow', '288');
    await handle.press('End');
    await expect(handle).toHaveAttribute('aria-valuenow', '400');

    await page.reload({ waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('communications-navigation-resize-handle'))
      .toHaveAttribute('aria-valuenow', '400');
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
      .toContainText('No se pudieron cargar las comunicaciones.');
  });
});
