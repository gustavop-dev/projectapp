/**
 * E2E tests for the platform hosting stored-card delete flow.
 *
 * @flow:platform-hosting-card-delete
 * A client with a stored card removes it: "Eliminar tarjeta" → confirmation
 * modal warning that automatic billing stops → DELETE
 * /api/accounts/projects/:id/subscription/card/remove/ → the register-card
 * state reappears. Covers confirm, cancel (no API call) and the error branch.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_HOSTING_CARD_DELETE } from '../helpers/flow-tags.js';
import { setPlatformAuth, mockPlatformClient } from '../helpers/platform-auth.js';

function futureDate(daysFromNow) {
  const d = new Date();
  d.setDate(d.getDate() + daysFromNow);
  return d.toISOString().split('T')[0];
}

const mockProject = {
  id: 1, name: 'E-commerce Platform', status: 'active', progress: 33,
  client_id: 9002, client_name: 'Client E2E', client_email: 'client@e2e-test.com',
  hosting_start_date: '2025-04-01', payment_milestones: [], has_subscription: true,
};

const mockPhases = [
  {
    id: 11, order: 1, hosting_start_date: '2025-04-01', hosting_activated_at: '2025-04-01T10:00:00Z',
    proposal: { id: 1, title: 'Fase 1 — Sitio base' },
    hosting_tiers: [
      { frequency: 'quarterly', months: 3, label: 'Trimestral', discount_percent: 10, base_monthly: 250000, monthly_equivalent: 225000, billing_amount: 675000 },
    ],
  },
];

const baseSubscription = {
  id: 1, plan: 'quarterly', plan_display: 'Trimestral',
  base_monthly_amount: '250000.00', discount_percent: 10,
  effective_monthly_amount: '225000.00', billing_amount: '675000.00',
  status: 'active', status_display: 'Activa', is_archived: false,
  next_billing_date: futureDate(60), project_id: 1, project_name: 'E-commerce Platform',
  payments: [],
};

const subWithCard = {
  ...baseSubscription,
  has_payment_source: true,
  card_brand: 'VISA', card_last_four: '4242', card_exp_month: 12, card_exp_year: 29,
};
const subWithoutCard = { ...baseSubscription, has_payment_source: false };

const json = (body) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

function setupDeleteMocks(page, { removeStatus = 200 } = {}) {
  const state = { removed: false, removeCalls: 0 };
  const routing = mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return json(mockPlatformClient);
    if (apiPath === 'accounts/projects/1/' && method === 'GET') return json(mockProject);
    if (apiPath === 'accounts/projects/' && method === 'GET') return json([mockProject]);
    if (apiPath === 'accounts/projects/1/phases/' && method === 'GET') return json(mockPhases);
    if (apiPath === 'accounts/notifications/unread-count/' && method === 'GET') return json({ unread_count: 0 });
    if (apiPath === 'accounts/projects/1/subscription/' && method === 'GET') {
      return json(state.removed ? subWithoutCard : subWithCard);
    }
    if (apiPath === 'accounts/projects/1/subscription/card/remove/' && method === 'DELETE') {
      state.removeCalls += 1;
      if (removeStatus !== 200) {
        return { status: removeStatus, contentType: 'application/json', body: JSON.stringify({ error: 'No se pudo eliminar la tarjeta.' }) };
      }
      state.removed = true;
      return json({ subscription: subWithoutCard });
    }
    return null;
  });
  return { state, routing };
}

async function openDeleteModal(page) {
  await page.goto('/platform/projects/1/payments', { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: 'Eliminar tarjeta' }).click();
  await expect(page.getByText('¿Eliminar tarjeta?')).toBeVisible();
}

test.describe('Platform Hosting Card Delete', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
  });

  test('confirming removes the stored card and restores the register state', {
    tag: [...PLATFORM_HOSTING_CARD_DELETE, '@role:client'],
  }, async ({ page }) => {
    const { state, routing } = setupDeleteMocks(page);
    await routing;
    await openDeleteModal(page);

    await page.getByRole('button', { name: 'Sí, eliminar' }).click();

    await expect(page.getByText('¿Eliminar tarjeta?')).toBeHidden();
    await expect(page.getByRole('button', { name: /Registrar tarjeta/i })).toBeVisible();
    expect(state.removeCalls).toBe(1);
  });

  test('cancelling keeps the card without calling the API', {
    tag: [...PLATFORM_HOSTING_CARD_DELETE, '@role:client'],
  }, async ({ page }) => {
    const { state, routing } = setupDeleteMocks(page);
    await routing;
    await openDeleteModal(page);

    await page.getByRole('button', { name: 'Cancelar', exact: true }).click();

    await expect(page.getByText('¿Eliminar tarjeta?')).toBeHidden();
    await expect(page.getByText('•••• 4242')).toBeVisible();
    expect(state.removeCalls).toBe(0);
  });

  test('shows the backend error inside the modal on failure', {
    tag: [...PLATFORM_HOSTING_CARD_DELETE, '@role:client'],
  }, async ({ page }) => {
    const { state, routing } = setupDeleteMocks(page, { removeStatus: 500 });
    await routing;
    await openDeleteModal(page);

    await page.getByRole('button', { name: 'Sí, eliminar' }).click();

    await expect(page.getByText('No se pudo eliminar la tarjeta.')).toBeVisible();
    await expect(page.getByText('¿Eliminar tarjeta?')).toBeVisible();
  });
});
