/**
 * E2E tests for Proposal Summary KPI cards.
 *
 * @flow: proposal-summary-kpis
 *
 * Covers: KPI cards render with value, label, source citation;
 * standard summary cards still render below KPIs.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_SUMMARY_KPIS } from '../helpers/flow-tags.js';

const MOCK_UUID = 'kpi-uuid-1234-5678-abcdef123456';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'KPI Proposal',
  client_name: 'KPI Client',
  status: 'sent',
  language: 'es',
  total_investment: '8000000',
  currency: 'COP',
  sections: [
    {
      id: 1,
      section_type: 'greeting',
      title: 'Bienvenido',
      order: 0,
      is_enabled: true,
      content_json: { clientName: 'KPI Client', inspirationalQuote: '' },
    },
    {
      id: 2,
      section_type: 'proposal_summary',
      title: 'Resumen',
      order: 1,
      is_enabled: true,
      content_json: {
        index: '1',
        title: 'Resumen de la Propuesta',
        subtitle: 'Detalles clave de esta propuesta:',
        kpis: [
          { value: '+40%', label: 'Incremento esperado en conversión web', source: 'HubSpot 2024' },
          { value: '3x', label: 'Retorno estimado de inversión a 12 meses', source: 'Análisis interno' },
          { value: '-60%', label: 'Reducción en tiempo de gestión manual', source: 'McKinsey Digital 2023' },
        ],
        cards: [
          { icon: '💰', title: 'Inversión Total', description: '$8.000.000 COP', source: 'static' },
          { icon: '⏳', title: 'Duración', description: '4 semanas', source: 'static' },
        ],
      },
    },
  ],
  requirement_groups: [],
};

function setupMock(page) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
    }
    return null;
  });
}

test.describe('@flow: proposal-summary-kpis — Proposal Summary KPI Cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('renders KPI cards with value, label, and source', {
    tag: [...PROPOSAL_SUMMARY_KPIS, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.proposal-wrapper')).toBeVisible({ timeout: 15000 });

    // Navigate to summary section (second section)
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 5000 });
    await nextBtn.click();

    // KPI values should be visible
    await expect(page.getByText('+40%')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('3x')).toBeVisible();
    await expect(page.getByText('-60%')).toBeVisible();
  });

  test('renders KPI labels and sources', {
    tag: [...PROPOSAL_SUMMARY_KPIS, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.proposal-wrapper')).toBeVisible({ timeout: 15000 });

    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 5000 });
    await nextBtn.click();

    // Labels
    await expect(page.getByText(/Incremento esperado en conversión web/)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/Retorno estimado de inversión/)).toBeVisible();

    // Sources
    await expect(page.getByText('HubSpot 2024')).toBeVisible();
    await expect(page.getByText('McKinsey Digital 2023')).toBeVisible();
  });

  test('renders standard summary cards below KPIs', {
    tag: [...PROPOSAL_SUMMARY_KPIS, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.proposal-wrapper')).toBeVisible({ timeout: 15000 });

    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 5000 });
    await nextBtn.click();

    // Standard cards should still render
    await expect(page.getByText('Inversión Total')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('$8.000.000 COP')).toBeVisible();
  });
});
