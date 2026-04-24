/**
 * E2E tests for proposal value_added_modules section.
 *
 * Covers: card grid renders resolved modules from functional_requirements,
 * "Gratis" free badge per card, footer note visibility, default title fallback.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_VALUE_ADDED_MODULES } from '../helpers/flow-tags.js';

const MOCK_UUID = 'eb111111-1111-1111-1111-111111111111';

const FR_GROUPS = [
  {
    id: 'maintenance',
    title: 'Mantenimiento mensual',
    icon: '🔧',
    description: 'Soporte técnico incluido.',
    price_percent: 0,
    selected: true,
  },
  {
    id: 'training',
    title: 'Capacitación del equipo',
    icon: '📚',
    description: 'Sesiones de onboarding.',
    price_percent: 0,
    selected: true,
  },
];

function makeMockProposal(overrides = {}) {
  return {
    id: 1,
    uuid: MOCK_UUID,
    title: 'Value Added Modules Proposal',
    client_name: 'Test Client',
    status: 'sent',
    language: 'es',
    total_investment: '10000000',
    currency: 'COP',
    sections: [
      {
        id: 1,
        section_type: 'greeting',
        title: 'Bienvenido',
        order: 0,
        is_enabled: true,
        content_json: { clientName: 'Test Client', inspirationalQuote: 'Hola.' },
      },
      {
        id: 2,
        section_type: 'value_added_modules',
        title: 'Módulos incluidos',
        order: 1,
        is_enabled: true,
        content_json: {
          title: 'Beneficios incluidos sin costo',
          intro: 'Como parte de tu proyecto, incluimos estos módulos de regalo.',
          module_ids: ['maintenance', 'training'],
          justifications: {
            maintenance: 'Queremos que tu plataforma siempre funcione.',
            training: 'Tu equipo debe aprovechar al máximo la herramienta.',
          },
          footer_note: 'Todo incluido en tu inversión inicial.',
        },
        ...overrides,
      },
      {
        id: 3,
        section_type: 'functional_requirements',
        title: 'Requerimientos',
        order: 2,
        is_enabled: true,
        content_json: { groups: FR_GROUPS },
      },
    ],
    requirement_groups: [],
    ...overrides,
  };
}

function setupMock(page, proposal = makeMockProposal()) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposal) };
    }
    return null;
  });
}

test.describe('Proposal Value Added Modules', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('renders module cards with titles and free badge', {
    tag: [...PROPOSAL_VALUE_ADDED_MODULES, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('domcontentloaded');

    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();
    await page.waitForLoadState('domcontentloaded');

    // Section title
    await expect(page.getByRole('heading', { name: 'Beneficios incluidos sin costo' })).toBeVisible({ timeout: 10000 });

    // Both module cards are rendered via data-testid
    await expect(page.getByTestId('value-added-card-maintenance')).toBeVisible();
    await expect(page.getByTestId('value-added-card-training')).toBeVisible();

    // Card titles from functional_requirements groups
    await expect(page.getByText('Mantenimiento mensual').first()).toBeVisible();
    await expect(page.getByText('Capacitación del equipo').first()).toBeVisible();

    // Each card shows "Gratis" badge (free badge per card)
    const freeBadges = page.getByText('Gratis');
    await expect(freeBadges.first()).toBeVisible();
  });

  test('renders justification text for each card', {
    tag: [...PROPOSAL_VALUE_ADDED_MODULES, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('domcontentloaded');

    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByText('Queremos que tu plataforma siempre funcione.').first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Tu equipo debe aprovechar al máximo la herramienta.').first()).toBeVisible();
  });

  test('renders footer note when provided', {
    tag: [...PROPOSAL_VALUE_ADDED_MODULES, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('domcontentloaded');

    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByText('Todo incluido en tu inversión inicial.').first()).toBeVisible({ timeout: 10000 });
  });

  test('falls back to default title when content has no title', {
    tag: [...PROPOSAL_VALUE_ADDED_MODULES, '@role:client'],
  }, async ({ page }) => {
    const proposalNoTitle = makeMockProposal();
    delete proposalNoTitle.sections[1].content_json.title;
    await setupMock(page, proposalNoTitle);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('domcontentloaded');

    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByRole('heading', { name: 'Incluido sin costo adicional' })).toBeVisible({ timeout: 10000 });
  });
});
