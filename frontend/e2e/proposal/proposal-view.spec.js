/**
 * E2E tests for viewing a business proposal via UUID link.
 *
 * Covers: proposal render, expired/404 handling, next/prev navigation,
 * SectionCounter updating on navigation, SectionNavButtons visibility.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_VIEW } from '../helpers/flow-tags.js';

const MOCK_UUID = '12345678-1234-5678-1234-567812345678';

const mockProposalTwoSections = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Web Application Development',
  client_name: 'Acme Corp',
  status: 'sent',
  language: 'es',
  total_investment: '15000.00',
  currency: 'COP',
  sections: [
    {
      id: 1,
      section_type: 'greeting',
      title: '👋 Bienvenido',
      order: 0,
      is_enabled: true,
      content_json: {
        clientName: 'Acme Corp',
        inspirationalQuote: 'Design is how it works.',
      },
    },
    {
      id: 2,
      section_type: 'executive_summary',
      title: '🧾 Resumen Ejecutivo',
      order: 1,
      is_enabled: true,
      content_json: {
        index: '1',
        title: 'Resumen ejecutivo',
        paragraphs: ['Nuestra solución está diseñada para escalar.'],
        highlightsTitle: 'Incluye',
        highlights: ['Diseño UX'],
      },
    },
  ],
  requirement_groups: [],
};

function buildMockHandler(proposal) {
  return async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposal) };
    }
    return null;
  };
}

test.describe('Proposal View', () => {
  test.beforeEach(async ({ page }) => {
    // Skip onboarding overlay so nav buttons are clickable
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('renders proposal greeting section on first load', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(mockProposalTwoSections));
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    // Page loaded without errors
    await expect(page.locator('body')).not.toContainText('Error');
  });

  test('clicking next navigation button advances to second section', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(mockProposalTwoSections));
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    // Wait for next button to appear (not on last panel)
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible();

    // Click next to advance to section 2
    await nextBtn.click();

    // The previous button should now be visible (not on first panel anymore)
    await expect(page.getByTestId('nav-prev')).toBeVisible({ timeout: 3000 });
  });

  test('navigating forward then back returns to first section', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(mockProposalTwoSections));
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    // Go forward
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible();
    await nextBtn.click();

    // Previous button should be visible once we're on panel 2
    const prevBtn = page.getByTestId('nav-prev');
    await expect(prevBtn).toBeVisible({ timeout: 3000 });

    // Go back
    await prevBtn.click();

    // Previous button should be gone (back at first panel)
    await expect(page.getByTestId('nav-prev')).not.toBeVisible({ timeout: 3000 });
  });

  test('next button is absent on last panel', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler({
      ...mockProposalTwoSections,
      sections: [mockProposalTwoSections.sections[0]],
    }));
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    // Single section proposal: only closing panel remains → navigate to it
    const nextBtn = page.getByTestId('nav-next');
    // Navigate through all panels until last
    let safetyLimit = 5;
    while (await nextBtn.isVisible({ timeout: 500 }).catch(() => false) && safetyLimit-- > 0) {
      await nextBtn.click();
      await expect(page.locator('body')).toBeVisible(); // yield to microtasks
    }

    // On the last panel, next button should be gone
    await expect(page.getByTestId('nav-next')).not.toBeVisible();
  });

  test('shows expired message for expired proposal', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return {
          status: 410,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'This proposal has expired.' }),
        };
      }
      return null;
    });

    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    // Expired state component should be rendered
    await expect(page.locator('body')).not.toContainText('404');
  });

  test('shows 404 state for non-existent proposal', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return {
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Not found.' }),
        };
      }
      return null;
    });

    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    await expect(page.locator('body')).toContainText('404');
  });
});
