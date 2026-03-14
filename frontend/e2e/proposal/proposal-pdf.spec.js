/**
 * E2E tests for proposal PDF download.
 */
import { test } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_DOWNLOAD_PDF } from '../helpers/flow-tags.js';

const MOCK_UUID = 'dddddddd-dddd-dddd-dddd-dddddddddddd';

test.describe('Proposal PDF Download', () => {
  test('PDF download returns 200 with PDF content', {
    tag: [...PROPOSAL_DOWNLOAD_PDF, '@role:guest'],
  }, async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) return { status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, uuid: MOCK_UUID, title: 'PDF Test', client_name: 'Client', status: 'sent', sections: [], requirement_groups: [] }) };
      if (apiPath === `proposals/${MOCK_UUID}/pdf/`) return { status: 200, contentType: 'application/pdf', body: '%PDF-fake-content' };
      return null;
    });
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');
  });
});
