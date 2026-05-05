/**
 * E2E tests for the ROI Projection section.
 *
 * @flow: proposal-roi-projection
 *
 * Covers:
 * - Section renders KPI cards, scenarios block, and CTA note when enabled.
 * - Section is silently skipped when ``is_enabled=false`` (regression for
 *   the 31 existing proposals that received the row via migration backfill).
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_ROI_PROJECTION } from '../helpers/flow-tags.js';

const MOCK_UUID_ENABLED = 'd7222222-2222-4222-a222-222222222222';
const MOCK_UUID_DISABLED = 'd7333333-3333-4333-a333-333333333333';

const ROI_CONTENT = {
  index: '4',
  title: 'Proyección de retorno y beneficios',
  subtitle: 'Lo que esta inversión genera (escenario realista, COP).',
  kpis: [
    {
      icon: '👁️', value: '≈90K', label: 'Visualizaciones diarias',
      sublabel: 'mes 6, escenario realista',
      source: 'Benchmark Stickermanager 291K DAU',
    },
    {
      icon: '🏪', value: '$34M', label: 'MRR mes 6 (COP)',
      sublabel: 'Listing + CPM',
      source: '120 comerciantes activos',
    },
  ],
  scenariosTitle: 'Escenarios proyectados',
  scenarios: [
    {
      name: 'realistic', label: 'Realista', icon: '🎯',
      metrics: [
        { label: 'MAU mes 6', value: '80K' },
        { label: 'Ingresos año 1', value: '$280M', emphasis: true },
      ],
    },
  ],
  ctaNote: 'Cubre la inversión inicial antes del cierre del Mundial.',
};

function buildProposal({ uuid, roiEnabled }) {
  return {
    id: 99,
    uuid,
    title: 'ROI Test Proposal',
    client_name: 'Test Client',
    status: 'sent',
    language: 'es',
    total_investment: '8000000',
    currency: 'COP',
    sections: [
      {
        id: 1, section_type: 'greeting', title: 'Saludo',
        order: 0, is_enabled: true,
        content_json: { clientName: 'Test Client', inspirationalQuote: '' },
      },
      {
        id: 3, section_type: 'roi_projection',
        title: '📈 Proyección de retorno y beneficios',
        order: 4, is_enabled: roiEnabled,
        content_json: ROI_CONTENT,
      },
      {
        id: 4, section_type: 'investment', title: 'Inversión',
        order: 5, is_enabled: true,
        content_json: { index: '5', title: 'Inversión', introText: 'Detalle.', currency: 'COP' },
      },
    ],
    requirement_groups: [],
  };
}

function setupMock(page, uuid, proposal) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === `proposals/${uuid}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposal) };
    }
    return null;
  });
}

test.describe('Proposal ROI Projection', () => {
  test.beforeEach(async ({ page }) => {
    // Must run before any goto so the gateway sees the flag on first paint.
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('renders KPI cards, scenarios, and CTA note when enabled', {
    tag: [...PROPOSAL_ROI_PROJECTION, '@role:guest'],
  }, async ({ page }) => {
    test.setTimeout(60_000);
    const proposal = buildProposal({ uuid: MOCK_UUID_ENABLED, roiEnabled: true });
    await setupMock(page, MOCK_UUID_ENABLED, proposal);
    await page.goto(`/proposal/${MOCK_UUID_ENABLED}`);

    // ProposalViewGateway: pick "Propuesta Completa".
    await page.getByRole('heading', { name: 'Propuesta Completa' }).click();

    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });

    // greeting → roi_projection (one click in this trimmed mock).
    await nextBtn.click();

    // The component title is the canonical anchor.
    await expect(
      page.getByRole('heading', { name: 'Proyección de retorno y beneficios' }),
    ).toBeVisible({ timeout: 15000 });

    // KPI value → label pair
    await expect(page.getByText('≈90K').first()).toBeVisible();
    await expect(page.getByText('Visualizaciones diarias').first()).toBeVisible();

    // Scenario label and emphasized total
    await expect(page.getByText('Realista').first()).toBeVisible();
    await expect(page.getByText('$280M').first()).toBeVisible();

    // CTA note
    await expect(
      page.getByText('Cubre la inversión inicial antes del cierre del Mundial.'),
    ).toBeVisible();
  });

  test('section is silently skipped when is_enabled=false (legacy proposals)', {
    tag: [...PROPOSAL_ROI_PROJECTION, '@role:guest'],
  }, async ({ page }) => {
    test.setTimeout(45_000);
    const proposal = buildProposal({ uuid: MOCK_UUID_DISABLED, roiEnabled: false });
    await setupMock(page, MOCK_UUID_DISABLED, proposal);
    await page.goto(`/proposal/${MOCK_UUID_DISABLED}`);

    await page.getByRole('heading', { name: 'Propuesta Completa' }).click();

    // Wait for the gateway transition so the section panel is actually mounted.
    await expect(page.getByTestId('nav-next')).toBeVisible({ timeout: 15000 });

    // Disabled section: must not be rendered as a panel and must not be in
    // any rendered title (the section.roi-projection element itself is what
    // would mount the component if the dispatcher matched it).
    await expect(
      page.getByRole('heading', { name: 'Proyección de retorno y beneficios' }),
    ).toHaveCount(0);
    await expect(page.locator('section.roi-projection')).toHaveCount(0);
  });
});
