/**
 * E2E tests for the biometric verification module in the investment calculator.
 * The module is provider-billed (is_invite: true, price_percent: 0): it appears
 * in the calculator list, shows "Agendar llamada" instead of a price, displays
 * an invite note, and does NOT contribute to the total when selected.
 *
 * @flow: proposal-calculator-biometric-module
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_CALCULATOR_BIOMETRIC_MODULE } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-b10b10b10b10';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Biometric Module Proposal',
  client_name: 'Biometric Client',
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
      content_json: { clientName: 'Biometric Client', inspirationalQuote: '' },
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
            id: 'biometric_verification_module',
            icon: '🪪',
            title: 'Verificación y Validación Biométrica (Integración API)',
            is_visible: true,
            description: 'Valida que la persona detrás de la pantalla es realmente quien dice ser.',
            is_calculator_module: true,
            default_selected: false,
            selected: false,
            price_percent: 0,
            is_invite: true,
            invite_note: '🤝 Te invitamos a una llamada donde definimos juntos el alcance de la verificación biométrica y validación de identidad para tu negocio.',
            items: [
              { icon: '🪪', name: 'Lectura y validación de documento', description: 'OCR del documento de identidad.' },
              { icon: '👤', name: 'Reconocimiento facial', description: 'Comparación biométrica.' },
              { icon: '🎬', name: 'Prueba de vida (liveness)', description: 'Evita suplantación.' },
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

test.describe('Proposal Calculator — Biometric Verification Module (provider-billed, is_invite)', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
      localStorage.setItem(`investment_onboarding_seen_${_uuid}`, 'true');
    }, MOCK_UUID);
  });

  test('biometric module appears in calculator with invite label instead of price', {
    tag: [...PROPOSAL_CALCULATOR_BIOMETRIC_MODULE, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    await expect(page.getByText(/Verificación y Validación Biométrica/i).first()).toBeVisible();
    await expect(page.getByText('Agendar llamada')).toContainText('Agendar llamada');
  });

  test('clicking biometric module reveals invite note', {
    tag: [...PROPOSAL_CALCULATOR_BIOMETRIC_MODULE, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await openCalculatorModal(page);

    const bioRow = page.locator('div.rounded-xl.border').filter({ hasText: /Verificación.*Biométrica/ });
    await bioRow.scrollIntoViewIfNeeded();
    await bioRow.click();

    await expect(page.getByText(/Te invitamos a una llamada/)).toContainText('Te invitamos a una llamada', { timeout: 5000 });
  });
});
