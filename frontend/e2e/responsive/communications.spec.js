/** R-communications-01: touch users must be able to change the visible thread order without hover. */
import { test, expect, assertResponsiveScenario } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { viewportUse } from '../helpers/viewports.js';
import { RESPONSIVE_PROFILES, batchForScenario, getResponsiveScenario } from './catalog-scenarios.js';

const scenario = getResponsiveScenario('frontend/pages/panel/communications/index.vue');
// The complete timeline shape comes from the communications flow fixture so
// opening and closing a thread mounts the real workspace, not a list-only stub.
const documentReference = { id: 73, title: 'Alcance fase 2', status: 'published', project_id: 19, client_user_id: 501 };
const outgoingMessage = { id: 801, thread_id: 41, channel: 'email', channel_display: 'Correo', direction: 'outgoing', direction_display: 'Saliente', status: 'sent', status_display: 'Enviado', subject: 'Alcance para aprobación', content: 'Te compartimos el alcance actualizado.', occurred_at: '2026-08-24T14:00:00Z', recorded_at: '2026-08-24T14:05:00Z', updated_at: '2026-08-24T14:05:00Z', source: 'manual', reply_to_id: null, has_reply: true, documents: [documentReference], date_corrections: [], created_by_name: 'Admin', voided_at: null, void_reason: '' };
const incomingMessage = { ...outgoingMessage, id: 802, channel: 'whatsapp', channel_display: 'WhatsApp', direction: 'incoming', direction_display: 'Entrante', status: 'received', status_display: 'Recibido', subject: '', content: 'Está aprobado, pueden continuar.', occurred_at: '2026-08-24T15:10:00Z', recorded_at: '2026-08-24T15:12:00Z', reply_to_id: 801, has_reply: false, documents: [] };
const thread = { id: 41, title: 'Aprobación de alcance', status: 'open', client_id: 7, client_name: 'Ana Proyecto', client_email: 'ana@example.com', project_id: 19, project_name: 'Portal de clientes', messages_count: 2, draft_count: 0, channels: ['email', 'whatsapp'], latest_message: { id: 802, direction: 'incoming', status: 'received', content: incomingMessage.content, occurred_at: incomingMessage.occurred_at }, last_activity_at: incomingMessage.occurred_at, closed_at: null, created_at: '2026-08-24T13:00:00Z', updated_at: '2026-08-24T15:12:00Z', messages: [outgoingMessage, incomingMessage] };
const supplementaryThreads = [
  { ...thread, id: 42, title: 'Coordinación de entrega', project_id: null, project_name: null, messages_count: 0, channels: [], latest_message: null },
  { ...thread, id: 43, title: 'Seguimiento de implementación', draft_count: 1, project_id: 143, project_name: 'Proyecto 43' },
  { ...thread, id: 44, title: 'Revisión de contenidos', project_id: 144, project_name: 'Proyecto 44' },
  { ...thread, id: 45, title: 'Cierre de publicación', project_id: 145, project_name: 'Proyecto 45' },
];

async function setupCommunications(page) {
  await setAuthLocalStorage(page, { token: 'communications-token', userAuth: { id: 9001, role: 'admin', is_staff: true } });
  await mockApi(page, async ({ apiPath, method }) => {
    const json = (body) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
    if (apiPath === 'auth/check/') return json({ user: { username: 'admin', is_staff: true } });
    if (apiPath === 'communications/threads/' && method === 'GET') return json({ results: [thread, ...supplementaryThreads], count: 5, page: 1, num_pages: 1, facets: { total: 5, navigation_total: 5, without_project_count: 1, projects: [{ id: 19, name: 'Portal de clientes', client_id: 7, client_name: 'Ana Proyecto', catalog_bucket: 'active', count: 4, unavailable: false }], clients: [{ id: 7, name: 'Ana Proyecto', count: 5, unavailable: false }], filters: { status: { open: 5, closed: 0 }, channel: { email: 4, whatsapp: 1 }, direction: { outgoing: 4, incoming: 1 }, message_status: { draft: 1, sent: 3, received: 1, failed: 0 }, reply_status: { answered: 1, unanswered: 3 } } } });
    if (apiPath === 'communications/threads/41/' && method === 'GET') return json(thread);
    if (apiPath === 'communications/threads/tab-counts/' && method === 'POST') return json({ counts: { all: 5, 'draft-pending': 1, 'sent-unanswered': 0, open: 5, closed: 0, 'channel-email': 4, 'channel-whatsapp': 1 } });
    if (apiPath === 'accounts/panel-preferences/communications/' && method === 'GET') return json({ navigation_mode: 'project', thread_order: 'recent', page_size: 20, default_channel: 'whatsapp', show_manual_help: true, navigation_width: 288 });
    if (apiPath === 'accounts/panel-preferences/communications/' && method === 'PATCH') return json({ navigation_mode: 'project', thread_order: 'oldest', page_size: 20, default_channel: 'whatsapp', show_manual_help: true, navigation_width: 288 });
    if (apiPath.startsWith('accounts/saved-filter-tabs')) return json([]);
    if (apiPath === 'projects/') return json({ results: [], meta: {} });
    if (apiPath === 'documents/' && method === 'GET') return json([documentReference]);
    return null;
  });
}

const communicationsEntryByProfile = Object.freeze({
  compact: async (page) => { await page.getByRole('button', { name: 'Abrir menú' }).click(); await page.getByRole('link', { name: 'Hilos con clientes', exact: true }).click(); },
  portrait: async (page) => { await page.getByRole('button', { name: 'Abrir menú' }).click(); await page.getByRole('link', { name: 'Hilos con clientes', exact: true }).click(); },
  landscape: (page) => page.getByRole('link', { name: 'Hilos con clientes', exact: true }).click(),
  desktop: (page) => page.getByRole('link', { name: 'Hilos con clientes', exact: true }).click(),
  wide: (page) => page.getByRole('link', { name: 'Hilos con clientes', exact: true }).click(),
});

async function openCommunications(page, profile) {
  await page.goto('/en-us/panel', { waitUntil: 'domcontentloaded' });
  await communicationsEntryByProfile[profile](page);
  await expect(page.getByRole('heading', { name: 'Comunicaciones', exact: true })).toHaveText('Comunicaciones');
}

for (const profile of RESPONSIVE_PROFILES) {
  test.describe(`communications catalog · ${profile}`, { tag: [`@viewport:${profile}`] }, () => {
    test.use(viewportUse(profile));
    test('thread order remains actionable through panel navigation', {
      tag: ['@flow:admin-client-communications', '@outcome:success', '@responsive:communications', `@responsive-scenario:${scenario.catalogKey}`, `@responsive-batch:${batchForScenario(scenario.catalogKey)}`, `@viewport:${profile}`],
    }, async ({ page }, testInfo) => {
      await setupCommunications(page);
      await openCommunications(page, profile);
      await page.getByTestId('communications-order-oldest').click();
      await expect(page.getByTestId('communications-order-oldest')).toHaveAttribute('aria-selected', 'true');
      await expect(page.getByTestId('communication-thread-row-41')).toContainText('Aprobación de alcance');
      await assertResponsiveScenario(page, testInfo, scenario, { profile });
    });
  });
}

test.describe('communications responsive special', () => {
  test.use(viewportUse('compact'));
  test('closing a thread preserves the oldest order selected from touch controls', {
    tag: ['@flow:admin-client-communications', '@outcome:success', '@responsive-special:communications', '@viewport:compact', '@responsive-batch:communications-special-1'],
  }, async ({ page }) => {
    await setupCommunications(page);
    // quality: allow-deep-link (the catalog scenario covers panel navigation; this isolates detail return state)
    await page.goto('/en-us/panel/communications', { waitUntil: 'domcontentloaded' });
    await page.getByTestId('communications-order-oldest').click();
    await expect(page.getByTestId('communications-order-oldest')).toHaveAttribute('aria-selected', 'true');
    await page.getByTestId('communication-thread-row-41').click();
    await expect(page.getByRole('heading', { name: 'Aprobación de alcance', exact: true })).toHaveText('Aprobación de alcance');
    await page.getByRole('button', { name: 'Cerrar detalle del hilo' }).click();
    await expect(page).not.toHaveURL(/(?:\?|&)thread=/);
    await expect(page.getByTestId('communications-order-oldest')).toHaveAttribute('aria-selected', 'true');
  });
});
