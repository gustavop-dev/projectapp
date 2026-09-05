/**
 * E2E tests for the hosting plan terms shown in the public proposal's
 * investment section.
 *
 * @flow: proposal-hosting-plan-terms
 * Covers: the nine-month (40% discount) billing tier renders, the free-month
 * gift bucket renders and obeys its visibility checkbox, and the PDF-only
 * renewal note is NEVER leaked into the web view — even though it travels
 * through the same hostingPlan payload as the rest of the section.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_HOSTING_PLAN_TERMS } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-b05714b1a70e';

const DISTINCTIVE_RENEWAL_TEXT = 'RENOVACION-SOLO-PDF-9f3a1c-nunca-en-la-web';
const HIDDEN_GIFT_TEXT = 'REGALO-OCULTO-4b7e2d-nunca-visible-al-cliente';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Hosting Plan Terms Proposal',
  client_name: 'Hosting Client',
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
      content_json: { clientName: 'Hosting Client', inspirationalQuote: '' },
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
        hostingPlan: {
          title: 'Hosting, Mantenimiento y Soporte',
          description: 'Infraestructura optimizada para proyectos de alto rendimiento.',
          hostingPercent: 80,
          billingTiers: [
            { frequency: 'nine_month', months: 9, discountPercent: 40, label: 'Cada 9 meses', badge: 'Máximo descuento' },
            { frequency: 'semiannual', months: 6, discountPercent: 20, label: 'Semestral', badge: '20% dcto' },
            { frequency: 'quarterly', months: 3, discountPercent: 10, label: 'Trimestral', badge: '10% dcto' },
          ],
          freeMonths: 1,
          renewalNote: DISTINCTIVE_RENEWAL_TEXT,
        },
      },
    },
  ],
  requirement_groups: [],
};

function setupMock(page, hostingPlanOverrides = {}) {
  const proposal = structuredClone(mockProposal);
  const investment = proposal.sections.find(s => s.section_type === 'investment');
  Object.assign(investment.content_json.hostingPlan, hostingPlanOverrides);
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposal) };
    }
    return null;
  });
}

async function openInvestmentSection(page) {
  await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

  const nextBtn = page.getByTestId('nav-next');
  await expect(nextBtn).toBeVisible({ timeout: 15000 });
  await nextBtn.click();

  await expect(page.getByText(/inversi[oó]n/i).first()).toBeVisible({ timeout: 10000 });
}

test.describe('Proposal Hosting Plan Terms', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
      localStorage.setItem(`investment_onboarding_seen_${_uuid}`, 'true');
    }, MOCK_UUID);
  });

  // Catches: a hosting-plan wiring bug that drops the nine-month tier, hides the
  // free-month bucket, or — the regression that actually matters here —
  // leaks the PDF-only renewal note into the public web view. The unit test
  // (Investment.test.js) already proves this in isolation; this is the first
  // check that proves it end-to-end through the real uuid fetch → render path.
  test('shows the nine-month tier and free-month bucket, and never leaks the renewal note', {
    tag: [...PROPOSAL_HOSTING_PLAN_TERMS, '@role:guest', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the proposal link is the guest's only real entry
    // point — it is shared via email/WhatsApp, there is no in-app UI to browse to
    // it from; ?mode=detailed is the documented E2E/direct-link gateway bypass,
    // matching every other spec in e2e/proposal/)
    await setupMock(page);
    await openInvestmentSection(page);

    await expect(page.getByText('Cada 9 meses', { exact: true })).toBeVisible();
    // Nine-month tier (40% discount) badge is visible.
    await expect(page.getByText('Máximo descuento')).toBeVisible({ timeout: 10000 });

    // Free-month gift bucket copy is visible.
    await expect(page.getByText('1 mes de hosting gratis')).toBeVisible();

    // The PDF-only renewal note must never render in the web view.
    await expect(page.getByText(DISTINCTIVE_RENEWAL_TEXT)).toHaveCount(0);
  });

  // Catches: the visibility checkbox failing to reach the public view. The
  // count stays at 1 on purpose — under the old rule that alone rendered the
  // bucket, so this only passes if the flag is what gates it.
  test('honors the visibility checkbox: an unchecked free-month block never reaches the client', {
    tag: [...PROPOSAL_HOSTING_PLAN_TERMS, '@role:guest', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the proposal link is the guest's only real entry
    // point — it is shared via email/WhatsApp, there is no in-app UI to browse to
    // it from; ?mode=detailed is the documented E2E/direct-link gateway bypass,
    // matching every other spec in e2e/proposal/)
    await setupMock(page, {
      freeMonths: 1,
      freeMonthsVisible: false,
      freeMonthNote: HIDDEN_GIFT_TEXT,
    });
    await openInvestmentSection(page);

    // The rest of the hosting subsection still renders — only the gift is gone.
    await expect(page.getByText('Cada 9 meses', { exact: true })).toBeVisible();
    await expect(page.getByText(HIDDEN_GIFT_TEXT)).toHaveCount(0);
    await expect(page.getByText('mes de hosting gratis')).toHaveCount(0);
  });
});
