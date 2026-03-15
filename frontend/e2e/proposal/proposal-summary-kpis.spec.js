/**
 * E2E tests for Proposal Summary cards.
 *
 * @flow: proposal-summary-kpis
 *
 * Covers: standard summary cards render correctly.
 * Note: KPI highlight cards (+40%, 3x, -60%) were removed from ProposalSummary.
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

test.describe('Proposal Summary Cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('renders standard summary cards', {
    tag: [...PROPOSAL_SUMMARY_KPIS, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);

    // Gateway should show — pick detailed view
    await page.getByText('Propuesta Completa').click();

    // Navigate to summary section (second section)
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();

    // Standard cards should render
    await expect(page.getByText('Inversión Total')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Inversión Total').locator('..').getByText('$8.000.000 COP')).toBeVisible();
  });
});
