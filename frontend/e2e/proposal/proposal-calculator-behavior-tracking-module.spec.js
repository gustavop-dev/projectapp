/**
 * E2E tests for the behavior_tracking_module calculator add-on in the
 * investment calculator.
 *
 * @flow: proposal-calculator-behavior-tracking-module
 * Covers: the module appears under the "Rastreo de Comportamiento" group
 * label, is unselected by default, and toggling it on adds exactly
 * base*price_percent to the modal footer total.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_CALCULATOR_BEHAVIOR_TRACKING_MODULE } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-b3ba710a7ac1';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Behavior Tracking Module Proposal',
  client_name: 'Behavior Tracking Client',
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
      content_json: { clientName: 'Behavior Tracking Client', inspirationalQuote: '' },
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
        whatsIncluded: [
          { icon: '🎨', title: 'Diseño', description: 'UX/UI personalizado' },
        ],
        paymentOptions: [
          { label: 'Pago único', description: '$10.000.000' },
        ],
        modules: [
          { id: 'mod-core', name: 'Módulo Core', price: 10000000, is_required: true },
        ],
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
        intro: 'Detalle de los requerimientos.',
        groups: [
          {
            id: 'views',
            icon: '👁️',
            title: 'Vistas',
            is_visible: true,
            description: 'Pantallas del proyecto.',
            items: [
              { icon: '🏠', name: 'Home', description: 'Landing page.' },
            ],
          },
        ],
        additionalModules: [
          {
            id: 'behavior_tracking_module',
            icon: '👣',
            title: 'Rastreo de Comportamiento',
            is_visible: true,
            description: 'Tracking de sesiones y vistas propio, mapa de intereses, embudo de navegación, panel de comportamiento (hasta 8 KPIs / 4 gráficas), desglose por dispositivo y retención de 12 meses.',
            is_calculator_module: true,
            default_selected: false,
            selected: false,
            price_percent: 30,
            items: [
              { icon: '📈', name: 'Panel de comportamiento', description: 'Hasta 8 KPIs / 4 gráficas.' },
              { icon: '📱', name: 'Desglose por dispositivo', description: 'Segmentación por dispositivo.' },
            ],
          },
        ],
      },
    },
    {
      id: 4,
      section_type: 'timeline',
      title: 'Cronograma',
      order: 3,
      is_enabled: true,
      content_json: {
        index: '4',
        title: 'Cronograma',
        totalDuration: '10 semanas',
        phases: [],
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

async function openCalculatorModal(page) {
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
}

test.describe('Proposal Calculator — Behavior Tracking Module (30% priced add-on)', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
      localStorage.setItem(`investment_onboarding_seen_${_uuid}`, 'true');
    }, MOCK_UUID);
  });

  test('appears unselected by default under the behavior tracking group label', {
    tag: [...PROPOSAL_CALCULATOR_BEHAVIOR_TRACKING_MODULE, '@role:guest', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the proposal link is the guest's only real entry
    // point — it is shared via email/WhatsApp, there is no in-app UI to browse to
    // it from; ?mode=detailed is the documented E2E/direct-link gateway bypass,
    // matching every other spec in e2e/proposal/)
    await setupMock(page);
    await openCalculatorModal(page);

    await expect(page.getByText(/Rastreo de Comportamiento/i).first()).toBeVisible();

    const behaviorRow = page.locator('div.rounded-xl.border').filter({ hasText: /Rastreo de Comportamiento/ });
    await expect(behaviorRow).toBeVisible();
    // Unselected calculator modules show the "won't be included" impact warning.
    await expect(behaviorRow.getByText(/no se incluirá/i)).toBeVisible();
  });

  // Catches: a wrong price_percent wiring, a missing group-label fallback, or
  // the modal total not recalculating for this specific module id — none of
  // which would fail today since the module was only ever render-checked.
  test('toggling it on adds exactly 30% of the base total to the footer', {
    tag: [...PROPOSAL_CALCULATOR_BEHAVIOR_TRACKING_MODULE, '@role:guest', '@outcome:success'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // No calculator modules are pre-selected — initial total is the base $10.000.000.
    const modalFooter = page.locator('div.border-t.border-border-default.bg-surface');
    const footerTotal = modalFooter.locator('span.font-bold').filter({ hasText: /\$/ });
    await expect(footerTotal).toContainText('10.000.000');

    // 30% of 10.000.000 = 3.000.000 -> total becomes 13.000.000.
    const behaviorRow = page.locator('div.rounded-xl.border').filter({ hasText: /Rastreo de Comportamiento/ });
    await behaviorRow.click();

    await expect(footerTotal).toContainText('13.000.000', { timeout: 3000 });
  });
});
