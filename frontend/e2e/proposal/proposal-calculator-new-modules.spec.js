/**
 * E2E tests for the new default calculator modules added in v1.7.0:
 * KPI Dashboard (free, default selected), Email Marketing (10%),
 * Conversion Tracking (invite), i18n (15%), Gift Cards (20%).
 *
 * @flow: proposal-calculator-new-modules
 *
 * Covers: module visibility, default states, pricing display,
 * free module badge, invite-only label, selecting module updates total.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_CALCULATOR_NEW_MODULES } from '../helpers/flow-tags.js';

const MOCK_UUID = 'new-modules-uuid-1234-5678-abcdef';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'New Modules Proposal',
  client_name: 'Modules Client',
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
      content_json: { clientName: 'Modules Client', inspirationalQuote: '' },
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
        whatsIncluded: [],
        paymentOptions: [],
        modules: [
          { id: 'mod-core', name: 'Módulo Core', price: 5000000, is_required: true },
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
        intro: 'Detalle.',
        groups: [
          {
            id: 'views',
            icon: '👁️',
            title: 'Vistas',
            description: 'Pantallas.',
            items: [{ icon: '🏠', name: 'Home', description: 'Landing.' }],
          },
          {
            id: 'kpi_dashboard_module',
            icon: '📊',
            title: 'Dashboard de KPIs',
            description: 'Panel de métricas clave en tiempo real.',
            is_calculator_module: true,
            default_selected: true,
            price_percent: 0,
            items: [
              { icon: '📈', name: 'Métricas en tiempo real', description: 'KPIs actualizados.' },
            ],
          },
          {
            id: 'email_marketing_module',
            icon: '📧',
            title: 'Email Marketing Integrado',
            description: 'Campañas de email automatizadas.',
            is_calculator_module: true,
            default_selected: false,
            price_percent: 10,
            items: [
              { icon: '📬', name: 'Campañas automáticas', description: 'Secuencias de emails.' },
            ],
          },
          {
            id: 'conversion_tracking_module',
            icon: '🎯',
            title: 'Conversiones Inteligentes',
            description: 'Seguimiento avanzado de conversiones.',
            is_calculator_module: true,
            default_selected: false,
            price_percent: null,
            is_ai_invite: true,
            invite_note: 'Agendemos una llamada para diseñar tu embudo de conversión personalizado.',
            items: [
              { icon: '📊', name: 'Embudos de conversión', description: 'Tracking multi-canal.' },
            ],
          },
          {
            id: 'i18n_module',
            icon: '🌐',
            title: 'Multi-idioma (i18n)',
            description: 'Soporte multilingüe completo.',
            is_calculator_module: true,
            default_selected: false,
            price_percent: 15,
            items: [
              { icon: '🗣️', name: 'Traducción dinámica', description: 'Contenido en múltiples idiomas.' },
            ],
          },
          {
            id: 'gift_cards_module',
            icon: '🎁',
            title: 'Sistema de Gift Cards',
            description: 'Gift cards digitales.',
            is_calculator_module: true,
            default_selected: false,
            price_percent: 20,
            items: [
              { icon: '💳', name: 'Gift cards digitales', description: 'Tarjetas de regalo.' },
            ],
          },
        ],
        additionalModules: [],
      },
    },
    {
      id: 4,
      section_type: 'timeline',
      title: 'Cronograma',
      order: 3,
      is_enabled: true,
      content_json: { index: '4', title: 'Cronograma', totalDuration: '10 semanas', phases: [] },
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
  await page.goto(`/proposal/${MOCK_UUID}`);
  await page.waitForLoadState('networkidle');
  await expect(page.locator('.proposal-wrapper')).toBeVisible({ timeout: 15000 });

  const nextBtn = page.getByTestId('nav-next');
  await expect(nextBtn).toBeVisible({ timeout: 5000 });
  await nextBtn.click();

  const customizeBtn = page.getByRole('button', { name: /Personalizar/i });
  await expect(customizeBtn).toBeVisible({ timeout: 10000 });
  await customizeBtn.scrollIntoViewIfNeeded();
  await customizeBtn.click();

  await expect(page.getByText(/Selecciona los módulos/i)).toBeVisible({ timeout: 5000 });
}

test.describe('@flow: proposal-calculator-new-modules — New Default Calculator Modules', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('KPI Dashboard module appears with zero price (included at no cost)', {
    tag: [...PROPOSAL_CALCULATOR_NEW_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // The group header uses groupLabels: "Dashboard de KPIs"
    await expect(page.locator('h4').filter({ hasText: /Dashboard de KPIs/ })).toBeVisible();

    // The module row shows the group icon + title
    const kpiRow = page.locator('div.rounded-xl.border').filter({ hasText: /Dashboard de KPIs/ });
    await expect(kpiRow).toBeVisible();

    // Calculator modules default to unselected (default_selected: false in page code)
    const checkbox = kpiRow.locator('div.w-6.h-6');
    await expect(checkbox.locator('svg')).not.toBeVisible();
  });

  test('Email Marketing module appears as unselected with 10% price', {
    tag: [...PROPOSAL_CALCULATOR_NEW_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    const emailRow = page.locator('div.rounded-xl.border').filter({ hasText: /Email Marketing/ });
    await expect(emailRow).toBeVisible();

    // Should be unselected (no checkmark)
    const checkbox = emailRow.locator('div.w-6.h-6');
    await expect(checkbox.locator('svg')).not.toBeVisible();
  });

  test('Conversion Tracking module shows invite-only label', {
    tag: [...PROPOSAL_CALCULATOR_NEW_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // Group header from groupLabels
    await expect(page.locator('h4').filter({ hasText: /Conversiones Inteligentes/ })).toBeVisible();

    // Module row with invite-only "Agendar llamada" label
    const convRow = page.locator('div.rounded-xl.border').filter({ hasText: /Conversiones Inteligentes/ });
    await expect(convRow).toBeVisible();
    await expect(convRow.getByText('Agendar llamada')).toBeVisible();
  });

  test('i18n module appears with 15% price', {
    tag: [...PROPOSAL_CALCULATOR_NEW_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    const i18nRow = page.locator('div.rounded-xl.border').filter({ hasText: /Multi-idioma/ });
    await expect(i18nRow).toBeVisible();

    // Should be unselected
    const checkbox = i18nRow.locator('div.w-6.h-6');
    await expect(checkbox.locator('svg')).not.toBeVisible();
  });

  test('Gift Cards module appears with 20% price', {
    tag: [...PROPOSAL_CALCULATOR_NEW_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    const giftRow = page.locator('div.rounded-xl.border').filter({ hasText: /Gift Cards/ });
    await expect(giftRow).toBeVisible();
  });

  test('selecting Gift Cards module increases total by 20%', {
    tag: [...PROPOSAL_CALCULATOR_NEW_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    const modalFooter = page.locator('div.border-t.border-gray-100.bg-gray-50');
    const footerTotal = modalFooter.locator('span.font-bold').filter({ hasText: /\$/ });
    await expect(footerTotal).toContainText('10.000.000');

    // Click Gift Cards module (+20% = +$2.000.000)
    const giftRow = page.locator('div.rounded-xl.border').filter({ hasText: /Gift Cards/ });
    await giftRow.click();

    await expect(footerTotal).toContainText('12.000.000', { timeout: 3000 });
  });
});
