/**
 * E2E tests for the three new calculator modules in the investment modal:
 * PWA (30%), AI Implementation (invite-only), Reports & Alerts (10%).
 *
 * Covers: modules visibility, default unselected state, price display,
 * AI invite note, info badge, selecting module updates total.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_CALCULATOR_MODULES } from '../helpers/flow-tags.js';

const MOCK_UUID = 'calc-modules-uuid-1234-5678-abcdef';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Calculator Modules Proposal',
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
        whatsIncluded: [
          { icon: '🎨', title: 'Diseño', description: 'UX/UI personalizado' },
        ],
        paymentOptions: [
          { label: 'Pago único', description: '$10.000.000' },
        ],
        modules: [
          { id: 'mod-core', name: 'Módulo Core', price: 5000000, is_required: true },
          { id: 'mod-blog', name: 'Blog Integrado', price: 3000000, is_required: false },
          { id: 'mod-analytics', name: 'Analytics', price: 2000000, is_required: false },
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
            description: 'Pantallas del proyecto.',
            items: [
              { icon: '🏠', name: 'Home', description: 'Landing page.' },
            ],
          },
          {
            id: 'pwa_module',
            icon: '📱',
            title: 'Progressive Web App (PWA)',
            description: 'Convierte tu sitio web en una aplicación instalable.',
            is_calculator_module: true,
            default_selected: false,
            price_percent: 30,
            items: [
              { icon: '📲', name: 'Instalación en dispositivo', description: 'Instala como app.' },
              { icon: '📡', name: 'Funcionamiento offline', description: 'Acceso sin conexión.' },
            ],
          },
          {
            id: 'ai_module',
            icon: '🤖',
            title: 'Integración y Automatización con IA',
            description: 'Potencia tu proyecto con IA.',
            is_calculator_module: true,
            default_selected: false,
            price_percent: null,
            is_ai_invite: true,
            items: [
              { icon: '⚡', name: 'Automatizaciones', description: 'Flujos inteligentes.' },
              { icon: '💬', name: 'Comunicación inteligente', description: 'Chatbots 24/7.' },
            ],
          },
          {
            id: 'reports_alerts_module',
            icon: '📬',
            title: 'Reportes y Alertas vía Correo o Telegram',
            description: 'Reportes automáticos y alertas personalizadas.',
            is_calculator_module: true,
            default_selected: false,
            price_percent: 10,
            items: [
              { icon: '📧', name: 'Reportes automáticos', description: 'Métricas por correo.' },
              { icon: '✈️', name: 'Integración con Telegram', description: 'Alertas en Telegram.' },
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
  await page.goto(`/proposal/${MOCK_UUID}`);
  await page.waitForLoadState('networkidle');
  await expect(page.locator('.proposal-wrapper')).toBeVisible({ timeout: 15000 });

  // Navigate from greeting to investment section
  const nextBtn = page.getByTestId('nav-next');
  await expect(nextBtn).toBeVisible({ timeout: 5000 });
  await nextBtn.click();

  // Open calculator modal
  const customizeBtn = page.getByRole('button', { name: /Personalizar/i });
  await expect(customizeBtn).toBeVisible({ timeout: 10000 });
  await customizeBtn.scrollIntoViewIfNeeded();
  await customizeBtn.click();

  // Wait for modal content
  await expect(page.getByText(/Selecciona los módulos/i)).toBeVisible({ timeout: 5000 });
}

test.describe('Proposal Calculator Modules (PWA, AI, Reports)', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('PWA module appears in modal as unselected by default', {
    tag: [...PROPOSAL_CALCULATOR_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // PWA group label (h4) should be visible
    await expect(page.locator('h4').filter({ hasText: /Progressive Web App/i })).toBeVisible();

    // PWA module item row should exist inside the modal body
    const pwaRow = page.locator('div.rounded-xl.border').filter({ hasText: /Progressive Web App/ });
    await expect(pwaRow).toBeVisible();

    // The module checkbox should show unselected state (no checkmark SVG)
    const pwaCheckbox = pwaRow.locator('div.w-6.h-6');
    await expect(pwaCheckbox.locator('svg')).not.toBeVisible();
  });

  test('AI module shows schedule call label instead of price', {
    tag: [...PROPOSAL_CALCULATOR_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // AI module group label
    await expect(page.getByText(/Integración con IA/i)).toBeVisible();

    // Should show "Agendar llamada" instead of a price
    await expect(page.getByText('Agendar llamada')).toBeVisible();
  });

  test('AI module displays creative invite note', {
    tag: [...PROPOSAL_CALCULATOR_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // Click the AI module to select it
    const aiRow = page.locator('div.rounded-xl.border').filter({ hasText: /Integración.*IA/ });
    await aiRow.click();

    // The creative invite note should be visible (purple box)
    await expect(page.getByText(/Te invitamos a una llamada personalizada/)).toBeVisible();
  });

  test('Reports & Alerts module appears in modal as unselected by default', {
    tag: [...PROPOSAL_CALCULATOR_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // Reports & Alerts group label (h4) should be visible
    await expect(page.locator('h4').filter({ hasText: /Reportes y Alertas/i })).toBeVisible();

    // Module item row should exist
    const reportsRow = page.locator('div.rounded-xl.border').filter({ hasText: /Reportes y Alertas/ });
    await expect(reportsRow).toBeVisible();

    // The module checkbox should show unselected state (no checkmark SVG)
    const reportsCheckbox = reportsRow.locator('div.w-6.h-6');
    await expect(reportsCheckbox.locator('svg')).not.toBeVisible();
  });

  test('selecting PWA module increases total investment display', {
    tag: [...PROPOSAL_CALCULATOR_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // Modal footer total — scope to the border-t footer area containing "Total inversión"
    const modalFooter = page.locator('div.border-t.border-gray-100.bg-gray-50');
    const footerTotal = modalFooter.locator('span.font-bold').filter({ hasText: /\$/ });
    await expect(footerTotal).toContainText('10.000.000');

    // Click PWA module to select it (+30% = +$3.000.000)
    const pwaRow = page.locator('div.rounded-xl.border').filter({ hasText: /Progressive Web App/ });
    await pwaRow.click();

    // Total should increase to $13.000.000
    await expect(footerTotal).toContainText('13.000.000', { timeout: 3000 });
  });

  test('info badge about optional items is visible at modal bottom', {
    tag: [...PROPOSAL_CALCULATOR_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // The informational badge text should be visible
    await expect(page.getByText(/Los elementos aquí son opcionales/)).toBeVisible();

    // The "view requirements" link should be present
    await expect(page.getByText(/Ver detalle de requerimientos funcionales/)).toBeVisible();
  });
});
