/**
 * E2E tests for the three client-facing affordances on the public diagnostic page:
 * PDF download button, share modal, and dark mode toggle.
 *
 * @flow:diagnostic-public-pdf-download
 * @flow:diagnostic-public-share
 * @flow:diagnostic-public-dark-mode
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import {
  DIAGNOSTIC_PUBLIC_PDF_DOWNLOAD,
  DIAGNOSTIC_PUBLIC_SHARE,
  DIAGNOSTIC_PUBLIC_DARK_MODE,
} from '../helpers/flow-tags.js';

const TEST_UUID = 'de111111-1111-1111-1111-111111111111';

function buildSection(overrides = {}) {
  return {
    id: overrides.id ?? 1,
    section_type: overrides.section_type ?? 'purpose',
    title: overrides.title ?? 'Propósito',
    order: overrides.order ?? 1,
    is_enabled: true,
    visibility: 'both',
    content_json: { title: overrides.title ?? 'Propósito', index: '1', paragraphs: [] },
  };
}

const MOCK_DIAGNOSTIC = {
  uuid: TEST_UUID,
  title: 'Diagnóstico — AffordanceCo',
  client_name: 'AffordanceCo',
  status: 'sent',
  language: 'es',
  initial_sent_at: '2026-04-20T10:00:00Z',
  final_sent_at: null,
  responded_at: null,
  investment_amount: null,
  currency: 'COP',
  duration_label: '5 días',
  size_category: '',
  sections: [buildSection({ id: 1 })],
  render_context: { client_name: 'AffordanceCo', currency: 'COP' },
};

async function setupMock(page, { pdfStatus = 200, pdfBody = '%PDF-1.4 test' } = {}) {
  await mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === `diagnostics/public/${TEST_UUID}/` && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_DIAGNOSTIC) };
    }
    if (apiPath === `diagnostics/public/${TEST_UUID}/track/` && method === 'POST') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ view_count: 1 }) };
    }
    if (apiPath === `diagnostics/public/${TEST_UUID}/pdf/` && method === 'GET') {
      return { status: pdfStatus, contentType: 'application/pdf', body: pdfBody };
    }
    return null;
  });
}

async function loadDiagnosticPage(page) {
  await page.goto(`/diagnostic/${TEST_UUID}/`, { waitUntil: 'domcontentloaded' });
  await expect(page.getByTestId('diagnostic-theme-toggle')).toBeVisible({ timeout: 15000 });
}

// ── PDF Download ──────────────────────────────────────────────────────────────

test.describe('Diagnostic Public — PDF Download', () => {
  test.setTimeout(60_000);

  test('clicking Descargar PDF triggers a successful PDF request', {
    tag: [...DIAGNOSTIC_PUBLIC_PDF_DOWNLOAD, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);

    const pdfFetch = page.waitForResponse(
      (res) =>
        res.url().includes(`/api/diagnostics/public/${TEST_UUID}/pdf/`) &&
        res.request().method() === 'GET',
    );

    await loadDiagnosticPage(page);

    const pdfBtn = page.getByTestId('download-diagnostic-pdf-btn');
    await expect(pdfBtn).toBeVisible({ timeout: 10000 });
    await pdfBtn.click();

    const res = await pdfFetch;
    expect(res.status()).toBe(200);
    const ct = res.headers()['content-type'] ?? '';
    expect(ct).toMatch(/pdf/i);
  });

  test('PDF button shows spinner while generating and re-enables after', {
    tag: [...DIAGNOSTIC_PUBLIC_PDF_DOWNLOAD, '@role:guest'],
  }, async ({ page }) => {
    let resolvePdf;
    const pdfReady = new Promise((r) => { resolvePdf = r; });

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === `diagnostics/public/${TEST_UUID}/` && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_DIAGNOSTIC) };
      }
      if (apiPath === `diagnostics/public/${TEST_UUID}/track/` && method === 'POST') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ view_count: 1 }) };
      }
      if (apiPath === `diagnostics/public/${TEST_UUID}/pdf/` && method === 'GET') {
        // Block until the test signals readiness so we can assert the disabled state.
        await pdfReady;
        return { status: 200, contentType: 'application/pdf', body: '%PDF-1.4' };
      }
      return null;
    });

    await loadDiagnosticPage(page);

    const pdfBtn = page.getByTestId('download-diagnostic-pdf-btn');
    await expect(pdfBtn).toBeVisible({ timeout: 10000 });
    await pdfBtn.click();

    // While the fetch is pending the button should be disabled.
    await expect(pdfBtn).toBeDisabled();

    resolvePdf();

    // After the fetch completes the button re-enables.
    await expect(pdfBtn).toBeEnabled({ timeout: 5000 });
  });
});

// ── Share Modal ───────────────────────────────────────────────────────────────

test.describe('Diagnostic Public — Share Button', () => {
  test.setTimeout(60_000);

  test('share button is visible on the public diagnostic page', {
    tag: [...DIAGNOSTIC_PUBLIC_SHARE, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await loadDiagnosticPage(page);

    await expect(page.getByTestId('share-diagnostic-btn')).toBeVisible({ timeout: 10000 });
  });

  test('clicking share button opens modal with copy link option', {
    tag: [...DIAGNOSTIC_PUBLIC_SHARE, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await loadDiagnosticPage(page);

    const shareBtn = page.getByTestId('share-diagnostic-btn');
    await expect(shareBtn).toBeVisible({ timeout: 10000 });
    await shareBtn.click();

    await expect(page.getByText('Compartir diagnóstico')).toBeVisible();
    await expect(page.getByText('Copiar enlace')).toBeVisible();
  });
});

// ── Dark Mode Toggle ──────────────────────────────────────────────────────────

test.describe('Diagnostic Public — Dark Mode Toggle', () => {
  test.setTimeout(60_000);

  test('dark mode toggle switches the wrapper to data-theme="dark"', {
    tag: [...DIAGNOSTIC_PUBLIC_DARK_MODE, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await loadDiagnosticPage(page);

    const toggle = page.getByTestId('diagnostic-theme-toggle');
    await expect(toggle).toBeVisible({ timeout: 10000 });

    const wrapper = page.locator('.diagnostic-public');
    await expect(wrapper).not.toHaveClass(/(^|\s)dark(\s|$)/);

    await toggle.click();
    await expect(wrapper).toHaveClass(/(^|\s)dark(\s|$)/);
  });

  test('dark mode preference persists in localStorage after toggle', {
    tag: [...DIAGNOSTIC_PUBLIC_DARK_MODE, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await loadDiagnosticPage(page);

    await page.getByTestId('diagnostic-theme-toggle').click();

    const stored = await page.evaluate(() => localStorage.getItem('diagnostic_theme'));
    expect(stored).toBe('dark');
  });

  test('page loads in dark mode when localStorage is pre-set', {
    tag: [...DIAGNOSTIC_PUBLIC_DARK_MODE, '@role:guest'],
  }, async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('diagnostic_theme', 'dark');
    });
    await setupMock(page);
    await loadDiagnosticPage(page);

    const wrapper = page.locator('.diagnostic-public');
    await expect(wrapper).toHaveClass(/(^|\s)dark(\s|$)/, { timeout: 10000 });
  });
});
