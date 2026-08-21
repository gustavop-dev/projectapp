/**
 * Public proposal Contract and terms mode.
 *
 * @flow:proposal-contract-terms
 * @flow:proposal-contract-draft-download
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import {
  PROPOSAL_CONTRACT_DRAFT_DOWNLOAD,
  PROPOSAL_CONTRACT_TERMS,
} from '../helpers/flow-tags.js';

const MOCK_UUID = 'ec111111-1111-1111-1111-111111111111';

const proposal = {
  id: 902,
  uuid: MOCK_UUID,
  title: 'Contrato E2E',
  client_name: 'Cliente Legal',
  created_at: '2026-08-21T12:00:00Z',
  language: 'es',
  status: 'sent',
  total_investment: '5000000',
  currency: 'COP',
  show_contract_terms: true,
  has_confirmed_module_selection: true,
  sections: [],
  requirement_groups: [],
};

const contractTerms = {
  title: 'Contrato de prestación de servicios',
  label: 'Borrador informativo',
  preamble_markdown: 'Entre las partes identificadas como XXX-XXX-XXX.',
  clauses: [
    {
      id: 'clause-01',
      number: 1,
      title: 'CLÁUSULA PRIMERA — OBJETO',
      content_markdown: 'El proveedor desarrollará el alcance acordado.',
    },
    {
      id: 'clause-02',
      number: 2,
      title: 'CLÁUSULA SEGUNDA — FORMA DE PAGO',
      content_markdown: 'Los pagos se realizarán según los hitos definidos.',
    },
  ],
};

function buildMockHandler({ proposalOverrides = {}, failTermsOnce = false } = {}) {
  let termsRequests = 0;
  return async ({ apiPath, method }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...proposal, ...proposalOverrides }),
      };
    }
    if (apiPath === `proposals/${MOCK_UUID}/contract-terms/`) {
      termsRequests += 1;
      if (failTermsOnce && termsRequests === 1) {
        return {
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'contract_template_unavailable' }),
        };
      }
      return { status: 200, contentType: 'application/json', body: JSON.stringify(contractTerms) };
    }
    if (apiPath === `proposals/${MOCK_UUID}/contract/draft-pdf/` && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/pdf',
        headers: { 'Content-Disposition': 'attachment; filename="Borrador_Contrato_E2E.pdf"' },
        body: '%PDF-1.4 contract draft',
      };
    }
    if (apiPath === `proposals/${MOCK_UUID}/record-view/` || apiPath.includes('/track/')) {
      return { status: 200, contentType: 'application/json', body: '{}' };
    }
    return null;
  };
}

test.describe('Proposal Contract and terms', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('gateway selection renders the current clause index', {
    tag: [...PROPOSAL_CONTRACT_TERMS, '@role:guest', '@outcome:display'],
  }, async ({ page }) => {
    test.setTimeout(60_000);
    await mockApi(page, buildMockHandler());
    // quality: allow-deep-link (the shared proposal URL is the guest's real entry point; this test then exercises the gateway selection)
    await page.goto(`/proposal/${MOCK_UUID}`, { waitUntil: 'domcontentloaded' });

    await page.getByTestId('gateway-legal-card').click({ timeout: 30_000 });
    await expect(page.getByRole('heading', { name: 'Índice de cláusulas' })).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText('CLÁUSULA SEGUNDA — FORMA DE PAGO')).toBeVisible();
  });

  test('clause index opens the selected contract clause', {
    tag: [...PROPOSAL_CONTRACT_TERMS, '@role:guest', '@outcome:success'],
  }, async ({ page }) => {
    test.setTimeout(60_000);
    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}?mode=legal`, { waitUntil: 'domcontentloaded' });

    await page.getByTestId('contract-clause-link-clause-02').click({ timeout: 30_000 });
    const paper = page.getByTestId('contract-paper');
    const selectedClause = paper.getByTestId('contract-clause-clause-02');
    await expect(paper).toBeVisible({ timeout: 20_000 });
    await expect(paper).toHaveAttribute('role', 'document');
    await expect(selectedClause).toBeVisible({ timeout: 20_000 });
    await expect(selectedClause).toContainText('Los pagos se realizarán según los hitos definidos.');
  });

  test('introductory description uses the clause index width', {
    tag: [...PROPOSAL_CONTRACT_TERMS, '@role:guest', '@outcome:display'],
  }, async ({ page }) => {
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1366, height: 900 });
    await mockApi(page, buildMockHandler());
    // quality: allow-deep-link (the shared proposal URL is the guest's real entry point; this test drives legal selection through the gateway)
    await page.goto(`/proposal/${MOCK_UUID}`, { waitUntil: 'domcontentloaded' });
    await page.getByTestId('gateway-legal-card').click({ timeout: 30_000 });

    const description = page.getByTestId('contract-terms-description');
    const clauseIndex = page.getByTestId('contract-terms-index');
    await expect(description).toBeVisible({ timeout: 30_000 });
    await expect(description).toContainText('Revisa de forma transparente el borrador');
    await expect(clauseIndex).toBeVisible();

    const descriptionBox = await description.boundingBox();
    const indexBox = await clauseIndex.boundingBox();
    expect(descriptionBox.width / indexBox.width).toBeGreaterThanOrEqual(0.98);
  });

  test('hidden mode cannot be forced through the legal query', {
    tag: [...PROPOSAL_CONTRACT_TERMS, '@role:guest', '@outcome:error'],
  }, async ({ page }) => {
    test.setTimeout(60_000);
    await mockApi(page, buildMockHandler({ proposalOverrides: { show_contract_terms: false } }));
    await page.goto(`/proposal/${MOCK_UUID}?mode=legal`, { waitUntil: 'domcontentloaded' });

    const gatewayHeading = page.getByRole('heading', { name: '¿Cómo prefieres explorar esta propuesta?' });
    await expect(gatewayHeading).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('gateway-legal-card')).toHaveCount(0);

    await page.getByRole('button', { name: /Vista Ejecutiva/ }).click();
    await expect(gatewayHeading).not.toBeVisible({ timeout: 10_000 });
  });

  test('English proposal cannot be forced into the legal mode', {
    tag: [...PROPOSAL_CONTRACT_TERMS, '@role:guest', '@outcome:error'],
  }, async ({ page }) => {
    test.setTimeout(60_000);
    await mockApi(page, buildMockHandler({ proposalOverrides: { language: 'en' } }));
    await page.goto(`/proposal/${MOCK_UUID}?mode=legal`, { waitUntil: 'domcontentloaded' });

    const gatewayHeading = page.getByRole('heading', { name: 'How would you like to explore this proposal?' });
    await expect(gatewayHeading).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('gateway-legal-card')).toHaveCount(0);

    await page.getByRole('button', { name: /Executive View/ }).click();
    await expect(gatewayHeading).not.toBeVisible({ timeout: 10_000 });
  });

  test('temporary contract failure exposes a working retry', {
    tag: [...PROPOSAL_CONTRACT_TERMS, '@role:guest', '@outcome:failure'],
  }, async ({ page }) => {
    test.setTimeout(60_000);
    await mockApi(page, buildMockHandler({ failTermsOnce: true }));
    await page.goto(`/proposal/${MOCK_UUID}?mode=legal`, { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('No pudimos cargar el borrador')).toBeVisible({ timeout: 30_000 });
    await page.getByTestId('contract-terms-retry').click();
    await expect(page.getByText('CLÁUSULA PRIMERA — OBJETO')).toBeVisible({ timeout: 20_000 });
  });

  test('floating download is the only draft PDF action', {
    tag: [...PROPOSAL_CONTRACT_DRAFT_DOWNLOAD, '@role:guest', '@outcome:success'],
  }, async ({ page }) => {
    test.setTimeout(60_000);
    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}?mode=legal`, { waitUntil: 'domcontentloaded' });
    const downloadButton = page.getByTitle('Descargar PDF');
    await expect(downloadButton).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('contract-draft-download')).toHaveCount(0);

    const downloadPromise = page.waitForEvent('download');
    await downloadButton.click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toBe('Borrador_Contrato_Contrato_E2E_21-08-26.pdf');
  });
});
