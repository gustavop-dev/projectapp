/**
 * E2E tests for calculator micro-feedback badge.
 *
 * Covers: toggling a calculator module shows the transient +/- price badge
 * next to the module price (green + on select, red - on deselect).
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_CALCULATOR_MICRO_FEEDBACK } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Micro Feedback Proposal',
  client_name: 'Test Client',
  status: 'sent',
  language: 'es',
  total_investment: '10000000',
  effective_total_investment: 10000000,
  currency: 'COP',
  sections: [
    {
      id: 1,
      section_type: 'greeting',
      title: 'Bienvenido',
      order: 0,
      is_enabled: true,
      content_json: { clientName: 'Test Client', inspirationalQuote: '' },
    },
    {
      id: 2,
      section_type: 'investment',
      title: 'Inversión',
      order: 1,
      is_enabled: true,
      content_json: {
        index: '2',
        title: 'Inversión',
        introText: 'Tu inversión incluye:',
        totalInvestment: '$10.000.000',
        currency: 'COP',
        whatsIncluded: [{ icon: '🎨', title: 'Diseño', description: 'UX/UI' }],
        paymentOptions: [{ label: 'Pago único', description: '$10.000.000' }],
        valueReasons: [],
      },
    },
    {
      id: 3,
      section_type: 'functional_requirements',
      title: 'Requerimientos',
      order: 2,
      is_enabled: true,
      content_json: {
        index: '3',
        title: 'Requerimientos Funcionales',
        intro: 'Detalle.',
        groups: [
          {
            id: 'views',
            icon: '👁️',
            title: 'Vistas',
            is_visible: true,
            description: 'Pantallas.',
            items: [{ icon: '🏠', name: 'Home', description: 'Landing.' }],
          },
          {
            id: 'pwa_module',
            icon: '📱',
            title: 'Progressive Web App (PWA)',
            is_visible: true,
            description: 'App instalable.',
            is_calculator_module: true,
            default_selected: false,
            price_percent: 40,
            items: [{ icon: '📲', name: 'Instalación', description: 'Como app.' }],
          },
        ],
        additionalModules: [],
      },
    },
  ],
  requirement_groups: [],
};

test.describe('Proposal Calculator Micro-Feedback', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
      localStorage.setItem(`investment_onboarding_seen_${_uuid}`, 'true');
    }, MOCK_UUID);
  });

  test('toggling a calculator module shows the transient +/- price badge', {
    tag: [...PROPOSAL_CALCULATOR_MICRO_FEEDBACK, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      return null;
    });

    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();
    await expect(page.getByText(/inversi[oó]n/i).first()).toBeVisible({ timeout: 10000 });

    const customizeBtn = page.getByRole('button', { name: /Personalizar/i });
    await expect(customizeBtn).toBeVisible({ timeout: 10000 });
    await customizeBtn.scrollIntoViewIfNeeded();
    await customizeBtn.click();
    await expect(page.getByText(/Selecciona los módulos/i)).toBeVisible({ timeout: 10000 });

    // Selecting PWA (40% of $10M): the price span gains a "+" AND the
    // transient micro-feedback badge flashes the same amount — two matches.
    // The row's border class flips border → border-2 on select, so the
    // locator anchors on the unconditional rounded-xl + transition-all pair.
    const pwaRow = page.locator('div.rounded-xl.transition-all').filter({ hasText: /Progressive Web App/ });
    const pwaTitle = pwaRow.getByText('Progressive Web App (PWA)');
    await pwaTitle.click();
    await expect(pwaRow.getByText('+$4.000.000')).toHaveCount(2, { timeout: 1400 });

    // The badge expires after ~1.5s, leaving only the price span.
    await expect(pwaRow.getByText('+$4.000.000')).toHaveCount(1, { timeout: 3000 });

    // Deselecting flashes the negative badge (unique — the price loses its +).
    await pwaTitle.click();
    await expect(pwaRow.getByText('-$4.000.000')).toBeVisible({ timeout: 1400 });
  });
});
