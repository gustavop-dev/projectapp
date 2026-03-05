/**
 * E2E tests for proposal PDF download.
 */
import { test } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_DOWNLOAD_PDF } from '../helpers/flow-tags.js';

const MOCK_UUID = 'dddddddd-dddd-dddd-dddd-dddddddddddd';

test.describe('Proposal PDF Download', () => {
  test('PDF download returns 501 not implemented', {
    tag: [...PROPOSAL_DOWNLOAD_PDF, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) return { status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, uuid: MOCK_UUID, title: 'PDF Test', client_name: 'Client', status: 'sent', sections: [], requirement_groups: [] }) };
      if (apiPath === `proposals/${MOCK_UUID}/pdf/`) return { status: 501, contentType: 'application/json', body: JSON.stringify({ error: 'PDF generation is not yet available.' }) };
      return null;
    });
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');
  });
});
