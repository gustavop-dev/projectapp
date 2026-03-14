/**
 * E2E tests for proposal calculator dynamic timeline.
 *
 * Covers: timeline display in calculator modal, week reduction when
 * deselecting modules, week extension when selecting calculator modules,
 * and timeline change text visibility.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_CALCULATOR_TIMELINE } from '../helpers/flow-tags.js';

const MOCK_UUID = 'calc-timeline-uuid-1234-5678-abcdef';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Calculator Timeline Proposal',
  client_name: 'Timeline Client',
  status: 'sent',
  language: 'es',
  total_investment: '15000000',
  currency: 'COP',
  sections: [
    {
      id: 1, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true,
      content_json: { clientName: 'Timeline Client', inspirationalQuote: 'Hello.' },
    },
    {
      id: 2, section_type: 'timeline', title: 'Cronograma', order: 1, is_enabled: true,
      content_json: {
        index: '1',
        title: 'Cronograma',
        totalDuration: '12 semanas',
        phases: [
          { title: 'Discovery', duration: '2 semanas', tasks: ['Research'] },
          { title: 'Desarrollo', duration: '8 semanas', tasks: ['Build'] },
          { title: 'QA', duration: '2 semanas', tasks: ['Testing'] },
        ],
      },
    },
    {
      id: 3, section_type: 'investment', title: 'Inversión', order: 2, is_enabled: true,
      content_json: {
        index: '2',
        title: 'Inversión',
        introText: 'Tu inversión incluye:',
        totalInvestment: '15000000',
        currency: 'COP',
        modules: [
          { id: 'm1', name: 'Módulo CRM', price: 3000000, is_required: true },
          { id: 'm2', name: 'Módulo E-commerce', price: 5000000, is_required: false },
          { id: 'm3', name: 'Integración Pasarela', price: 2000000, is_required: false },
          { id: 'm4', name: 'App Móvil', price: 5000000, is_required: false },
        ],
        whatsIncluded: [{ icon: '✅', title: 'Soporte', description: '6 meses' }],
        paymentOptions: [],
        paymentMethods: [],
        valueReasons: [],
      },
    },
    {
      id: 4, section_type: 'functional_requirements', title: 'Requerimientos', order: 3, is_enabled: true,
      content_json: {
        index: '3',
        title: 'Requerimientos Funcionales',
        intro: 'Detalle.',
        groups: [
          {
            id: 'views', icon: '👁️', title: 'Vistas', is_visible: true, description: 'Pantallas.',
            items: [{ icon: '🏠', name: 'Home', description: 'Landing.' }],
          },
          {
            id: 'pwa_module', icon: '📱', title: 'Progressive Web App (PWA)', is_visible: true,
            description: 'App instalable.', is_calculator_module: true, default_selected: false, price_percent: 40,
            items: [{ icon: '📲', name: 'Instalación', description: 'Instala como app.' }],
          },
        ],
        additionalModules: [],
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

test.describe('Proposal Calculator Dynamic Timeline', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('calculator modal shows timeline with base weeks when opened', {
    tag: [...PROPOSAL_CALCULATOR_TIMELINE, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    // Navigate to investment section (section index 2)
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();
    // Wait for timeline section before clicking again
    await expect(page.getByText('Cronograma')).toBeVisible({ timeout: 5000 });
    await nextBtn.click();

    // Click "Personalizar tu inversión" button to open calculator
    const customizeBtn = page.getByRole('button', { name: /Personalizar/i });
    await expect(customizeBtn).toBeVisible({ timeout: 10000 });
    await customizeBtn.click();

    // Calculator modal should show timeline with 12 weeks
    await expect(page.getByText('12 semanas')).toBeVisible({ timeout: 10000 });
  });

  test('deselecting a module reduces the timeline weeks', {
    tag: [...PROPOSAL_CALCULATOR_TIMELINE, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    // Navigate to investment section
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();
    await expect(page.getByText('Cronograma')).toBeVisible({ timeout: 5000 });
    await nextBtn.click();

    // Open calculator
    const customizeBtn = page.getByRole('button', { name: /Personalizar/i });
    await expect(customizeBtn).toBeVisible({ timeout: 10000 });
    await customizeBtn.click();

    // Deselect "Módulo E-commerce" (non-required module)
    await expect(page.getByText('Módulo E-commerce')).toBeVisible({ timeout: 5000 });
    await page.getByText('Módulo E-commerce').click();

    // Timeline should now show the reduction text
    await expect(page.getByText(/Se reduce de 12 a 11 semanas/)).toBeVisible({ timeout: 10000 });
  });

  test('deselecting multiple modules shows cumulative reduction', {
    tag: [...PROPOSAL_CALCULATOR_TIMELINE, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    // Navigate to investment section
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();
    await expect(page.getByText('Cronograma')).toBeVisible({ timeout: 5000 });
    await nextBtn.click();

    // Open calculator
    const customizeBtn = page.getByRole('button', { name: /Personalizar/i });
    await expect(customizeBtn).toBeVisible({ timeout: 10000 });
    await customizeBtn.click();

    // Deselect two non-required modules
    await expect(page.getByText('Módulo E-commerce')).toBeVisible({ timeout: 5000 });
    await page.getByText('Módulo E-commerce').click();
    await page.getByText('Integración Pasarela').click();

    // Should show reduction from 12 to 10 (2 modules = -2 weeks)
    await expect(page.getByText(/Se reduce de 12 a 10 semanas/)).toBeVisible({ timeout: 10000 });
  });

  test('selecting a calculator module extends the timeline weeks', {
    tag: [...PROPOSAL_CALCULATOR_TIMELINE, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    // Navigate to investment section
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();
    await expect(page.getByText('Cronograma')).toBeVisible({ timeout: 5000 });
    await nextBtn.click();

    // Open calculator
    const customizeBtn = page.getByRole('button', { name: /Personalizar/i });
    await expect(customizeBtn).toBeVisible({ timeout: 10000 });
    await customizeBtn.click();

    // Select PWA calculator module (adds ~1 week)
    const pwaRow = page.locator('div.rounded-xl.border').filter({ hasText: /Progressive Web App/ });
    await expect(pwaRow).toBeVisible({ timeout: 5000 });
    await pwaRow.click();

    // Timeline should now show the extension text
    await expect(page.getByText(/Se extiende de 12 a 13 semanas/)).toBeVisible({ timeout: 10000 });
  });
});
