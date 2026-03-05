/**
 * E2E tests for client responding to a proposal (accept/reject).
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_RESPOND } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

test.describe('Proposal Respond', () => {
  test('client can accept a proposal', {
    tag: [...PROPOSAL_RESPOND, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, uuid: MOCK_UUID, title: 'Test', client_name: 'Client', status: 'sent', sections: [], requirement_groups: [] }) };
      }
      if (apiPath === `proposals/${MOCK_UUID}/respond/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'accepted', message: 'Proposal accepted successfully.' }) };
      }
      return null;
    });
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');
  });

  test('client can reject a proposal', {
    tag: [...PROPOSAL_RESPOND, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, uuid: MOCK_UUID, title: 'Test', client_name: 'Client', status: 'viewed', sections: [], requirement_groups: [] }) };
      }
      if (apiPath === `proposals/${MOCK_UUID}/respond/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'rejected', message: 'Proposal rejected.' }) };
      }
      return null;
    });
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');
  });
});
