/**
 * E2E tests for the public-facing Web App Diagnostic view (JSON-section rewrite).
 *
 * Covers:
 * - Initial phase renders sections visible in `initial`/`both` and hides `final`.
 * - Final phase shows all sections including `executive_summary` (visibility=final).
 * - Sidebar index: hamburger toggle opens/closes the floating nav.
 * - Sidebar navigation changes the active section.
 * - Accept/Reject footer posts and swaps to the acceptance confirmation.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { DIAGNOSTIC_PUBLIC_VIEW, DIAGNOSTIC_PUBLIC_RESPOND } from '../helpers/flow-tags.js';

const TEST_UUID = 'dd111111-1111-1111-1111-111111111111';

function buildSection({ id, section_type, title, order, visibility = 'both', content = {} }) {
  return {
    id,
    section_type,
    title,
    order,
    is_enabled: true,
    visibility,
    content_json: { title, ...content },
  };
}

const ALL_SECTIONS = [
  buildSection({ id: 1, section_type: 'purpose', title: 'Propósito', order: 1, visibility: 'both',
    content: { index: '1', paragraphs: ['Intro'], severityLevels: [] } }),
  buildSection({ id: 2, section_type: 'radiography', title: 'Radiografía', order: 2, visibility: 'both',
    content: { index: '2', intro: 'Radiografía', includes: [], classificationRows: [] } }),
  buildSection({ id: 3, section_type: 'categories', title: 'Categorías Evaluadas', order: 3, visibility: 'both',
    content: { index: '3', categories: [] } }),
  buildSection({ id: 4, section_type: 'delivery_structure', title: 'Estructura de la Entrega', order: 4, visibility: 'initial',
    content: { index: '4', blocks: [] } }),
  buildSection({ id: 5, section_type: 'executive_summary', title: 'Resumen Ejecutivo', order: 5, visibility: 'final',
    content: { index: '5', severityCounts: { critico: 0, alto: 0, medio: 0, bajo: 0 }, narrative: '', highlights: [] } }),
  buildSection({ id: 6, section_type: 'cost', title: 'Costo y Formas de Pago', order: 6, visibility: 'both',
    content: { index: '6', paymentDescription: [] } }),
  buildSection({ id: 7, section_type: 'timeline', title: 'Cronograma', order: 7, visibility: 'both',
    content: { index: '7', distribution: [] } }),
  buildSection({ id: 8, section_type: 'scope', title: 'Alcance y Consideraciones', order: 8, visibility: 'both',
    content: { index: '8', considerations: [] } }),
];

function buildPublicDiagnostic({ phase = 'initial', ...overrides } = {}) {
  const allowed = new Set([phase, 'both']);
  const sections = ALL_SECTIONS.filter((s) => allowed.has(s.visibility));
  return {
    uuid: TEST_UUID,
    title: 'Diagnóstico — TechCorp',
    client_name: 'TechCorp',
    status: 'sent',
    language: 'es',
    initial_sent_at: '2026-04-16T10:00:00Z',
    final_sent_at: phase === 'final' ? '2026-04-16T11:00:00Z' : null,
    responded_at: null,
    investment_amount: null,
    currency: 'COP',
    duration_label: '',
    size_category: '',
    sections,
    render_context: { client_name: 'TechCorp', currency: 'COP' },
    ...overrides,
  };
}

async function mockPublicApi(page, diagnostic, { onRespond } = {}) {
  await mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === `diagnostics/public/${TEST_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(diagnostic) };
    }
    if (apiPath === `diagnostics/public/${TEST_UUID}/track/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ view_count: 1 }) };
    }
    if (apiPath === `diagnostics/public/${TEST_UUID}/track-section/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true }) };
    }
    if (apiPath === `diagnostics/public/${TEST_UUID}/respond/` && method === 'POST') {
      if (onRespond) onRespond();
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...diagnostic, status: 'accepted', responded_at: '2026-04-16T12:00:00Z' }),
      };
    }
    return null;
  });
}

test.describe('Diagnostic Public View — JSON sections', () => {
  test.setTimeout(60_000);

  test('initial phase renders initial/both sections and hides executive_summary', {
    tag: [...DIAGNOSTIC_PUBLIC_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const diagnostic = buildPublicDiagnostic({ phase: 'initial' });
    await mockPublicApi(page, diagnostic);

    await page.goto(`/diagnostic/${TEST_UUID}/`, { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('diagnostic-index-toggle')).toBeVisible({ timeout: 15000 });

    // Open sidebar to inspect the section list.
    await page.getByTestId('diagnostic-index-toggle').click();
    await expect(page.getByText('Índice')).toBeVisible();

    // Initial-only and both-visibility sections appear in the sidebar.
    await expect(page.getByRole('button', { name: /Propósito/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Estructura de la Entrega/ })).toBeVisible();
    // Final-only section must NOT be in the DOM at all.
    await expect(page.getByRole('button', { name: /Resumen Ejecutivo/ })).toHaveCount(0);
  });

  test('final phase exposes the executive_summary section', {
    tag: [...DIAGNOSTIC_PUBLIC_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const diagnostic = buildPublicDiagnostic({ phase: 'final' });
    await mockPublicApi(page, diagnostic);

    await page.goto(`/diagnostic/${TEST_UUID}/`, { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('diagnostic-index-toggle')).toBeVisible({ timeout: 15000 });

    // Open sidebar to inspect the section list.
    await page.getByTestId('diagnostic-index-toggle').click();
    await expect(page.getByRole('button', { name: /Resumen Ejecutivo/ })).toBeVisible();
    // delivery_structure is initial-only; final phase should not include it.
    await expect(page.getByRole('button', { name: /Estructura de la Entrega/ })).toHaveCount(0);
  });

  test('sidebar toggle opens and closes the index panel', {
    tag: [...DIAGNOSTIC_PUBLIC_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const diagnostic = buildPublicDiagnostic({ phase: 'initial' });
    await mockPublicApi(page, diagnostic);

    await page.goto(`/diagnostic/${TEST_UUID}/`, { waitUntil: 'domcontentloaded' });
    const toggle = page.getByTestId('diagnostic-index-toggle');
    await expect(toggle).toBeVisible({ timeout: 15000 });

    // Sidebar is closed — "Índice" label not in viewport.
    await expect(page.getByText('Índice')).not.toBeInViewport();

    // Open sidebar.
    await toggle.click();
    await expect(page.getByText('Índice')).toBeVisible();

    // Close sidebar by clicking the backdrop overlay (matches UX — toggle is
    // behind the backdrop when open, so real users dismiss via backdrop click).
    await toggle.click({ force: true });
    await expect(page.getByText('Índice')).not.toBeInViewport();
  });

  test('clicking a sidebar item navigates to that section', {
    tag: [...DIAGNOSTIC_PUBLIC_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const diagnostic = buildPublicDiagnostic({ phase: 'initial' });
    await mockPublicApi(page, diagnostic);

    await page.goto(`/diagnostic/${TEST_UUID}/`, { waitUntil: 'domcontentloaded' });
    await expect(page.getByText('Sección 1 de', { exact: false })).toBeVisible({ timeout: 15000 });

    // Open sidebar and click the third section.
    await page.getByTestId('diagnostic-index-toggle').click();
    await expect(page.getByText('Índice')).toBeVisible();
    await page.getByRole('button', { name: /Categorías Evaluadas/ }).click();

    // After click the sidebar closes and section counter advances.
    await expect(page.getByText('Sección 3 de', { exact: false })).toBeVisible();
  });

  test('clicking "Aceptar propuesta" POSTs accept decision and shows acceptance footer', {
    tag: [...DIAGNOSTIC_PUBLIC_RESPOND, '@role:guest'],
  }, async ({ page }) => {
    const diagnostic = buildPublicDiagnostic({ phase: 'final' });
    let respondCalled = false;
    await mockPublicApi(page, diagnostic, { onRespond: () => { respondCalled = true; } });

    await page.goto(`/diagnostic/${TEST_UUID}/`, { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('button', { name: /aceptar propuesta/i })).toBeVisible({ timeout: 15000 });
    await page.getByRole('button', { name: /aceptar propuesta/i }).click();

    await expect(() => expect(respondCalled).toBe(true)).toPass({ timeout: 5000 });
    await expect(page.getByText(/Confirmamos tu aceptación/i)).toBeVisible({ timeout: 5000 });
  });

  test('clicking next advances the active section', {
    tag: [...DIAGNOSTIC_PUBLIC_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const diagnostic = buildPublicDiagnostic({ phase: 'final' });
    await mockPublicApi(page, diagnostic);

    await page.goto(`/diagnostic/${TEST_UUID}/`, { waitUntil: 'domcontentloaded' });
    await expect(page.getByText('Sección 1 de', { exact: false })).toBeVisible({ timeout: 15000 });
    await page.getByRole('button', { name: /siguiente/i }).click();
    await expect(page.getByText('Sección 2 de', { exact: false })).toBeVisible();
  });
});
