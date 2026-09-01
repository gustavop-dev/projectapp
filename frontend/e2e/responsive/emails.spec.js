/** R-emails-01: responsive email views must keep recipient, subject and preview controls reachable rather than rendering an empty shell. */
import { test, expect, assertResponsiveScenario } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { viewportUse } from '../helpers/viewports.js';
import { RESPONSIVE_PROFILES, batchForScenario, getResponsiveScenario } from './catalog-scenarios.js';

const json = (body) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
const deliverabilityScenario = getResponsiveScenario('frontend/pages/panel/proposals/email-deliverability.vue');
const composerScenario = getResponsiveScenario('frontend/pages/panel/emails/index.vue');
const responsiveRecipient = ['client', 'responsive.test'].join('@');
const historyEntry = { id: 1, subject: 'Seguimiento responsive', recipient: responsiveRecipient, status: 'delivered', sent_at: '2026-08-25T10:00:00Z', has_body: true, metadata: { greeting: 'Hola Ana', sections: ['Contenido fixture para el preview.'], footer: 'Equipo ProjectApp' } };

async function setupEmails(page) {
  await setAuthLocalStorage(page, { token: 'emails-responsive-token', userAuth: { id: 9001, role: 'admin', is_staff: true, is_superuser: true } });
  await mockApi(page, async ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') return json({ user: { username: 'admin', is_staff: true, is_superuser: true } });
    if (apiPath === 'emails/defaults/' && method === 'GET') return json({ greeting: 'Hola', footer: 'Equipo ProjectApp', config: { greeting: 'Hola {client_name}', footer: 'Equipo ProjectApp', signer: 'vanessa' }, defaults: {}, available_signers: [] });
    if (apiPath === 'emails/history/' && method === 'GET') return json({ results: [historyEntry], total: 1, page: 1, has_next: false });
    if (apiPath === 'emails/preview/' && method === 'POST') { const payload = route.request().postDataJSON() || {}; return json({ subject: payload.subject, html_preview: `<!doctype html><html><body><p>${payload.sections?.[0]?.text || 'Contenido fixture para el preview.'}</p></body></html>` }); }
    if (apiPath.includes('email-deliverability')) return json({ results: [{ id: 1, recipient: responsiveRecipient, status: 'delivered', subject: 'Seguimiento responsive' }], summary: { delivered: 1 } });
    return null;
  });
}

async function openComposer(page) {
  await setupEmails(page);
  // quality: allow-deep-link (the standalone composer is itself the cataloged route; its form and preview are exercised below)
  await page.goto(composerScenario.resolvedUrl, { waitUntil: 'domcontentloaded' });
  await page.getByPlaceholder('correo@ejemplo.com').fill(responsiveRecipient);
  const subjectInput = page.getByPlaceholder('Asunto del correo');
  await subjectInput.fill('Seguimiento responsive');
  await expect(subjectInput).toHaveValue('Seguimiento responsive');
  return subjectInput;
}

for (const profile of RESPONSIVE_PROFILES) {
  test.describe(`emails catalog · ${profile}`, { tag: [`@viewport:${profile}`] }, () => {
    test.use(viewportUse(profile));
    test('deliverability keeps a concrete recipient reachable after opening its filter control', { tag: ['@flow:admin-email-deliverability', '@outcome:display', '@responsive:emails', `@responsive-scenario:${deliverabilityScenario.catalogKey}`, `@responsive-batch:${batchForScenario(deliverabilityScenario.catalogKey)}`, `@viewport:${profile}`] }, async ({ page }, testInfo) => {
      await setupEmails(page);
      // quality: allow-deep-link (this catalog status route has no panel navigation equivalent)
      await page.goto(deliverabilityScenario.resolvedUrl, { waitUntil: 'domcontentloaded' });
      await page.getByRole('button', { name: /filtros/i }).click();
      const priorityLocator = page.getByText(responsiveRecipient, { exact: true });
      await expect(priorityLocator).toHaveCount(1);
      await assertResponsiveScenario(page, testInfo, deliverabilityScenario, { profile, priorityLocator });
    });

    test('composer keeps the filled subject after its responsive form interaction', { tag: ['@flow:admin-standalone-email-composer', '@outcome:display', '@responsive:emails', `@responsive-scenario:${composerScenario.catalogKey}`, `@responsive-batch:${batchForScenario(composerScenario.catalogKey)}`, `@viewport:${profile}`] }, async ({ page }, testInfo) => {
      // quality: allow-deep-link (the standalone composer is entered directly from a contextual action outside this catalog route)
      const priorityLocator = await openComposer(page);
      await expect(priorityLocator).toHaveCount(1);
      await assertResponsiveScenario(page, testInfo, composerScenario, { profile, priorityLocator });
    });
  });
}

test.describe('emails responsive special', () => {
  test.use(viewportUse('portrait'));
  test('composer preserves its completed subject after preview dismissal', { tag: ['@flow:admin-standalone-email-composer', '@outcome:success', '@responsive-special:emails', '@viewport:portrait', '@responsive-batch:emails-special-1'] }, async ({ page }) => {
    const subjectInput = await openComposer(page);
    await page.getByPlaceholder('Escribe el contenido de esta sección...').fill('Contenido fixture para el preview.');
    const previewResponse = page.waitForResponse((response) => response.url().includes('emails/preview/') && response.status() === 200);
    await page.getByRole('button', { name: 'Vista previa', exact: true }).click();
    await previewResponse;
    await expect(page.frameLocator('iframe[title="Vista previa del correo"]').getByText('Contenido fixture para el preview.', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Editar', exact: true }).click();
    await expect(subjectInput).toHaveValue('Seguimiento responsive');
  });
});
