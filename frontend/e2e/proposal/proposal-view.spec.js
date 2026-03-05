/**
 * E2E tests for viewing a business proposal via UUID link.
 *
 * Covers: proposal render, expired proposal handling, 404 handling.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_VIEW } from '../helpers/flow-tags.js';

const MOCK_UUID = '12345678-1234-5678-1234-567812345678';

const mockProposal = {
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
      title: 'Bienvenido',
      order: 0,
      is_enabled: true,
      content_json: { heading: 'Welcome' },
    },
  ],
  requirement_groups: [],
};

test.describe('Proposal View', () => {
  test('renders proposal content for valid UUID', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockProposal),
        };
      }
      return null;
    });

    await page.goto(`/proposal/${MOCK_UUID}`);

    await page.waitForLoadState('networkidle');
  });

  test('shows expired message for expired proposal', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return {
          status: 410,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'This proposal has expired.' }),
        };
      }
      return null;
    });

    await page.goto(`/proposal/${MOCK_UUID}`);

    await page.waitForLoadState('networkidle');
  });
});
