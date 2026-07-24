/**
 * E2E tests for graceful expired proposal handling.
 *
 * @flow: proposal-expired-graceful
 *
 * Covers: 410 response renders ProposalExpired component with client name,
 * proposal title, WhatsApp reactivation CTA, and email contact option.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_EXPIRED_GRACEFUL } from '../helpers/flow-tags.js';

const MOCK_UUID = 'e1111111-1111-1111-1111-111111111111';

const expiredPayload = {
  error: 'This proposal has expired.',
  client_name: 'María García',
  title: 'Landing Profesional — María',
  uuid: MOCK_UUID,
  expired_at: '2026-02-28T12:00:00Z',
};

function setup410Mock(page) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return {
        status: 410,
        contentType: 'application/json',
        body: JSON.stringify(expiredPayload),
      };
    }
    return null;
  });
}

// New behaviour: an expired proposal returns 200 with the full proposal + expired_meta,
// so the whole proposal renders under a persistent banner (rather than the 410 fallback page).
const expiredFullProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Landing Profesional — María',
  client_name: 'María García',
  status: 'sent',
  language: 'es',
  total_investment: '15000.00',
  currency: 'COP',
  expired_meta: {
    expired_at: '2026-02-28T12:00:00Z',
    seller_name: 'Gustavo',
    whatsapp_url: 'https://wa.me/573001112222',
  },
  sections: [
    { id: 1, section_type: 'greeting', title: '👋 Bienvenido', order: 0, is_enabled: true, content_json: { clientName: 'María García', inspirationalQuote: 'Design is how it works.' } },
    { id: 2, section_type: 'executive_summary', title: '🧾 Resumen', order: 1, is_enabled: true, content_json: { index: '1', title: 'Resumen ejecutivo', paragraphs: ['Solución diseñada para escalar.'], highlightsTitle: 'Incluye', highlights: ['Diseño UX'] } },
  ],
  requirement_groups: [],
};

function setup200ExpiredMock(page) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(expiredFullProposal) };
    }
    return null;
  });
}

test.describe('Expired Proposal Graceful Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('renders expired message with client name', {
    tag: [...PROPOSAL_EXPIRED_GRACEFUL, '@role:guest'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display flow — the client views the expired proposal; there is no in-page action, the render is asserted by concrete content)
    await setup410Mock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    await expect(page.getByText(/María García, esta propuesta ha expirado/)).toBeVisible({ timeout: 10000 });
  });

  test('renders proposal title in description', {
    tag: [...PROPOSAL_EXPIRED_GRACEFUL, '@role:guest'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display flow — expired proposal view; render asserted by concrete content)
    await setup410Mock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    await expect(page.getByText(/Landing Profesional — María/)).toBeVisible({ timeout: 10000 });
  });

  test('shows WhatsApp reactivation button', {
    tag: [...PROPOSAL_EXPIRED_GRACEFUL, '@role:guest'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display flow — expired proposal view; the reactivation CTA is asserted by its href)
    await setup410Mock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    const whatsappLink = page.getByRole('link', { name: /Solicitar reactivación/ });
    await expect(whatsappLink).toBeVisible({ timeout: 10000 });

    const href = await whatsappLink.getAttribute('href');
    expect(href).toContain('wa.me');
    expect(href).toContain('Landing%20Profesional');
  });

  test('shows email contact button', {
    tag: [...PROPOSAL_EXPIRED_GRACEFUL, '@role:guest'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display flow — expired proposal view; the email CTA is asserted by its mailto href)
    await setup410Mock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    const emailLink = page.getByRole('link', { name: /Email/ });
    await expect(emailLink).toBeVisible({ timeout: 10000 });

    const href = await emailLink.getAttribute('href');
    expect(href).toContain('mailto:');
  });

  test('does not render main proposal sections on 410', {
    tag: [...PROPOSAL_EXPIRED_GRACEFUL, '@role:guest'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display flow — asserts the 410 state suppresses the live proposal, by absence)
    await setup410Mock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    // quality: allow-fragile-selector (checking proposal-wrapper absence confirms expired state renders instead of proposal)
    await expect(page.locator('.proposal-wrapper')).not.toBeVisible({ timeout: 5000 });

    // The expired message should be the main content
    await expect(page.getByText(/propuesta ha expirado/)).toBeVisible();
  });

  test('200 + expired_meta renders the full proposal under a persistent banner with the index toggle offset below it', {
    tag: [...PROPOSAL_EXPIRED_GRACEFUL, '@role:guest'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display flow — asserts the 200+expired_meta variant renders the full proposal under a persistent banner)
    await setup200ExpiredMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    // Persistent expired banner is shown OVER the full proposal (not the 410 fallback page).
    await expect(page.getByText(/Esta propuesta expiró/)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/Gustavo te envíe una versión actualizada/)).toBeVisible();
    // The full proposal renders (the 410 page would not mount .proposal-wrapper).
    // quality: allow-fragile-selector (the proposal viewer root has no testid; its presence distinguishes the full render from the 410 fallback)
    await expect(page.locator('.proposal-wrapper')).toBeVisible();

    // The index toggle drops below the banner (bannerActive → top-28 sm:top-20, no overlap).
    const toggle = page.getByTestId('index-toggle');
    await expect(toggle).toBeVisible();
    await expect(toggle).toHaveClass(/top-28/);

    // Geometry check: the toggle's top edge is at/below the banner's bottom edge.
    // quality: allow-fragile-selector (the expired banner has no testid; scope by its fixed-top class for the no-overlap measurement)
    const bannerBox = await page.locator('div.fixed.top-0.z-\\[9998\\]').boundingBox();
    const toggleBox = await toggle.boundingBox();
    expect(toggleBox.y).toBeGreaterThanOrEqual(bannerBox.y + bannerBox.height - 2);
  });
});
