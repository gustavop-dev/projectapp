/**
 * E2E tests for admin diagnostic analytics tab (full-parity rewrite, Apr 20, 2026).
 *
 * Covers: CSV export button, engagement score (high/moderate/low levels),
 * summary KPI cards, funnel section, device breakdown section.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_DIAGNOSTIC_ANALYTICS,
  ADMIN_DIAGNOSTIC_ENGAGEMENT_SCORE,
} from '../helpers/flow-tags.js';

const DIAG_ID = 42;
const DIAG_UUID = 'diag-analytics-uuid-0042';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function buildDiagnostic(overrides = {}) {
  return {
    id: DIAG_ID,
    uuid: DIAG_UUID,
    title: 'Diagnóstico — Acme',
    status: 'sent',
    language: 'es',
    client: { name: 'Acme', email: 'acme@example.com' },
    client_name: 'Acme',
    investment_amount: null,
    currency: 'COP',
    payment_terms: {},
    duration_label: '',
    size_category: '',
    radiography: {},
    view_count: 5,
    last_viewed_at: '2026-04-20T10:00:00Z',
    initial_sent_at: '2026-04-15T08:00:00Z',
    final_sent_at: null,
    responded_at: null,
    sections: [],
    change_logs: [],
    attachments: [],
    render_context: { client_name: 'Acme', investment_amount: '', currency: 'COP' },
    public_url: `/diagnostic/${DIAG_UUID}/`,
    ...overrides,
  };
}

const baseAnalytics = {
  total_views: 5,
  unique_sessions: 3,
  first_viewed_at: '2026-04-16T10:00:00Z',
  last_viewed_at: '2026-04-20T10:00:00Z',
  time_to_first_view_hours: 26.0,
  time_to_response_hours: null,
  responded_at: null,
  sections: [
    { section_type: 'purpose', section_title: 'Propósito', visit_count: 3, total_time_seconds: 45.0, avg_time_seconds: 15.0 },
    { section_type: 'cost', section_title: 'Costo', visit_count: 2, total_time_seconds: 80.0, avg_time_seconds: 40.0 },
  ],
  skipped_sections: [{ section_type: 'scope', section_title: 'Alcance y Consideraciones' }],
  device_breakdown: { desktop: 2, mobile: 1, tablet: 0 },
  sessions: [
    { session_id: 'sess-abc', ip_address: '192.168.1.1', viewed_at: '2026-04-16T10:00:00Z', sections_viewed: ['purpose'], total_time_seconds: 45.0 },
  ],
  timeline: [],
  funnel: [
    { section_type: 'purpose', section_title: 'Propósito', reached_count: 3, drop_off_percent: 0.0 },
    { section_type: 'cost', section_title: 'Costo', reached_count: 2, drop_off_percent: 33.3 },
  ],
  comparison: { avg_time_to_first_view_hours: 20.0, avg_time_to_response_hours: null, avg_views: 4.0 },
  engagement_score: 55,
};

function setupMock(page, analyticsOverride = {}) {
  const analytics = { ...baseAnalytics, ...analyticsOverride };
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
    }
    if (apiPath === `diagnostics/${DIAG_ID}/analytics/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(analytics) };
    }
    return null;
  });
}

test.describe('Admin Diagnostic Analytics', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('analytics tab shows CSV button and summary KPI cards', {
    tag: [...ADMIN_DIAGNOSTIC_ANALYTICS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Analytics' }).click();

    await expect(page.getByRole('button', { name: 'Exportar CSV' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Vistas').first()).toBeVisible();
    await expect(page.getByText('Sesiones').first()).toBeVisible();
    await expect(page.getByText('5', { exact: true }).first()).toBeVisible();
  });

  test('analytics tab shows engagement score with high-engagement label', {
    tag: [...ADMIN_DIAGNOSTIC_ENGAGEMENT_SCORE, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page, { engagement_score: 75 });
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Analytics' }).click();

    await expect(page.getByText('Engagement Score')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('75', { exact: true })).toBeVisible();
    await expect(page.getByText(/Alto engagement/)).toBeVisible();
  });

  test('analytics tab shows low-engagement warning when score is below 40', {
    tag: [...ADMIN_DIAGNOSTIC_ENGAGEMENT_SCORE, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page, { engagement_score: 18 });
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Analytics' }).click();

    await expect(page.getByText('Engagement Score')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/Bajo engagement/)).toBeVisible();
  });

  test('analytics tab renders funnel rows when funnel data is present', {
    tag: [...ADMIN_DIAGNOSTIC_ANALYTICS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Analytics' }).click();

    // Funnel section renders with section names from the funnel array
    await expect(page.getByText('Propósito').first()).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Costo').first()).toBeVisible();
  });

  test('analytics tab renders device breakdown section', {
    tag: [...ADMIN_DIAGNOSTIC_ANALYTICS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Analytics' }).click();

    await expect(page.getByText('Dispositivos')).toBeVisible({ timeout: 15000 });
  });
});
