/**
 * E2E tests for the platform hosting stored-card setup (3DS) flow.
 *
 * @flow:platform-hosting-card-setup
 * A client with an active subscription but no stored card registers one:
 * "Registrar tarjeta" → card form → start (Wompi) → confirm → "Tarjeta registrada",
 * then the stored-card panel appears. Wompi + 3DS are fully mocked (:srcdoc iframe,
 * no live sandbox). Covers the AVAILABLE happy path and the PENDING → 3DS challenge path.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_HOSTING_CARD_SETUP } from '../helpers/flow-tags.js';
import { setPlatformAuth, mockPlatformClient } from '../helpers/platform-auth.js';

const PAYMENT_SOURCE_ID = 123;

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

const subWithoutCard = { ...baseSubscription, has_payment_source: false };
const subWithCard = {
  ...baseSubscription,
  has_payment_source: true,
  card_brand: 'VISA', card_last_four: '4242', card_exp_month: 12, card_exp_year: 29,
};

const meResponse = (user) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(user) });
const json = (body) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

/**
 * Stateful mock: the subscription GET reports no stored card until `state.registered`
 * flips true (after confirm), so the stored-card panel appears on the follow-up fetch.
 * @param {object} startResponse  body returned by POST subscription/card/ (start)
 * @param {object} [statusResponse] body returned by GET .../status/ (3DS polling path)
 */
function setupCardMocks(page, { startResponse, statusResponse } = {}) {
  const state = { registered: false };
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(mockPlatformClient);
    if (apiPath === 'accounts/projects/1/' && method === 'GET') return json(mockProject);
    if (apiPath === 'accounts/projects/' && method === 'GET') return json([mockProject]);
    if (apiPath === 'accounts/projects/1/phases/' && method === 'GET') return json(mockPhases);
    if (apiPath === 'accounts/notifications/unread-count/' && method === 'GET') return json({ unread_count: 0 });

    if (apiPath === 'accounts/projects/1/subscription/' && method === 'GET') {
      return json(state.registered ? subWithCard : subWithoutCard);
    }
    if (apiPath === 'accounts/projects/1/subscription/card/' && method === 'POST') {
      return json(startResponse);
    }
    if (apiPath === `accounts/projects/1/subscription/card/${PAYMENT_SOURCE_ID}/status/` && method === 'GET') {
      return json(statusResponse);
    }
    if (apiPath === `accounts/projects/1/subscription/card/${PAYMENT_SOURCE_ID}/confirm/` && method === 'POST') {
      state.registered = true;
      return json({ charge: { transaction_status: 'APPROVED' }, subscription: subWithCard });
    }
    return null;
  });
}

async function openCardFormAndFill(page) {
  await page.getByRole('button', { name: 'Registrar tarjeta' }).click();
  await expect(page.getByRole('heading', { name: 'Registrar tarjeta' })).toBeVisible();
  await page.getByPlaceholder('4242 4242 4242 4242').fill('4242424242424242');
  await page.getByPlaceholder('Nombre como aparece en la tarjeta').fill('CLIENT E2E');
  await page.getByPlaceholder('MM').fill('12');
  await page.getByPlaceholder('AA').fill('29');
  await page.getByPlaceholder('123').fill('123');
}

test.describe('Platform Hosting Card Setup (3DS)', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
  });

  test('AVAILABLE happy path: register card → confirm → stored-card panel appears', {
    tag: [...PLATFORM_HOSTING_CARD_SETUP, '@role:platform-client'],
  }, async ({ page }) => {
    await setupCardMocks(page, {
      startResponse: { status: 'AVAILABLE', payment_source_id: PAYMENT_SOURCE_ID, card_brand: 'VISA', card_last_four: '4242' },
    });

    await page.goto('/platform/projects/1/payments', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /hosting/i }).first().waitFor({ state: 'visible', timeout: 30000 });

    await openCardFormAndFill(page);

    await Promise.all([
      page.waitForResponse((r) => r.url().includes('/subscription/card/') && r.url().includes('/confirm/')),
      page.getByRole('button', { name: 'Guardar tarjeta' }).click(),
    ]);

    await expect(page.getByText('Tarjeta registrada')).toBeVisible();

    // Close the modal; the follow-up subscription fetch now reports the stored card.
    await page.getByRole('button', { name: 'Listo' }).click();
    await expect(page.getByText('VISA •••• 4242')).toBeVisible();
    await expect(page.getByText('Cobro automático activado')).toBeVisible();
  });

  test('PENDING path shows the 3DS challenge iframe, then completes on AVAILABLE', {
    tag: [...PLATFORM_HOSTING_CARD_SETUP, '@role:platform-client'],
  }, async ({ page }) => {
    await setupCardMocks(page, {
      startResponse: {
        status: 'PENDING',
        payment_source_id: PAYMENT_SOURCE_ID,
        card_brand: 'VISA',
        card_last_four: '4242',
        three_ds_auth: { current_step: 'CHALLENGE', three_ds_method_data: '<html><body>3DS Challenge</body></html>' },
      },
      statusResponse: { status: 'AVAILABLE', payment_source_id: PAYMENT_SOURCE_ID },
    });

    await page.goto('/platform/projects/1/payments', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /hosting/i }).first().waitFor({ state: 'visible', timeout: 30000 });

    await openCardFormAndFill(page);
    await page.getByRole('button', { name: 'Guardar tarjeta' }).click();

    // The 3DS challenge frame renders (visible for CHALLENGE step).
    await expect(page.getByTitle('Verificación 3D Secure')).toBeVisible({ timeout: 10000 });

    // After the mocked status flips to AVAILABLE, the flow confirms and finishes.
    await expect(page.getByText('Tarjeta registrada')).toBeVisible({ timeout: 15000 });
  });
});
