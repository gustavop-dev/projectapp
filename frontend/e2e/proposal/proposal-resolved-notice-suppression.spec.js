/**
 * E2E tests for resolved-status notice suppression on the public proposal view.
 *
 * @flow: proposal-resolved-notice-suppression
 *
 * Covers: once a proposal's status is settled (accepted/finished), the public
 * page at /proposal/:uuid must hide the expiration countdown (ExpirationBadge)
 * and the limited-time discount banner (Investment .discount-banner) — both
 * are wired from the API's top-level `status` field via `isProposalResolved`
 * (page) and the `proposalStatus` prop (Investment.vue). While the proposal is
 * still open (sent) both notices must keep rendering.
 *
 * Bug this catches: a client who already accepted (or whose proposal is
 * finished) still sees "expires in Xh" / a limited-time-discount push — the
 * unit test (Investment.test.js:144-164) only proves the component itself
 * hides the banner given a `proposalStatus` prop; it does not prove the real
 * page ever threads the API's `status` field into that prop (or into
 * `isProposalResolved` for the ExpirationBadge). A regression here (e.g. the
 * page prop wiring silently dropped, or the resolved-statuses list drifting)
 * would go undetected without this spec.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_RESOLVED_NOTICE_SUPPRESSION } from '../helpers/flow-tags.js';

const MOCK_UUID = 'ac222222-2222-2222-2222-222222222222';

function buildProposal(status) {
  return {
    id: 77,
    uuid: MOCK_UUID,
    title: 'Resolved Notice Suppression Test',
    client_name: 'Ana Torres',
    status,
    language: 'es',
    total_investment: '12000000',
    currency: 'COP',
    discount_percent: 15,
    discounted_investment: '10200000',
    expires_at: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
    sections: [
      {
        id: 1, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true,
        content_json: { clientName: 'Ana Torres', inspirationalQuote: '' },
      },
      {
        id: 2, section_type: 'investment', title: 'Inversión', order: 1, is_enabled: true,
        content_json: {
          index: '2',
          title: 'Inversión',
          introText: 'Tu inversión incluye:',
          totalInvestment: '$12.000.000',
          currency: 'COP',
          whatsIncluded: [],
          paymentOptions: [{ label: 'Pago único', description: '$12.000.000' }],
          modules: [
            { id: 'mod-core', name: 'Módulo Core', price: 6000000, is_required: true },
          ],
          valueReasons: [],
        },
      },
    ],
    requirement_groups: [],
  };
}

function setupMock(page, proposal) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposal) };
    }
    return null;
  });
}

test.describe('Proposal Resolved Notice Suppression', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  for (const status of ['accepted', 'finished']) {
    test(`hides the expiration badge and discount banner when proposal status is ${status}`, {
      tag: [...PROPOSAL_RESOLVED_NOTICE_SUPPRESSION, '@outcome:display', '@role:guest'],
    }, async ({ page }) => {
      // quality: allow-deep-link (the proposal link is the guest's only real entry
      // point — it is shared via email/WhatsApp, there is no in-app UI to browse to
      // it from; ?mode=detailed is the documented E2E/direct-link gateway bypass,
      // matching every other spec in e2e/proposal/)
      await setupMock(page, buildProposal(status));
      await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

      // Navigate from greeting to investment — a real interaction, and the
      // section where the discount banner (and the persistent ExpirationBadge
      // overlay) would render if the resolved status were not suppressing them.
      const nextBtn = page.getByTestId('nav-next');
      await expect(nextBtn).toBeVisible({ timeout: 15000 });
      await nextBtn.click();
      await expect(page.getByRole('heading', { name: /Inversión/ })).toBeVisible({ timeout: 5000 });

      await expect(page.getByText(/Expira en/)).toHaveCount(0);
      await expect(page.getByText(/15% OFF/)).toHaveCount(0);
    });
  }

  test('shows the expiration badge and discount banner while the proposal is still open (sent)', {
    tag: [...PROPOSAL_RESOLVED_NOTICE_SUPPRESSION, '@outcome:display', '@role:guest'],
  }, async ({ page }) => {
    // quality: allow-deep-link (control case for the same magic-link entry point
    // used by every spec in e2e/proposal/ — see the accepted/finished cases above)
    await setupMock(page, buildProposal('sent'));
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();
    await expect(page.getByRole('heading', { name: /Inversión/ })).toBeVisible({ timeout: 5000 });

    await expect(page.getByText(/Expira en/)).toHaveCount(1);
    await expect(page.getByText(/15% OFF/)).toHaveCount(1);
  });
});
