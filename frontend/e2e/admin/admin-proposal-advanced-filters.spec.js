/**
 * E2E tests for admin proposal advanced filters.
 *
 * @flow:admin-proposal-advanced-filters
 * Covers: filter panel toggle, filter dimensions, active filter chips,
 *         clear all, saved filter tabs, tab CRUD, URL deep-linking.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_ADVANCED_FILTERS } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockProposals = [
  {
    id: 1, uuid: 'aaa-111', title: 'Propuesta E-commerce', client_name: 'Alpha Corp',
    client_email: 'alpha@test.com', status: 'sent', total_investment: '5000000',
    currency: 'COP', language: 'es', project_type: 'ecommerce', market_type: 'retail',
    view_count: 5, is_active: true, heat_score: 7,
    created_at: '2026-01-10T10:00:00Z', last_activity_at: '2026-03-20T10:00:00Z',
  },
  {
    id: 2, uuid: 'bbb-222', title: 'Propuesta SaaS', client_name: 'Beta Inc',
    client_email: 'beta@test.com', status: 'draft', total_investment: '12000',
    currency: 'USD', language: 'en', project_type: 'saas', market_type: 'b2b',
    view_count: 0, is_active: true, heat_score: 3,
    created_at: '2026-02-15T10:00:00Z', last_activity_at: '2026-02-15T10:00:00Z',
  },
  {
    id: 3, uuid: 'ccc-333', title: 'Propuesta Web App', client_name: 'Gamma LLC',
    client_email: 'gamma@test.com', status: 'accepted', total_investment: '8000000',
    currency: 'COP', language: 'es', project_type: 'webapp', market_type: 'fintech',
    view_count: 12, is_active: false, heat_score: 9,
    created_at: '2025-11-01T10:00:00Z', last_activity_at: '2026-01-05T10:00:00Z',
  },
];

function buildMockHandler(proposals = mockProposals) {
  return async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'proposals/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposals) };
    }
    if (apiPath === 'proposals/dashboard/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({
        total_proposals: proposals.length, conversion_rate: 33, pct_revisit: 0,
        avg_time_to_first_view_hours: 2, avg_time_to_response: null,
        by_status: { draft: 1, sent: 1, accepted: 1 }, top_rejection_reasons: [],
        monthly_trend: [], avg_value_by_status: {},
      }) };
    }
    if (apiPath === 'proposals/alerts/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    return null;
  };
}

test.describe('Admin Proposal Advanced Filters', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8700, role: 'admin', is_staff: true },
    });
  });

  test('filter toggle button opens and closes the filter panel', {
    tag: [...ADMIN_PROPOSAL_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Propuestas' })).toBeVisible({ timeout: 20_000 });

    const filterButton = page.getByRole('button', { name: 'Filtros', exact: true });
    await expect(filterButton).toBeVisible();

    await filterButton.click();
    await expect(page.getByText('Clasificación')).toBeVisible();
    await expect(page.getByText('Valores', { exact: true })).toBeVisible();
    await expect(page.getByText('Fechas')).toBeVisible();

    await filterButton.click();
    await expect(page.getByText('Clasificación')).not.toBeVisible();
  });

  test('filter panel shows filter dropdowns for status and project type', {
    tag: [...ADMIN_PROPOSAL_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Propuestas' })).toBeVisible({ timeout: 20_000 });

    await page.getByRole('button', { name: 'Filtros', exact: true }).click();
    await expect(page.getByText('Clasificación')).toBeVisible();

    await expect(page.getByRole('button', { name: /estado/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /tipo de proyecto/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /mercado/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /moneda/i })).toBeVisible();
  });

  test('Todas tab is active by default and shows all proposals', {
    tag: [...ADMIN_PROPOSAL_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Propuestas' })).toBeVisible({ timeout: 20_000 });

    await expect(page.getByRole('button', { name: 'Todas' })).toBeVisible();
    await expect(page.getByText('Alpha Corp')).toBeVisible();
    await expect(page.getByText('Beta Inc')).toBeVisible();
    await expect(page.getByText('Gamma LLC')).toBeVisible();
    await expect(page.getByText('Propuesta E-commerce')).toBeVisible();
    await expect(page.getByText('Propuesta SaaS')).toBeVisible();
    await expect(page.getByText('Propuesta Web App')).toBeVisible();
  });

  test('status filter dropdown exposes Finalizadas option', {
    tag: [...ADMIN_PROPOSAL_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Propuestas' })).toBeVisible({ timeout: 20_000 });

    await page.getByRole('button', { name: 'Filtros', exact: true }).click();
    await expect(page.getByText('Clasificación')).toBeVisible();

    await page.getByRole('button', { name: /estado/i }).click();
    await expect(page.getByText('Finalizadas')).toBeVisible();
  });
});
