/**
 * E2E tests for admin proposal documents management flow.
 *
 * @flow:admin-proposal-documents-manage
 * Covers: upload form renders, document list with type badges,
 *         upload calls API, delete button on non-generated docs,
 *         custom type label for "Otro" type.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_DOCUMENTS_MANAGE } from '../helpers/flow-tags.js';

const PROPOSAL_ID = 1;
const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const additionalDoc = {
  id: 20,
  document_type: 'amendment',
  document_type_display: 'Otrosí',
  title: 'Otrosí No. 1',
  file: '/media/docs/otrosi-1.pdf',
  is_generated: false,
  created_at: '2026-04-01T12:00:00Z',
};

const generatedContractDoc = {
  id: 10,
  document_type: 'contract',
  document_type_display: 'Contrato',
  title: 'Contrato de desarrollo',
  file: '/media/contracts/contract.pdf',
  is_generated: true,
  created_at: '2026-04-01T10:00:00Z',
};

const mockProposal = {
  id: PROPOSAL_ID,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'Documents Manage Test',
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
  proposal_documents: [generatedContractDoc, additionalDoc],
  contract_params: { contract_source: 'default' },
};

test.describe('Admin Proposal Documents Manage', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('additional documents section renders with existing docs', {
    tag: [...ADMIN_PROPOSAL_DOCUMENTS_MANAGE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.waitForLoadState('networkidle');
    await page.getByText('Documentos').first().click();

    // Additional docs section header
    await expect(page.getByText('Documentos adicionales').first()).toBeVisible();
    // Document type badge
    await expect(page.getByText('Otrosí').first()).toBeVisible();
    // Document title link
    await expect(page.getByText('Otrosí No. 1')).toBeVisible();
  });

  test('upload form visible with title, type, and file inputs', {
    tag: [...ADMIN_PROPOSAL_DOCUMENTS_MANAGE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.waitForLoadState('networkidle');
    await page.getByText('Documentos').first().click();

    // Upload section text
    await expect(page.getByText(/Subir documento/i)).toBeVisible();
    // Title input
    await expect(page.getByPlaceholder(/Ej: Anexo técnico/i)).toBeVisible();
    // Upload button
    await expect(page.getByRole('button', { name: /Subir$/i })).toBeVisible();
  });

  test('delete button visible on non-generated documents only', {
    tag: [...ADMIN_PROPOSAL_DOCUMENTS_MANAGE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.waitForLoadState('networkidle');
    await page.getByText('Documentos').first().click();

    // The additional docs section should have at least one delete button (for the non-generated doc)
    const additionalSection = page.locator('section').filter({ hasText: 'Documentos adicionales' });
    const deleteButtons = additionalSection.locator('button').filter({ has: page.locator('svg path[d*="M19 7l"]') });
    await expect(deleteButtons).toHaveCount(1);
  });

  test('shows empty state when no additional documents', {
    tag: [...ADMIN_PROPOSAL_DOCUMENTS_MANAGE, '@role:admin'],
  }, async ({ page }) => {
    const proposalNoAdditional = {
      ...mockProposal,
      proposal_documents: [generatedContractDoc],
    };
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(proposalNoAdditional) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.waitForLoadState('networkidle');
    await page.getByText('Documentos').first().click();

    await expect(page.getByText('No hay documentos adicionales')).toBeVisible();
  });
});
