/**
 * E2E tests for platform hosting subscription flow.
 *
 * @flow:platform-hosting-subscription
 * Covers: hosting plan selection (client), subscription activation, payment via mocked Wompi,
 *         Netflix-style active state, admin read-only view, unified payments page.
 *         Wompi payment endpoints are mocked — no real transactions.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_HOSTING_SUBSCRIPTION } from '../helpers/flow-tags.js';
import {
  setPlatformAuth,
  mockPlatformAdmin,
  mockPlatformClient,
} from '../helpers/platform-auth.js';

const mockProject = {
  id: 1, name: 'E-commerce Platform', status: 'active', progress: 33,
  client_id: 9002, client_name: 'Client E2E', client_email: 'client@e2e-test.com',
  client_company: 'ACME Corp', proposal_id: 1, proposal_title: 'Propuesta E-commerce',
  start_date: '2025-01-01', estimated_end_date: '2025-06-30',
  hosting_start_date: '2025-04-01',
  hosting_tiers: [
    { frequency: 'semiannual', months: 6, label: 'Semestral', badge: 'Mejor precio', discount_percent: 20, base_monthly: 250000, effective_monthly: 200000, billing_amount: 1200000, currency: 'COP' },
    { frequency: 'quarterly', months: 3, label: 'Trimestral', badge: '10% dcto', discount_percent: 10, base_monthly: 250000, effective_monthly: 225000, billing_amount: 675000, currency: 'COP' },
    { frequency: 'monthly', months: 1, label: 'Mensual', badge: '', discount_percent: 0, base_monthly: 250000, effective_monthly: 250000, billing_amount: 250000, currency: 'COP' },
  ],
  payment_milestones: [],
  has_subscription: false,
};

const mockSubscription = {
  id: 1, plan: 'quarterly', plan_display: 'Trimestral',
  base_monthly_amount: '250000.00', discount_percent: 10,
  effective_monthly_amount: '225000.00', billing_amount: '675000.00',
  status: 'active', status_display: 'Activa',
  start_date: '2025-04-01', next_billing_date: '2025-07-01',
  project_id: 1, project_name: 'E-commerce Platform',
  payments: [
    {
      id: 1, amount: '675000.00', description: 'Hosting Trimestral',
      billing_period_start: '2025-04-01', billing_period_end: '2025-06-30',
      due_date: '2025-04-01', status: 'paid', paid_at: '2025-04-01T12:00:00Z',
      wompi_payment_link_url: null, project_id: 1, project_name: 'E-commerce Platform',
    },
    {
      id: 2, amount: '675000.00', description: 'Hosting Trimestral',
      billing_period_start: '2025-07-01', billing_period_end: '2025-09-30',
      due_date: '2025-07-01', status: 'pending', paid_at: null,
      wompi_payment_link_url: null, project_id: 1, project_name: 'E-commerce Platform',
    },
  ],
  created_at: '2025-04-01T10:00:00Z', updated_at: '2025-04-01T10:00:00Z',
};

const meResponse = (user) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(user) });

function setupMocksNoSubscription(page, { user }) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/projects/1/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProject) };
    }
    if (apiPath === 'accounts/projects/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([mockProject]) };
    }
    if (apiPath === 'accounts/projects/1/subscription/' && method === 'GET') {
      return { status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'No hay suscripción.' }) };
    }
    if (apiPath === 'accounts/projects/1/subscription/' && method === 'POST') {
      return { status: 201, contentType: 'application/json', body: JSON.stringify(mockSubscription) };
    }
    if (apiPath === 'accounts/notifications/unread-count/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 0 }) };
    }
    return null;
  });
}

function setupMocksWithSubscription(page, { user }) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/projects/1/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockProject, has_subscription: true }) };
    }
    if (apiPath === 'accounts/projects/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([{ ...mockProject, has_subscription: true }]) };
    }
    if (apiPath === 'accounts/projects/1/subscription/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSubscription) };
    }
    if (apiPath === 'accounts/subscriptions/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([{ ...mockSubscription, pending_payments: 0 }]) };
    }
    if (apiPath === 'accounts/notifications/unread-count/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 0 }) };
    }
    return null;
  });
}

test.describe('Platform Hosting Subscription — Client selects plan', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
  });

  test('client sees hosting tier cards when no subscription exists', {
    tag: [...PLATFORM_HOSTING_SUBSCRIPTION, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocksNoSubscription(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/payments', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /suscripción/i }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('Elige tu plan de hosting')).toBeVisible();
    await expect(page.getByText('Semestral')).toBeVisible();
    await expect(page.getByText('Trimestral')).toBeVisible();
    await expect(page.getByText('Mensual')).toBeVisible();
    await expect(page.getByText('Mejor precio')).toBeVisible();
  });

  test('client can select a plan and activate subscription', {
    tag: [...PLATFORM_HOSTING_SUBSCRIPTION, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocksNoSubscription(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/payments', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /suscripción/i }).waitFor({ state: 'visible', timeout: 30000 });

    await page.getByText('Trimestral').click();
    const activateBtn = page.getByRole('button', { name: /activar plan/i });
    await expect(activateBtn).toBeEnabled();
    await activateBtn.click();
  });

  test('active subscription shows Netflix-style up-to-date card', {
    tag: [...PLATFORM_HOSTING_SUBSCRIPTION, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocksWithSubscription(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/payments', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /suscripción/i }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('Suscripción activa')).toBeVisible();
    await expect(page.getByText(/se renueva automáticamente/i)).toBeVisible();
  });
});

test.describe('Platform Hosting Subscription — Admin view', () => {
  test.setTimeout(60_000);

  test('admin sees waiting message when no subscription exists', {
    tag: [...PLATFORM_HOSTING_SUBSCRIPTION, '@role:platform-admin'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
    await setupMocksNoSubscription(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/payments', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /suscripción/i }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText(/no ha activado/i)).toBeVisible();
    await expect(page.getByText('Elige tu plan')).not.toBeVisible();
  });

  test('admin sees subscription status when active', {
    tag: [...PLATFORM_HOSTING_SUBSCRIPTION, '@role:platform-admin'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
    await setupMocksWithSubscription(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/payments', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /suscripción/i }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('Suscripción activa')).toBeVisible();
  });
});
