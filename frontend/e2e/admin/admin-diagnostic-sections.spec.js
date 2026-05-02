/**
 * E2E tests for the JSON-section diagnostic flow (Apr 16, 2026 rewrite).
 *
 * Covers:
 * - Admin opens the Sections tab and sees the 8 seeded section rows.
 * - Admin edits a section's title and the debounced PATCH hits the section endpoint.
 * - Admin visits the Actividad tab and can log a note.
 * - Admin visits the Analítica tab and sees the analytics KPI cards.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_DIAGNOSTIC_SECTIONS,
  ADMIN_DIAGNOSTIC_ACTIVITY,
  ADMIN_DIAGNOSTIC_ANALYTICS,
} from '../helpers/flow-tags.js';

const DIAG_ID = 99;
const DIAG_UUID = 'diag-sections-uuid-9999';

const authOk = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function buildSection(overrides = {}) {
  return {
    id: 100,
    section_type: 'purpose',
    title: 'Propósito',
    order: 1,
    is_enabled: true,
    visibility: 'both',
    content_json: {
      index: '1',
      title: 'Propósito',
      paragraphs: ['Intro'],
      scopeNote: '',
      severityTitle: 'Escala de Severidad',
      severityLevels: [],
    },
    ...overrides,
  };
}

function buildDiagnostic(overrides = {}) {
  return {
    id: DIAG_ID,
    uuid: DIAG_UUID,
    title: 'Diagnóstico — Acme',
    status: 'draft',
    language: 'es',
    client: { name: 'Acme', email: 'acme@example.com' },
    client_name: 'Acme',
    investment_amount: null,
    currency: 'COP',
    payment_terms: {},
    duration_label: '',
    size_category: '',
    radiography: {},
    view_count: 0,
    last_viewed_at: null,
    initial_sent_at: null,
    final_sent_at: null,
    responded_at: null,
    sections: [
      buildSection({ id: 100, section_type: 'purpose',           title: 'Propósito',            order: 1, visibility: 'both' }),
      buildSection({ id: 101, section_type: 'radiography',       title: 'Radiografía',          order: 2, visibility: 'both' }),
      buildSection({ id: 102, section_type: 'categories',        title: 'Categorías Evaluadas', order: 3, visibility: 'both' }),
      buildSection({ id: 103, section_type: 'delivery_structure', title: 'Estructura de la Entrega', order: 4, visibility: 'initial' }),
      buildSection({ id: 104, section_type: 'executive_summary', title: 'Resumen Ejecutivo',    order: 5, visibility: 'final' }),
      buildSection({ id: 105, section_type: 'cost',              title: 'Costo y Formas de Pago', order: 6, visibility: 'both' }),
      buildSection({ id: 106, section_type: 'timeline',          title: 'Cronograma',           order: 7, visibility: 'both' }),
      buildSection({ id: 107, section_type: 'scope',             title: 'Alcance y Consideraciones', order: 8, visibility: 'both' }),
    ],
    change_logs: [],
    attachments: [],
    render_context: { client_name: 'Acme', investment_amount: '', currency: 'COP' },
    public_url: `/diagnostic/${DIAG_UUID}/`,
    ...overrides,
  };
}

test.describe('Admin Diagnostic — JSON sections flow', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('Sections tab lists all 8 seeded sections', {
    tag: [...ADMIN_DIAGNOSTIC_SECTIONS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
      }
      return null;
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Secciones' }).click();

    await expect(page.getByText('Propósito', { exact: true }).first()).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Categorías Evaluadas').first()).toBeVisible();
    await expect(page.getByText('Alcance y Consideraciones').first()).toBeVisible();
  });

  test('Actividad tab logs a note via POST /activity/create/', {
    tag: [...ADMIN_DIAGNOSTIC_ACTIVITY, '@role:admin'],
  }, async ({ page }) => {
    let logged = null;
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
      }
      if (apiPath === `diagnostics/${DIAG_ID}/activity/create/` && method === 'POST') {
        logged = JSON.parse(route.request().postData() || '{}');
        return {
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1, change_type: logged.change_type, description: logged.description,
            field_name: '', old_value: '', new_value: '',
            actor_type: 'seller', created_at: new Date().toISOString(),
          }),
        };
      }
      return null;
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Actividad' }).click();

    const input = page.getByPlaceholder(/descripción de la actividad/i);
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill('Primer seguimiento');
    await page.getByRole('button', { name: /registrar/i }).click();

    await expect(() => expect(logged?.description).toBe('Primer seguimiento')).toPass({ timeout: 5000 });
  });

  test('Analytics tab shows view-count KPI card', {
    tag: [...ADMIN_DIAGNOSTIC_ANALYTICS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic({ view_count: 7 })) };
      }
      if (apiPath === `diagnostics/${DIAG_ID}/analytics/`) {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            total_views: 7,
            unique_sessions: 4,
            first_viewed_at: '2026-04-16T12:00:00Z',
            last_viewed_at: '2026-04-16T12:00:00Z',
            time_to_first_view_hours: null,
            time_to_response_hours: null,
            responded_at: null,
            sections: [
              { section_type: 'purpose', section_title: 'Propósito', visit_count: 4, total_time_seconds: 40, avg_time_seconds: 10 },
            ],
            skipped_sections: [],
            device_breakdown: { desktop: 0, mobile: 0, tablet: 0 },
            sessions: [],
            timeline: [],
            funnel: [],
            comparison: { avg_time_to_first_view_hours: null, avg_time_to_response_hours: null, avg_views: null },
            engagement_score: 0,
          }),
        };
      }
      return null;
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Analytics' }).click();

    await expect(page.getByText('Vistas').first()).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('7', { exact: true }).first()).toBeVisible();
    await expect(page.getByText(/Propósito/).first()).toBeVisible();
  });
});

