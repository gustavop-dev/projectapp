/**
 * E2E tests for the admin "Enviar oferta de descuento" action.
 *
 * @flow:admin-proposal-discount-offer-send
 * Covers: the discount-offer action appears only when discount_percent > 0 and the
 * client has an email; opening it renders a server-side email preview
 * (POST proposals/:id/email-preview/, template proposal_urgency); confirming sends the
 * offer (POST proposals/:id/discount-offer/send/) and surfaces a success toast.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_DISCOUNT_OFFER_SEND } from '../helpers/flow-tags.js';

const PROPOSAL_ID = 1;
const futureDate = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();

const json = (body) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

const mockProposal = (overrides = {}) => ({
  id: PROPOSAL_ID,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'Discount Offer Test Proposal',
  client_name: 'Test Client',
  client_email: 'client@test.com',
  status: 'sent',
  language: 'es',
  total_investment: '5000000',
  currency: 'COP',
  discount_percent: 15,
  view_count: 3,
  sent_at: '2026-07-01T12:00:00Z',
  expires_at: futureDate,
  is_active: true,
  sections: [
    { id: 10, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true, content_json: { clientName: 'Test Client' } },
  ],
  requirement_groups: [],
  ...overrides,
});

function setupMocks(page, { proposal, onSend } = {}) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'auth/check/') return json({ user: { username: 'admin', is_staff: true } });
    if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) return json(proposal || mockProposal());
    if (apiPath === `proposals/${PROPOSAL_ID}/email-preview/` && method === 'POST') {
      return { status: 200, contentType: 'text/html', body: '<html><body>Oferta de descuento del 15%</body></html>' };
    }
    if (apiPath === `proposals/${PROPOSAL_ID}/discount-offer/send/` && method === 'POST') {
      if (onSend) onSend();
      return json({ success: true });
    }
    return null;
  });
}

test.describe('Admin Proposal Discount Offer', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8300, role: 'admin', is_staff: true },
    });
  });

  test('previews and sends the discount offer, then shows a success toast', {
    tag: [...ADMIN_PROPOSAL_DISCOUNT_OFFER_SEND, '@role:admin'],
  }, async ({ page }) => {
    let sendCalled = false;
    await setupMocks(page, { onSend: () => { sendCalled = true; } });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    // Open the actions menu and pick the discount-offer action.
    await page.getByTestId('proposal-actions-menu').click();
    const discountAction = page.getByTestId('proposal-action-discount-offer');
    await expect(discountAction).toBeVisible();

    // Clicking it opens the discount modal and loads the email preview.
    await Promise.all([
      page.waitForResponse((r) => r.url().includes(`proposals/${PROPOSAL_ID}/email-preview/`)),
      discountAction.click(),
    ]);

    await expect(page.getByRole('heading', { name: 'Enviar oferta de descuento' })).toBeVisible();

    // Confirm sending the offer.
    const sendBtn = page.getByRole('button', { name: 'Enviar oferta', exact: true });
    await expect(sendBtn).toBeEnabled();
    await Promise.all([
      page.waitForResponse((r) => r.url().includes(`proposals/${PROPOSAL_ID}/discount-offer/send/`)),
      sendBtn.click(),
    ]);

    expect(sendCalled).toBe(true);
    await expect(page.getByText('Oferta de descuento enviada al cliente.')).toBeVisible();
  });

  test('discount-offer action is hidden when there is no discount', {
    tag: [...ADMIN_PROPOSAL_DISCOUNT_OFFER_SEND, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page, { proposal: mockProposal({ discount_percent: 0 }) });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await page.getByTestId('proposal-actions-menu').click();
    // The actions modal is open, but the discount-offer action is absent.
    await expect(page.getByRole('heading', { name: 'Acciones de la propuesta' })).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId('proposal-action-discount-offer')).toHaveCount(0);
  });

  test('discount-offer action is hidden when the client has no email', {
    tag: [...ADMIN_PROPOSAL_DISCOUNT_OFFER_SEND, '@role:admin'],
  }, async ({ page }) => {
    await setupMocks(page, { proposal: mockProposal({ client_email: '' }) });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await page.getByTestId('proposal-actions-menu').click();
    await expect(page.getByRole('heading', { name: 'Acciones de la propuesta' })).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId('proposal-action-discount-offer')).toHaveCount(0);
  });
});
