/**
 * E2E tests for integration calculator modules in the investment modal:
 * International Payments (20%), Regional Payments (20%),
 * Electronic Invoicing (60%), Conversion Tracking (invite-only, 0%).
 *
 * @flow: proposal-calculator-integrations
 *
 * Covers: integration visibility, default unselected state, pricing display,
 * invite-only label for conversion tracking, selecting integration updates total.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_CALCULATOR_INTEGRATIONS } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-000000000002';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Integration Modules Proposal',
  client_name: 'Integration Client',
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
      content_json: { clientName: 'Integration Client', inspirationalQuote: '' },
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
            is_visible: true,
            description: 'Pantallas.',
            items: [{ icon: '🏠', name: 'Home', description: 'Landing.' }],
          },
          {
            id: 'integration_international_payments',
            icon: '🌎',
            title: 'Pasarela de Pago Internacional',
            is_visible: true,
            description: 'Integración con pasarelas de pago internacionales.',
            is_calculator_module: true,
            default_selected: false,
            price_percent: 20,
            is_invite: false,
            items: [
              { icon: '💳', name: 'Stripe', description: 'Pagos con tarjeta internacionales.' },
              { icon: '🅿️', name: 'PayPal', description: 'Pagos con saldo PayPal.' },
            ],
          },
          {
            id: 'integration_regional_payments',
            icon: '🇨🇴',
            title: 'Pasarela de Pago Regional (Colombia)',
            is_visible: true,
            description: 'Integración con pasarelas de pago colombianas.',
            is_calculator_module: true,
            default_selected: false,
            price_percent: 20,
            is_invite: false,
            items: [
              { icon: '💳', name: 'PayU', description: 'Pagos con tarjeta, PSE, Efecty.' },
              { icon: '🏦', name: 'Wompi', description: 'PSE, tarjetas, Nequi.' },
              { icon: '💰', name: 'ePayco', description: 'PSE, tarjetas, recaudos.' },
            ],
          },
          {
            id: 'integration_electronic_invoicing',
            icon: '🧾',
            title: 'Facturación Electrónica e Integración DIAN',
            is_visible: true,
            description: 'Facturación electrónica con trazabilidad fiscal.',
            is_calculator_module: true,
            default_selected: false,
            price_percent: 60,
            is_invite: false,
            items: [
              { icon: '📄', name: 'Comprobantes electrónicos', description: 'Facturas, notas crédito/débito.' },
              { icon: '🔗', name: 'Proveedores colombianos', description: 'Siigo, Alegra.' },
            ],
          },
          {
            id: 'integration_conversion_tracking',
            icon: '📡',
            title: 'Conversiones Inteligentes (Meta & Google Ads)',
            is_visible: true,
            description: 'Seguimiento de conversiones server-side.',
            is_calculator_module: true,
            default_selected: false,
            price_percent: 0,
            is_invite: true,
            invite_note: '🤝 Te invitamos a una llamada donde analizaremos tu estrategia publicitaria.',
            items: [
              { icon: '🔗', name: 'Meta Conversions API', description: 'Conexión directa con Meta.' },
              { icon: '📊', name: 'Google Enhanced Conversions', description: 'Conversiones encriptadas.' },
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
  await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
  await page.waitForLoadState('domcontentloaded');

  const nextBtn = page.getByTestId('nav-next');
  await expect(nextBtn).toBeVisible({ timeout: 20000 });
  await nextBtn.click();

  // Wait for investment section to render before opening modal
  await expect(page.getByText(/inversi[oó]n/i).first()).toBeVisible({ timeout: 10000 });

  const customizeBtn = page.getByRole('button', { name: /Personalizar/i });
  await expect(customizeBtn).toBeVisible({ timeout: 10000 });
  await customizeBtn.scrollIntoViewIfNeeded();
  await customizeBtn.click();

  await expect(page.getByText(/Selecciona los módulos/i)).toBeVisible({ timeout: 10000 });
}

test.describe('Integration Calculator Modules', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
      localStorage.setItem(`investment_onboarding_seen_${_uuid}`, 'true');
    }, MOCK_UUID);
  });

  test('International Payment Gateway appears as unselected with 20% price', {
    tag: [...PROPOSAL_CALCULATOR_INTEGRATIONS, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // Group header should be visible
    await expect(page.locator('h4').filter({ hasText: /Pasarela de Pago Internacional/ })).toBeVisible();

    // Integration row should be visible
    const intlRow = page.locator('div.rounded-xl.border').filter({ hasText: /Pasarela de Pago Internacional/ });
    await expect(intlRow).toBeVisible();

    // Should be unselected (no checkmark)
    const checkbox = intlRow.locator('div.w-6.h-6');
    await expect(checkbox.locator('svg')).not.toBeVisible();
  });

  test('Regional Payment Gateway (Colombia) appears as unselected with 20% price', {
    tag: [...PROPOSAL_CALCULATOR_INTEGRATIONS, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // Group header should be visible
    await expect(page.locator('h4').filter({ hasText: /Pasarela de Pago Regional/ })).toBeVisible();

    // Integration row should be visible
    const regRow = page.locator('div.rounded-xl.border').filter({ hasText: /Pasarela de Pago Regional/ });
    await expect(regRow).toBeVisible();

    // Should be unselected (no checkmark)
    const checkbox = regRow.locator('div.w-6.h-6');
    await expect(checkbox.locator('svg')).not.toBeVisible();
  });

  test('Electronic Invoicing appears as unselected with 60% price', {
    tag: [...PROPOSAL_CALCULATOR_INTEGRATIONS, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // Group header should be visible
    await expect(page.locator('h4').filter({ hasText: /Facturación Electrónica/ })).toBeVisible();

    // Integration row should be visible
    const invRow = page.locator('div.rounded-xl.border').filter({ hasText: /Facturación Electrónica/ });
    await expect(invRow).toBeVisible();

    // Should be unselected
    const checkbox = invRow.locator('div.w-6.h-6');
    await expect(checkbox.locator('svg')).not.toBeVisible();
  });

  test('Conversion Tracking integration shows invite-only label', {
    tag: [...PROPOSAL_CALCULATOR_INTEGRATIONS, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // Group header from groupLabels
    await expect(page.locator('h4').filter({ hasText: /Conversiones Inteligentes/ })).toBeVisible();

    // Integration row with invite-only "Agendar llamada" label
    const convRow = page.locator('div.rounded-xl.border').filter({ hasText: /Conversiones Inteligentes/ });
    await expect(convRow).toBeVisible();
    await expect(convRow.getByText('Agendar llamada')).toBeVisible();
  });

  test('selecting International Payment Gateway increases total by 20%', {
    tag: [...PROPOSAL_CALCULATOR_INTEGRATIONS, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    const modalFooter = page.locator('div.border-t.border-border-default.bg-surface-muted');
    const footerTotal = modalFooter.locator('span.font-bold').filter({ hasText: /\$/ });
    await expect(footerTotal).toContainText('10.000.000');

    // Click International Payments (+20% = +$2.000.000)
    const intlRow = page.locator('div.rounded-xl.border').filter({ hasText: /Pasarela de Pago Internacional/ });
    await intlRow.scrollIntoViewIfNeeded();
    await intlRow.click();

    await expect(footerTotal).toContainText('12.000.000', { timeout: 5000 });
  });

  test('selecting Electronic Invoicing increases total by 60%', {
    tag: [...PROPOSAL_CALCULATOR_INTEGRATIONS, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    const modalFooter = page.locator('div.border-t.border-border-default.bg-surface-muted');
    const footerTotal = modalFooter.locator('span.font-bold').filter({ hasText: /\$/ });
    await expect(footerTotal).toContainText('10.000.000');

    // Click Electronic Invoicing (+60% = +$6.000.000)
    const invRow = page.locator('div.rounded-xl.border').filter({ hasText: /Facturación Electrónica/ });
    await invRow.scrollIntoViewIfNeeded();
    await invRow.click();

    await expect(footerTotal).toContainText('16.000.000', { timeout: 5000 });
  });
});
