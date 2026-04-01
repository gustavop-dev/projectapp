/**
 * E2E tests for proposal PDF download (client clicks floating PDF button → fetch PDF API).
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_DOWNLOAD_PDF } from '../helpers/flow-tags.js';

const MOCK_UUID = 'dddddddd-dddd-dddd-dddd-dddddddddddd';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'PDF Test',
  client_name: 'Client',
  status: 'sent',
  language: 'es',
  total_investment: '100000',
  currency: 'COP',
  created_at: '2026-03-01T12:00:00Z',
  sections: [
    {
      id: 1,
      section_type: 'greeting',
      title: 'Hola',
      order: 0,
      is_enabled: true,
      content_json: { clientName: 'Client', inspirationalQuote: 'Quote' },
    },
  ],
  requirement_groups: [],
};

test.describe('Proposal PDF Download', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('clicking Descargar PDF triggers successful PDF request', {
    tag: [...PROPOSAL_DOWNLOAD_PDF, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === `proposals/${MOCK_UUID}/` && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      if (apiPath.startsWith(`proposals/${MOCK_UUID}/pdf`) && method === 'GET') {
        return { status: 200, contentType: 'application/pdf', body: '%PDF-1.4 test' };
      }
      return null;
    });

    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`, { waitUntil: 'domcontentloaded' });
    const pdfBtn = page.getByTitle('Descargar PDF');
    await pdfBtn.waitFor({ state: 'visible', timeout: 30000 });

    const pdfResponse = page.waitForResponse(
      (res) =>
        res.url().includes(`/api/proposals/${MOCK_UUID}/pdf`) &&
        res.request().method() === 'GET',
    );
    await pdfBtn.click();
    const res = await pdfResponse;
    expect(res.status()).toBe(200);
    const ct = res.headers()['content-type'] || '';
    expect(ct).toMatch(/pdf/i);
  });
});
