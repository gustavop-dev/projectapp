/**
 * E2E tests for admin sending a proposal to a client.
 *
 * Covers: "Enviar al Cliente" button click, API call verification,
 * status badge updates to 'sent', re-send button appears for sent proposals.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_SEND } from '../helpers/flow-tags.js';

const PROPOSAL_ID = 1;

const futureDate = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();

const mockDraftProposal = {
  id: PROPOSAL_ID,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'Send Test Proposal',
  client_name: 'Test Client',
  client_email: 'client@test.com',
  status: 'draft',
  language: 'es',
  total_investment: '5000000',
  currency: 'COP',
  view_count: 0,
  sent_at: null,
  expires_at: futureDate,
  is_active: true,
  sections: [
    { id: 10, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true, content_json: { clientName: 'Test Client' } },
  ],
  requirement_groups: [],
};

test.describe('Admin Proposal Send', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8300, role: 'admin', is_staff: true },
    });
  });

  test('"Enviar al Cliente" button is visible for draft proposal with email', {
    tag: [...ADMIN_PROPOSAL_SEND, '@role:admin'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (render guard for a valid draft; the send action itself is covered by the send tests below)
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDraftProposal) };
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await expect(page.getByRole('button', { name: 'Enviar al Cliente' })).toBeVisible();
  });

  test('clicking "Enviar al Cliente" opens checklist modal and sends on confirm', {
    tag: [...ADMIN_PROPOSAL_SEND, '@role:admin'],
  }, async ({ page }) => {
    let sendCalled = false;

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      }
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDraftProposal) };
      }
      if (apiPath === `proposals/${PROPOSAL_ID}/send/`) {
        sendCalled = true;
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockDraftProposal, status: 'sent', sent_at: '2026-03-04T12:00:00Z' }) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    // Click the send button — opens the pre-send checklist modal
    await page.getByRole('button', { name: 'Enviar al Cliente' }).first().click();

    // Scorecard modal should appear
    await expect(page.getByText('Scorecard pre-envío')).toBeVisible();

    // Click the modal's send button to confirm
    const [sendResponse] = await Promise.all([
      page.waitForResponse(r => r.url().includes(`proposals/${PROPOSAL_ID}/send/`)),
      page.locator('.fixed').getByRole('button', { name: 'Enviar al Cliente' }).click(),
    ]);
    await sendResponse.finished();

    expect(sendCalled).toBe(true);
    // the pre-send scorecard modal dismisses once the send resolves
    await expect(page.getByText('Scorecard pre-envío')).not.toBeVisible();
  });

  test('"Re-enviar al Cliente" button appears for sent proposal', {
    tag: [...ADMIN_PROPOSAL_SEND, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockDraftProposal, status: 'sent', sent_at: '2026-03-04T12:00:00Z' }) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    // For sent proposals, the resend action lives inside the actions menu.
    await page.getByTestId('proposal-actions-menu').click();
    await expect(page.getByTestId('proposal-action-resend')).toContainText('Re-enviar', { timeout: 10000 });
  });

  test('"Enviar al Cliente" is hidden when client email is empty', {
    tag: [...ADMIN_PROPOSAL_SEND, '@role:admin'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (asserts conditional rendering — the send button is withheld when the client has no email; no user action applies)
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockDraftProposal, client_email: '' }) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await expect(page.getByRole('button', { name: 'Enviar al Cliente' })).not.toBeVisible();
  });

  test('editing the email intro persists it through the update PATCH', {
    tag: [...ADMIN_PROPOSAL_SEND, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDraftProposal) };
      if (apiPath === `proposals/${PROPOSAL_ID}/update/` && method === 'PATCH') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDraftProposal) };
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`, { waitUntil: 'domcontentloaded' });

    const intro = page.getByTestId('edit-email-intro');
    await intro.waitFor({ state: 'visible', timeout: 15000 });
    await intro.fill('Hola María, adjunto la propuesta actualizada.');

    const [req] = await Promise.all([
      page.waitForRequest((r) => r.url().includes(`proposals/${PROPOSAL_ID}/update/`) && r.method() === 'PATCH'),
      page.getByRole('button', { name: 'Guardar Cambios' }).click(),
    ]);
    expect(req.postDataJSON().email_intro).toEqual('Hola María, adjunto la propuesta actualizada.');
  });

  test('shows a warning toast when the email delivery fails on send', {
    tag: [...ADMIN_PROPOSAL_SEND, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDraftProposal) };
      if (apiPath === `proposals/${PROPOSAL_ID}/send/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockDraftProposal, status: 'sent', sent_at: '2026-03-04T12:00:00Z', email_delivery: { ok: false, detail: 'El servidor SMTP rechazó el correo.' } }) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.getByRole('button', { name: 'Enviar al Cliente' }).first().click();
    await expect(page.getByText('Scorecard pre-envío')).toBeVisible();
    await Promise.all([
      page.waitForResponse((r) => r.url().includes(`proposals/${PROPOSAL_ID}/send/`)),
      page.locator('.fixed').getByRole('button', { name: 'Enviar al Cliente' }).click(),
    ]);

    await expect(page.getByText('Propuesta marcada como enviada')).toContainText('marcada como enviada');
  });

  test('shows a success toast when the send delivers', {
    tag: [...ADMIN_PROPOSAL_SEND, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDraftProposal) };
      if (apiPath === `proposals/${PROPOSAL_ID}/send/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockDraftProposal, status: 'sent', sent_at: '2026-03-04T12:00:00Z', email_delivery: { ok: true } }) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.getByRole('button', { name: 'Enviar al Cliente' }).first().click();
    await expect(page.getByText('Scorecard pre-envío')).toBeVisible();
    await Promise.all([
      page.waitForResponse((r) => r.url().includes(`proposals/${PROPOSAL_ID}/send/`)),
      page.locator('.fixed').getByRole('button', { name: 'Enviar al Cliente' }).click(),
    ]);

    await expect(page.getByText('Propuesta enviada al cliente')).toContainText('enviada al cliente');
  });
});
