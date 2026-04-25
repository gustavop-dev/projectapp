/**
 * E2E tests for calculator selection persistence across section navigation.
 *
 * @flow: proposal-calculator-reopen-after-nav
 *
 * Reproduces the reported bug: after deselecting a module and confirming,
 * navigating to another section and coming back should preserve the
 * deselection when the modal is reopened. A hard page reload, in contrast,
 * should reset to backend state.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_CALCULATOR_REOPEN_AFTER_NAV } from '../helpers/flow-tags.js';

const MOCK_UUID = '11111111-2222-3333-4444-555555555555';

const mockProposal = {
  id: 99,
  uuid: MOCK_UUID,
  title: 'Calculator Reopen Proposal',
  client_name: 'Reopen Client',
  status: 'sent',
  language: 'es',
  total_investment: '10000000',
  effective_total_investment: 12000000,
  currency: 'COP',
  has_confirmed_module_selection: false,
  selected_modules: [],
  sections: [
    {
      id: 1,
      section_type: 'greeting',
      title: 'Bienvenido',
      order: 0,
      is_enabled: true,
      content_json: { clientName: 'Reopen Client', inspirationalQuote: '' },
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
            items: [{ icon: '🏠', name: 'Home', description: 'Landing page.' }],
          },
          {
            id: 'reports_alerts_module',
            icon: '📬',
            title: 'Reportes y Alertas',
            is_visible: true,
            description: 'Reportes automáticos.',
            is_calculator_module: true,
            default_selected: true,
            price_percent: 20,
            items: [{ icon: '📧', name: 'Reportes', description: 'Por correo.' }],
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

const MOCK_PROPOSAL_JSON = JSON.stringify(mockProposal);

function setupMock(page) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: MOCK_PROPOSAL_JSON };
    }
    return null;
  });
}

async function goToInvestmentSection(page) {
  await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
  const nextBtn = page.getByTestId('nav-next');
  await expect(nextBtn).toBeVisible({ timeout: 15000 });
  await nextBtn.click();
  await expect(page.getByRole('button', { name: /Personalizar tu inversión/i })).toBeVisible({ timeout: 10000 });
}

async function openModal(page) {
  const customizeBtn = page.getByRole('button', { name: /Personalizar tu inversión/i });
  await customizeBtn.scrollIntoViewIfNeeded();
  await customizeBtn.click();
  await expect(page.getByText(/Selecciona los módulos/i)).toBeVisible({ timeout: 10000 });
}

function modalRow(page, label) {
  return page.locator('div.rounded-xl.border').filter({ hasText: label });
}

async function assertChecked(page, label) {
  const row = modalRow(page, label);
  await expect(row.locator('div.w-6.h-6 svg')).toBeVisible();
}

async function assertUnchecked(page, label) {
  const row = modalRow(page, label);
  await expect(row.locator('div.w-6.h-6 svg')).toHaveCount(0);
}

test.describe('Calculator selection persists across section navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
      localStorage.setItem(`investment_onboarding_seen_${uuid}`, 'true');
      localStorage.setItem(`executive_investment_onboarding_seen_${uuid}`, 'true');
      localStorage.setItem(`requirements_onboarding_seen_${uuid}`, 'true');
    }, MOCK_UUID);
  });

  test('confirm + navigate away + return keeps the deselected module unchecked', {
    tag: [...PROPOSAL_CALCULATOR_REOPEN_AFTER_NAV, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await goToInvestmentSection(page);

    const totalLocator = page.locator('section.investment span.text-lemon').filter({ hasText: /\$/ }).first();
    const initialTotal = (await totalLocator.innerText()).trim();

    await openModal(page);
    await assertChecked(page, 'Blog Integrado');
    await modalRow(page, 'Blog Integrado').click();
    await assertUnchecked(page, 'Blog Integrado');

    await page.getByRole('button', { name: /Confirmar selección/i }).click();
    await expect(page.getByText(/Selecciona los módulos/i)).not.toBeVisible({ timeout: 5000 });

    // Investment total must drop after confirm (≈$12M → ≈$9M).
    await expect(totalLocator).not.toHaveText(initialTotal, { timeout: 5000 });

    await page.getByTestId('nav-next').click();
    await expect(page.getByRole('heading', { name: /Requerimientos Funcionales/i })).toBeVisible({ timeout: 10000 });
    await page.getByTestId('nav-prev').click();
    await expect(page.getByRole('button', { name: /Personalizar tu inversión/i })).toBeVisible({ timeout: 10000 });

    // Bug repro: the deselection must survive the section round-trip.
    await openModal(page);
    await assertUnchecked(page, 'Blog Integrado');
  });

  test('close without confirm + navigate + return keeps the last in-modal toggle', {
    tag: [...PROPOSAL_CALCULATOR_REOPEN_AFTER_NAV, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await goToInvestmentSection(page);
    await openModal(page);
    await assertChecked(page, 'Blog Integrado');

    await modalRow(page, 'Blog Integrado').click();
    await assertUnchecked(page, 'Blog Integrado');
    await page.getByRole('button', { name: /Cerrar/i }).click();
    await expect(page.getByText(/Selecciona los módulos/i)).not.toBeVisible({ timeout: 5000 });

    await page.getByTestId('nav-next').click();
    await expect(page.getByRole('heading', { name: /Requerimientos Funcionales/i })).toBeVisible({ timeout: 10000 });
    await page.getByTestId('nav-prev').click();
    await expect(page.getByRole('button', { name: /Personalizar tu inversión/i })).toBeVisible({ timeout: 10000 });

    // Even without confirm, the live in-memory selection must survive nav.
    await openModal(page);
    await assertUnchecked(page, 'Blog Integrado');
  });

  test('deselecting to an empty set + navigate + return keeps it empty (does not fall back to defaults)', {
    tag: [...PROPOSAL_CALCULATOR_REOPEN_AFTER_NAV, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await goToInvestmentSection(page);
    await openModal(page);
    // Reports & Alerts is the only default-selected calc module in this mock.
    await assertChecked(page, 'Reportes y Alertas');

    // Deselect it so the confirmed selection becomes an empty array.
    await modalRow(page, 'Reportes y Alertas').click();
    await assertUnchecked(page, 'Reportes y Alertas');
    await page.getByRole('button', { name: /Confirmar selección/i }).click();
    await expect(page.getByText(/Selecciona los módulos/i)).not.toBeVisible({ timeout: 5000 });

    await page.getByTestId('nav-next').click();
    await expect(page.getByRole('heading', { name: /Requerimientos Funcionales/i })).toBeVisible({ timeout: 10000 });
    await page.getByTestId('nav-prev').click();
    await expect(page.getByRole('button', { name: /Personalizar tu inversión/i })).toBeVisible({ timeout: 10000 });

    // Bug repro: with an empty confirmed selection, the module must stay
    // unchecked — not re-check from the default_selected flag.
    await openModal(page);
    await assertUnchecked(page, 'Reportes y Alertas');
  });

  test('page reload resets the modal back to backend defaults', {
    tag: [...PROPOSAL_CALCULATOR_REOPEN_AFTER_NAV, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await goToInvestmentSection(page);
    await openModal(page);

    await modalRow(page, 'Blog Integrado').click();
    await page.getByRole('button', { name: /Confirmar selección/i }).click();
    await expect(page.getByText(/Selecciona los módulos/i)).not.toBeVisible({ timeout: 5000 });

    // addInitScript from beforeEach still applies after reload, so onboarding
    // flags stay suppressed; the reload only wipes the in-memory page state.
    await page.reload();
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();
    await expect(page.getByRole('button', { name: /Personalizar tu inversión/i })).toBeVisible({ timeout: 10000 });

    await openModal(page);
    await assertChecked(page, 'Blog Integrado');
  });
});
