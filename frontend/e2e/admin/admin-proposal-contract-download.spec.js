/**
 * E2E tests for admin proposal contract download flow.
 *
 * @flow:admin-proposal-contract-download
 * Covers: download links visible when contract exists, links point to correct
 *         API endpoints, links hidden when no contract.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_CONTRACT_DOWNLOAD } from '../helpers/flow-tags.js';

const PROPOSAL_ID = 1;
const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const existingContractDoc = {
  id: 10,
  document_type: 'contract',
  document_type_display: 'Contrato',
  title: 'Contrato de desarrollo',
  file: '/media/contracts/contract.pdf',
  is_generated: true,
  created_at: '2026-04-01T10:00:00Z',
};

const proposalWithContract = {
  id: PROPOSAL_ID,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'Download Test',
  client_name: 'Acme Corp',
  client_email: 'acme@example.com',
  language: 'es',
  status: 'negotiating',
  total_investment: '10000000',
  currency: 'COP',
  view_count: 3,
  sent_at: '2026-03-28T10:00:00Z',
  sections: [
    { id: 1, section_type: 'greeting', title: 'Saludo', order: 0, is_enabled: true, content_json: { clientName: 'Acme Corp' } },
  ],
  requirement_groups: [],
  proposal_documents: [existingContractDoc],
  contract_params: { contract_source: 'default' },
};

const proposalWithoutContract = {
  ...proposalWithContract,
  proposal_documents: [],
  contract_params: null,
};

test.describe('Admin Proposal Contract Download', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('shows download and draft links when contract exists', {
    tag: [...ADMIN_PROPOSAL_CONTRACT_DOWNLOAD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(proposalWithContract) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit?tab=documents`);
    await page.waitForLoadState('domcontentloaded');

    // Final PDF download link
    const downloadLink = page.getByRole('link', { name: /Descargar/i }).first();
    await expect(downloadLink).toBeVisible();
    await expect(downloadLink).toHaveAttribute('href', `/api/proposals/${PROPOSAL_ID}/contract/pdf/`);

    // Draft PDF download link
    const draftLink = page.getByRole('link', { name: /Borrador/i });
    await expect(draftLink).toBeVisible();
    await expect(draftLink).toHaveAttribute('href', `/api/proposals/${PROPOSAL_ID}/contract/draft-pdf/`);
  });

  test('shows "No generado" when no contract exists', {
    tag: [...ADMIN_PROPOSAL_CONTRACT_DOWNLOAD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(proposalWithoutContract) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit?tab=documents`);
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByText('No generado', { exact: true })).toBeVisible();
  });

  test('contract creation date shown when contract exists', {
    tag: [...ADMIN_PROPOSAL_CONTRACT_DOWNLOAD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(proposalWithContract) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit?tab=documents`);
    await page.waitForLoadState('domcontentloaded');

    // "Generado el" text should be visible
    await expect(page.getByText(/Generado el/i)).toBeVisible();
  });
});
