/**
 * E2E tests for accessing a business proposal via its human-friendly slug URL.
 *
 * Covers: slug-based routing, UUID backward-compat, 404 on unknown slug.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_SLUG_ACCESS } from '../helpers/flow-tags.js';

const MOCK_UUID = 'a1b2c3d4-e5f6-7890-abcd-1234567890ab';
const MOCK_SLUG = 'empresa-demo-2026';

const baseProposal = {
  id: 10,
  uuid: MOCK_UUID,
  slug: MOCK_SLUG,
  title: 'Plataforma SaaS',
  client_name: 'Empresa Demo',
  status: 'sent',
  language: 'es',
  total_investment: '25000.00',
  currency: 'COP',
  sections: [
    {
      id: 1,
      section_type: 'greeting',
      title: '👋 Bienvenido',
      order: 0,
      is_enabled: true,
      content_json: {
        clientName: 'Empresa Demo',
        inspirationalQuote: 'La calidad nunca es un accidente.',
      },
    },
  ],
  requirement_groups: [],
};

function slugHandler(proposal) {
  return async ({ apiPath }) => {
    if (apiPath === `proposals/by-slug/${MOCK_SLUG}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposal) };
    }
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposal) };
    }
    return null;
  };
}

test.describe('Proposal Slug Access', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('proposal loads when accessed via slug URL', {
    tag: [...PROPOSAL_SLUG_ACCESS, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, slugHandler(baseProposal));
    await page.goto(`/proposal/${MOCK_SLUG}?mode=detailed`);
    await page.waitForLoadState('domcontentloaded');

    await expect(page.locator('body')).not.toContainText('404');
    await expect(page.locator('body')).not.toContainText('Error');
  });

  test('proposal still loads when accessed via UUID for backward compatibility', {
    tag: [...PROPOSAL_SLUG_ACCESS, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, slugHandler(baseProposal));
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('domcontentloaded');

    await expect(page.locator('body')).not.toContainText('404');
    await expect(page.locator('body')).not.toContainText('Error');
  });

  test('unknown slug renders the not-found state', {
    tag: [...PROPOSAL_SLUG_ACCESS, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath.startsWith('proposals/by-slug/')) {
        return { status: 404, contentType: 'application/json', body: '{"detail":"Not found."}' };
      }
      return null;
    });
    await page.goto('/proposal/slug-que-no-existe');
    await page.waitForLoadState('domcontentloaded');

    await expect(page.locator('body')).toContainText(/404|no encontr|not found/i);
  });
});
