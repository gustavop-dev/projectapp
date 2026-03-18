/**
 * E2E tests for proposal section onboarding tooltips.
 *
 * @flow:proposal-section-onboarding
 * Covers: multi-step onboarding overlay on first visit, step progression,
 * skip/dismiss behavior, localStorage suppression on repeat visits,
 * investment onboarding trigger on section navigation.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_SECTION_ONBOARDING } from '../helpers/flow-tags.js';

const MOCK_UUID = 'onb-1111-2222-3333-4444-555555555555';

function _buildSection(id, type, title, order, contentJson = {}) {
  return {
    id,
    section_type: type,
    title,
    order,
    is_enabled: true,
    is_wide_panel: type === 'functional_requirements',
    content_json: contentJson,
  };
}

const mockProposal = {
  id: 60,
  uuid: MOCK_UUID,
  title: 'Onboarding Test Proposal',
  client_name: 'Onboarding Client',
  client_email: 'onboard@test.com',
  language: 'es',
  status: 'sent',
  total_investment: '7000000',
  currency: 'COP',
  view_count: 1,
  sent_at: '2026-01-01T00:00:00Z',
  expires_at: '2026-06-01T00:00:00Z',
  sections: [
    _buildSection(601, 'greeting', '👋 Bienvenido', 0, {
      clientName: 'Onboarding Client',
      inspirationalQuote: 'Design is intelligence made visible.',
    }),
    _buildSection(602, 'executive_summary', '🧾 Resumen ejecutivo', 1, {
      index: '1', title: 'Resumen ejecutivo',
      paragraphs: ['Solución diseñada para escalar.'],
      highlightsTitle: 'Incluye', highlights: ['Diseño UX'],
    }),
    _buildSection(603, 'investment', '💰 Inversión', 2, {
      index: '2', title: 'Inversión', introText: '', totalInvestment: '7000000', currency: 'COP',
      whatsIncluded: [], paymentOptions: [], paymentMethods: [], valueReasons: [],
      modules: [
        { id: 'mod1', name: 'Módulo Web', price: 5000000, included: true, is_required: true },
        { id: 'mod2', name: 'Módulo App', price: 2000000, included: false, is_required: false },
      ],
    }),
    _buildSection(604, 'functional_requirements', '🧩 Requerimientos', 3, {
      index: '3', title: 'Requerimientos', intro: '',
      groups: [{ id: 'views', icon: '🖥️', title: 'Vistas', description: '', items: [] }],
      additionalModules: [],
    }),
  ],
  requirement_groups: [],
};

function buildMockHandler() {
  return async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockProposal),
      };
    }
    if (apiPath === `proposals/${MOCK_UUID}/record-view/`) {
      return { status: 200, contentType: 'application/json', body: '{}' };
    }
    if (apiPath.includes('/track/')) {
      return { status: 200, contentType: 'application/json', body: '{}' };
    }
    return null;
  };
}

test.describe('Proposal Section Onboarding', () => {
  test('first visit shows onboarding overlay with step 1', {
    tag: [...PROPOSAL_SECTION_ONBOARDING, '@role:guest'],
  }, async ({ page }) => {
    // Do NOT set proposal_onboarding_seen — simulate first visit
    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    // Onboarding backdrop should be visible
    const backdrop = page.getByTestId('onboarding-backdrop');
    await expect(backdrop).toBeVisible({ timeout: 15000 });

    // First step title should be visible (dark mode toggle step)
    await expect(page.getByText('Modo claro y oscuro')).toBeVisible();

    // Progress indicator should show "1/N"
    await expect(page.getByText(/^1\//)).toBeVisible();
  });

  test('clicking "Siguiente" advances to step 2', {
    tag: [...PROPOSAL_SECTION_ONBOARDING, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    // Wait for onboarding to appear
    await expect(page.getByTestId('onboarding-backdrop')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Modo claro y oscuro')).toBeVisible();

    // Click next
    await page.getByRole('button', { name: 'Siguiente' }).click();

    // Step 2: section index
    await expect(page.getByText('Índice de secciones')).toBeVisible();
    await expect(page.getByText(/^2\//)).toBeVisible();
  });

  test('clicking "Omitir" dismisses onboarding overlay', {
    tag: [...PROPOSAL_SECTION_ONBOARDING, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    await expect(page.getByTestId('onboarding-backdrop')).toBeVisible({ timeout: 15000 });

    // Click skip
    await page.getByRole('button', { name: 'Omitir' }).click();

    // Backdrop should disappear
    await expect(page.getByTestId('onboarding-backdrop')).not.toBeVisible();
  });

  test('completing onboarding sets localStorage flag', {
    tag: [...PROPOSAL_SECTION_ONBOARDING, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    await expect(page.getByTestId('onboarding-backdrop')).toBeVisible({ timeout: 15000 });

    // Click skip to complete quickly
    await page.getByRole('button', { name: 'Omitir' }).click();
    await expect(page.getByTestId('onboarding-backdrop')).not.toBeVisible();

    // Check localStorage
    const flag = await page.evaluate(() => localStorage.getItem('proposal_onboarding_seen'));
    expect(flag).toBe('true');
  });

  test('repeat visit does NOT show onboarding overlay', {
    tag: [...PROPOSAL_SECTION_ONBOARDING, '@role:guest'],
  }, async ({ page }) => {
    // Set localStorage to simulate repeat visit
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });

    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    // Verify proposal loaded, then check onboarding is absent
    await expect(page.locator('[data-section-type="greeting"]')).toBeVisible({ timeout: 15000 });

    // Backdrop should NOT be visible
    await expect(page.getByTestId('onboarding-backdrop')).not.toBeVisible();
  });

  test('last step shows "Entendido" button instead of "Siguiente"', {
    tag: [...PROPOSAL_SECTION_ONBOARDING, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    await expect(page.getByTestId('onboarding-backdrop')).toBeVisible({ timeout: 15000 });

    // Advance through all steps until the last one
    let hasNext = true;
    let maxSteps = 10;
    while (hasNext && maxSteps > 0) {
      maxSteps--;
      const nextBtn = page.getByRole('button', { name: 'Siguiente' });
      const doneBtn = page.getByRole('button', { name: 'Entendido' });

      if (await doneBtn.isVisible()) {
        hasNext = false;
        // On last step, "Entendido" should be visible and "Siguiente" should not
        await expect(doneBtn).toBeVisible();
        await expect(nextBtn).not.toBeVisible();
      } else {
        await nextBtn.click();
        // Wait for step transition to complete
        await nextBtn.or(doneBtn).waitFor({ state: 'visible', timeout: 5000 });
      }
    }

    expect(hasNext).toBe(false);
  });
});
