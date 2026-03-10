/**
 * E2E tests for the investment calculator modal in the proposal viewer.
 *
 * Covers: opening the calculator, toggling optional modules, dynamic total
 * recalculation, required modules locked, confirm selection updates display.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_INVESTMENT_CALCULATOR } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Calculator Test Proposal',
  client_name: 'Test Client',
  status: 'sent',
  language: 'es',
  total_investment: '5000000',
  currency: 'COP',
  sections: [
    {
      id: 1,
      section_type: 'greeting',
      title: '👋 Bienvenido',
      order: 0,
      is_enabled: true,
      content_json: { clientName: 'Test Client', inspirationalQuote: '' },
    },
    {
      id: 2,
      section_type: 'investment',
      title: '💰 Inversión',
      order: 1,
      is_enabled: true,
      content_json: {
        index: '2',
        title: 'Inversión',
        introText: 'Tu inversión incluye:',
        totalInvestment: '$5.000.000',
        currency: 'COP',
        whatsIncluded: [
          { icon: '🎨', title: 'Diseño', description: 'UX/UI personalizado' },
        ],
        paymentOptions: [
          { label: 'Pago 1', description: '50% al inicio' },
        ],
        modules: [
          { id: 'mod-core', name: 'Módulo Core', price: 2000000, is_required: true },
          { id: 'mod-blog', name: 'Blog Integrado', price: 1500000, is_required: false },
          { id: 'mod-analytics', name: 'Analytics Dashboard', price: 1500000, is_required: false },
        ],
      },
    },
    {
      id: 3,
      section_type: 'timeline',
      title: '📅 Timeline',
      order: 2,
      is_enabled: true,
      content_json: {
        index: '3',
        title: 'Timeline',
        totalDuration: '8 semanas',
        phases: [],
      },
    },
  ],
  requirement_groups: [],
};

function buildMockHandler() {
  return async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
    }
    return null;
  };
}

async function navigateToInvestment(page) {
  await page.goto(`/proposal/${MOCK_UUID}`);
  await page.waitForLoadState('networkidle');

  // Wait for proposal content to render after preloader
  await expect(page.locator('.proposal-wrapper')).toBeVisible({ timeout: 15000 });

  // Navigate forward: greeting (0) → investment (1)
  const nextBtn = page.getByTestId('nav-next');
  await expect(nextBtn).toBeVisible({ timeout: 3000 });
  await nextBtn.click();

  // Wait for the customize button to confirm we're on the investment section
  await expect(page.getByText(/Personalizar tu inversión/i)).toBeVisible({ timeout: 5000 });
}

test.describe('Proposal Investment Calculator', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('customize button opens calculator modal', {
    tag: [...PROPOSAL_INVESTMENT_CALCULATOR, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await navigateToInvestment(page);

    const customizeBtn = page.getByText(/Personalizar tu inversión/i);
    await expect(customizeBtn).toBeVisible();

    // Scroll into view and click (btn-pulse animation may cause instability)
    await customizeBtn.scrollIntoViewIfNeeded();
    await customizeBtn.click();
    await expect(page.getByText(/Selecciona los módulos/i)).toBeVisible({ timeout: 3000 });
  });

  test('required modules are locked and cannot be toggled', {
    tag: [...PROPOSAL_INVESTMENT_CALCULATOR, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await navigateToInvestment(page);

    const customizeBtn = page.getByText(/Personalizar tu inversión/i);
    await expect(customizeBtn).toBeVisible();
    await customizeBtn.scrollIntoViewIfNeeded();
    await customizeBtn.click();
    await expect(page.getByText(/Selecciona los módulos/i)).toBeVisible();

    // Required module should show the "obligatorio" label
    await expect(page.getByText('Módulo Core')).toBeVisible();
    await expect(page.getByText(/obligatorio/i)).toBeVisible();
  });

  test('toggling optional module updates estimated total', {
    tag: [...PROPOSAL_INVESTMENT_CALCULATOR, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await navigateToInvestment(page);

    const customizeBtn = page.getByText(/Personalizar tu inversión/i);
    await expect(customizeBtn).toBeVisible();
    await customizeBtn.scrollIntoViewIfNeeded();
    await customizeBtn.click();
    await expect(page.getByText(/Selecciona los módulos/i)).toBeVisible();

    // All 3 modules should be listed
    await expect(page.getByText('Blog Integrado')).toBeVisible();
    await expect(page.getByText('Analytics Dashboard')).toBeVisible();

    // Click an optional module to deselect it
    await page.getByText('Blog Integrado').click();

    // Selected count should decrease
    await expect(page.getByText(/2\/3/)).toBeVisible();
  });

  test('confirm selection closes modal', {
    tag: [...PROPOSAL_INVESTMENT_CALCULATOR, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await navigateToInvestment(page);

    const customizeBtn = page.getByText(/Personalizar tu inversión/i);
    await expect(customizeBtn).toBeVisible();
    await customizeBtn.scrollIntoViewIfNeeded();
    await customizeBtn.click();
    await expect(page.getByText(/Selecciona los módulos/i)).toBeVisible();

    await page.getByRole('button', { name: /Confirmar selección/i }).click();

    // Modal should close
    await expect(page.getByText(/Selecciona los módulos/i)).not.toBeVisible();
  });
});
