/**
 * E2E tests for the magic-link recovery form on expired proposals.
 *
 * @flow: proposal-magic-link-request
 *
 * Covers: a guest who lands on an expired proposal submits their email through
 * the form in ProposalExpired.vue to request a fresh proposal link.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_MAGIC_LINK_REQUEST } from '../helpers/flow-tags.js';

const MOCK_UUID = 'e2222222-2222-2222-2222-222222222222';

const expiredPayload = {
  error: 'This proposal has expired.',
  client_name: 'Carlos Rivera',
  title: 'Web Corporativa — Carlos',
  uuid: MOCK_UUID,
  expired_at: '2026-02-28T12:00:00Z',
};

function setupMock(page, { requestLinkStatus = 200 } = {}) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 410, contentType: 'application/json', body: JSON.stringify(expiredPayload) };
    }
    if (apiPath === 'proposals/request-link/' && method === 'POST') {
      if (requestLinkStatus === 200) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true }) };
      }
      return { status: requestLinkStatus, contentType: 'application/json', body: JSON.stringify({ detail: 'error' }) };
    }
    return null;
  });
}

test.describe('Proposal Magic Link Request (expired recovery)', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('expired view renders the magic-link form with email input and submit button', {
    tag: [...PROPOSAL_MAGIC_LINK_REQUEST, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`, { waitUntil: 'domcontentloaded' });

    await expect(page.getByText(/¿Perdiste el enlace\?/)).toBeVisible({ timeout: 10000 });
    await expect(page.getByPlaceholder('tu@email.com')).toBeVisible();
    await expect(page.getByRole('button', { name: /Enviar/ })).toBeVisible();
  });

  test('submitting a valid email shows the confirmation message', {
    tag: [...PROPOSAL_MAGIC_LINK_REQUEST, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`, { waitUntil: 'domcontentloaded' });

    const emailInput = page.getByPlaceholder('tu@email.com');
    await expect(emailInput).toBeVisible({ timeout: 10000 });
    await emailInput.fill('carlos@example.com');
    await page.getByRole('button', { name: /Enviar/ }).click();

    await expect(
      page.getByText(/Si tenemos propuestas asociadas a ese email, recibirás un enlace en breve\./),
    ).toBeVisible({ timeout: 5000 });
  });

  test('POST hits proposals/request-link/ with the typed email', {
    tag: [...PROPOSAL_MAGIC_LINK_REQUEST, '@role:guest'],
  }, async ({ page }) => {
    let capturedEmail = null;
    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 410, contentType: 'application/json', body: JSON.stringify(expiredPayload) };
      }
      if (apiPath === 'proposals/request-link/' && method === 'POST') {
        const raw = route.request().postData();
        if (raw) capturedEmail = JSON.parse(raw).email;
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true }) };
      }
      return null;
    });

    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`, { waitUntil: 'domcontentloaded' });

    const emailInput = page.getByPlaceholder('tu@email.com');
    await expect(emailInput).toBeVisible({ timeout: 10000 });
    await emailInput.fill('carlos@example.com');
    await page.getByRole('button', { name: /Enviar/ }).click();

    await expect(() => expect(capturedEmail).toBe('carlos@example.com')).toPass({ timeout: 5000 });
  });
});
