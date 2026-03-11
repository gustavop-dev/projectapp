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

const MOCK_UUID = 'expired-uuid-1234-5678-abcdef123456';

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

test.describe('@flow: proposal-expired-graceful — Expired Proposal Graceful Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('renders expired message with client name', {
    tag: [...PROPOSAL_EXPIRED_GRACEFUL, '@role:guest'],
  }, async ({ page }) => {
    await setup410Mock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    await expect(page.getByText(/María García, esta propuesta ha expirado/)).toBeVisible({ timeout: 10000 });
  });

  test('renders proposal title in description', {
    tag: [...PROPOSAL_EXPIRED_GRACEFUL, '@role:guest'],
  }, async ({ page }) => {
    await setup410Mock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    await expect(page.getByText(/Landing Profesional — María/)).toBeVisible({ timeout: 10000 });
  });

  test('shows WhatsApp reactivation button', {
    tag: [...PROPOSAL_EXPIRED_GRACEFUL, '@role:guest'],
  }, async ({ page }) => {
    await setup410Mock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    const whatsappLink = page.getByRole('link', { name: /Solicitar reactivación/ });
    await expect(whatsappLink).toBeVisible({ timeout: 10000 });

    const href = await whatsappLink.getAttribute('href');
    expect(href).toContain('wa.me');
    expect(href).toContain('Landing%20Profesional');
  });

  test('shows email contact button', {
    tag: [...PROPOSAL_EXPIRED_GRACEFUL, '@role:guest'],
  }, async ({ page }) => {
    await setup410Mock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    const emailLink = page.getByRole('link', { name: /Email/ });
    await expect(emailLink).toBeVisible({ timeout: 10000 });

    const href = await emailLink.getAttribute('href');
    expect(href).toContain('mailto:');
  });

  test('does not render main proposal sections on 410', {
    tag: [...PROPOSAL_EXPIRED_GRACEFUL, '@role:guest'],
  }, async ({ page }) => {
    await setup410Mock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // The proposal wrapper should NOT be visible
    await expect(page.locator('.proposal-wrapper')).not.toBeVisible({ timeout: 5000 });

    // The expired message should be the main content
    await expect(page.getByText(/propuesta ha expirado/)).toBeVisible();
  });
});
