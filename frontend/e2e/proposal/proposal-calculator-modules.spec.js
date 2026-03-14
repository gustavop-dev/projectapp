/**
 * E2E tests for the three calculator modules in the investment modal:
 * PWA (40%), AI Implementation (invite-only, price_percent 0), Reports & Alerts (20%, default selected).
 *
 * @flow: proposal-calculator-modules
 *
 * Covers: modules visibility, default states, price display,
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
            is_visible: true,
            description: 'Pantallas del proyecto.',
            items: [
              { icon: '🏠', name: 'Home', description: 'Landing page.' },
            ],
          },
          {
            id: 'pwa_module',
            icon: '📱',
            title: 'Progressive Web App (PWA)',
            is_visible: true,
            description: 'Convierte tu sitio web en una aplicación instalable.',
            is_calculator_module: true,
            default_selected: false,
            price_percent: 40,
            items: [
              { icon: '📲', name: 'Instalación en dispositivo', description: 'Instala como app.' },
              { icon: '📡', name: 'Funcionamiento offline', description: 'Acceso sin conexión.' },
            ],
          },
          {
            id: 'ai_module',
            icon: '🤖',
            title: 'Integración y Automatización con IA',
            is_visible: true,
            description: 'Potencia tu proyecto con IA.',
            is_calculator_module: true,
            default_selected: false,
            price_percent: 0,
            is_invite: true,
            items: [
              { icon: '⚡', name: 'Automatizaciones', description: 'Flujos inteligentes.' },
              { icon: '💬', name: 'Comunicación inteligente', description: 'Chatbots 24/7.' },
            ],
          },
          {
            id: 'reports_alerts_module',
            icon: '📬',
            title: 'Reportes y Alertas vía Correo o Telegram',
            is_visible: true,
            description: 'Reportes automáticos y alertas personalizadas.',
            is_calculator_module: true,
            default_selected: true,
            price_percent: 20,
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
  await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

  // Navigate from greeting to investment section
  const nextBtn = page.getByTestId('nav-next');
  await expect(nextBtn).toBeVisible({ timeout: 15000 });
  await nextBtn.click();

  // Wait for investment section to render before opening modal
  await expect(page.getByText(/inversi[oó]n/i).first()).toBeVisible({ timeout: 10000 });

  // Open calculator modal
  const customizeBtn = page.getByRole('button', { name: /Personalizar/i });
  await expect(customizeBtn).toBeVisible({ timeout: 10000 });
  await customizeBtn.scrollIntoViewIfNeeded();
  await customizeBtn.click();

  // Wait for modal content
  await expect(page.getByText(/Selecciona los módulos/i)).toBeVisible({ timeout: 10000 });
}

test.describe('Proposal Calculator Modules (PWA, AI, Reports)', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('PWA module appears in modal as unselected by default', {
    tag: [...PROPOSAL_CALCULATOR_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // PWA group label should be visible
    await expect(page.getByText(/Progressive Web App/i).first()).toBeVisible();

    // PWA module row should be visible
    // quality: allow-fragile-selector (module row has no testid, identified by text content within styled container)
    const pwaRow = page.locator('.rounded-xl').filter({ hasText: /Progressive Web App/ }).first();
    await expect(pwaRow).toBeVisible();

    // Unselected modules show an impact warning — verify it is present (proves unselected state)
    // The generic impact text is 'Este componente no se incluirá en el proyecto.'
    await expect(pwaRow.getByText(/no se incluirá/i)).toBeVisible();
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
    await aiRow.scrollIntoViewIfNeeded();
    await aiRow.click();

    // The creative invite note should be visible (purple box)
    await expect(page.getByText(/Te invitamos a una llamada personalizada/)).toBeVisible({ timeout: 5000 });
  });

  test('Reports & Alerts module appears in modal as selected by default', {
    tag: [...PROPOSAL_CALCULATOR_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // Reports & Alerts group label (h4) should be visible
    await expect(page.locator('h4').filter({ hasText: /Reportes y Alertas/i })).toBeVisible();

    // Module item row should exist
    const reportsRow = page.locator('div.rounded-xl.border').filter({ hasText: /Reportes y Alertas/ });
    await expect(reportsRow).toBeVisible();

    // The module checkbox should show selected state (checkmark SVG visible)
    const reportsCheckbox = reportsRow.locator('div.w-6.h-6');
    await expect(reportsCheckbox.locator('svg')).toBeVisible();
  });

  test('selecting PWA module increases total investment display', {
    tag: [...PROPOSAL_CALCULATOR_MODULES, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    // Modal footer total — scope to the border-t footer area containing "Total inversión"
    // Reports & Alerts is default_selected:true at 20% = +$2.000.000, so initial = $12.000.000
    const modalFooter = page.locator('div.border-t.border-gray-100.bg-gray-50');
    const footerTotal = modalFooter.locator('span.font-bold').filter({ hasText: /\$/ });
    await expect(footerTotal).toContainText('12.000.000');

    // Click PWA module to select it (+40% = +$4.000.000)
    const pwaRow = page.locator('div.rounded-xl.border').filter({ hasText: /Progressive Web App/ });
    await pwaRow.click();

    // Total should increase to $16.000.000
    await expect(footerTotal).toContainText('16.000.000', { timeout: 3000 });
  });

  test('info badge about optional items is visible at modal top', {
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
