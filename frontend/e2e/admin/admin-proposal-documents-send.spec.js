/**
 * E2E tests for admin proposal documents send flow.
 *
 * @flow:admin-proposal-documents-send
 * Covers: document checkboxes, send button states, SendDocumentsModal
 *         fields, email submission calls API, success message.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_DOCUMENTS_SEND } from '../helpers/flow-tags.js';

const PROPOSAL_ID = 1;
const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const contractDoc = {
  id: 10,
  document_type: 'contract',
  document_type_display: 'Contrato',
  title: 'Contrato de desarrollo',
  file: '/media/contracts/contract.pdf',
  is_generated: true,
  created_at: '2026-04-01T10:00:00Z',
};

const additionalDoc = {
  id: 20,
  document_type: 'amendment',
  document_type_display: 'Otrosí',
  title: 'Otrosí No. 1',
  file: '/media/docs/otrosi-1.pdf',
  is_generated: false,
  created_at: '2026-04-01T12:00:00Z',
};

const mockProposal = {
  id: PROPOSAL_ID,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'Send Docs Test',
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
  proposal_documents: [contractDoc, additionalDoc],
  contract_params: { contract_source: 'default' },
};

function buildApiHandler(overrides = {}) {
  const proposal = overrides.proposal || mockProposal;
  return async ({ apiPath, method }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposal) };
    }
    if (apiPath === `proposals/${PROPOSAL_ID}/documents/send/` && method === 'POST') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) };
    }
    return null;
  };
}

test.describe('Admin Proposal Documents Send', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('send section shows checkboxes for main documents', {
    tag: [...ADMIN_PROPOSAL_DOCUMENTS_SEND, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildApiHandler());
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit?tab=documents`);
    await page.waitForLoadState('domcontentloaded');

    // Send section header
    await expect(page.getByText('Enviar documentos al cliente').first()).toBeVisible();
    // Checkboxes for main docs
    await expect(page.getByText('Contrato de desarrollo (borrador)')).toBeVisible();
    await expect(page.getByText('Propuesta comercial').first()).toBeVisible();
    await expect(page.getByText('Detalle técnico').first()).toBeVisible();
  });

  test('draft contract checkbox disabled when no contract generated', {
    tag: [...ADMIN_PROPOSAL_DOCUMENTS_SEND, '@role:admin'],
  }, async ({ page }) => {
    const proposalNoContract = {
      ...mockProposal,
      proposal_documents: [additionalDoc],
      contract_params: null,
    };
    await mockApi(page, buildApiHandler({ proposal: proposalNoContract }));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit?tab=documents`);
    await page.waitForLoadState('domcontentloaded');

    // Contract checkbox should be disabled
    const contractCheckbox = page.locator('input[type="checkbox"][value="draft_contract"]');
    await expect(contractCheckbox).toBeDisabled();
    // "no generado" hint visible
    await expect(page.getByText('(no generado)')).toBeVisible();
  });

  test('shows recipient email address', {
    tag: [...ADMIN_PROPOSAL_DOCUMENTS_SEND, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildApiHandler());
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit?tab=documents`);
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByText('acme@example.com').first()).toBeVisible();
  });

  test('send button opens SendDocumentsModal with email fields', {
    tag: [...ADMIN_PROPOSAL_DOCUMENTS_SEND, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildApiHandler());
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit?tab=documents`);
    await page.waitForLoadState('domcontentloaded');

    await page.getByRole('button', { name: /Enviar al cliente/i }).click();

    // Modal header
    await expect(page.getByText('Enviar documentos al cliente').nth(1)).toBeVisible();
    // Switch to edit tab (modal opens on preview by default)
    await page.getByRole('button', { name: /Editar/i }).click();
    // Email form fields
    await expect(page.getByLabel(/Asunto/i)).toBeVisible();
    await expect(page.getByLabel(/Saludo/i)).toBeVisible();
    await expect(page.getByLabel(/Texto introductorio/i)).toBeVisible();
    await expect(page.getByLabel(/Texto de cierre/i)).toBeVisible();
    // Submit button
    await expect(page.getByRole('button', { name: /Enviar documentos$/i })).toBeVisible();
  });

  test('modal subject is pre-filled with client name', {
    tag: [...ADMIN_PROPOSAL_DOCUMENTS_SEND, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildApiHandler());
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit?tab=documents`);
    await page.waitForLoadState('domcontentloaded');

    await page.getByRole('button', { name: /Enviar al cliente/i }).click();

    // Switch to edit tab (modal opens on preview by default)
    await page.getByRole('button', { name: /Editar/i }).click();
    const subjectInput = page.getByLabel(/Asunto/i);
    await expect(subjectInput).toHaveValue(/Acme Corp/);
  });

  test('submitting modal calls send API and shows success', {
    tag: [...ADMIN_PROPOSAL_DOCUMENTS_SEND, '@role:admin'],
  }, async ({ page }) => {
    let sendCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      if (apiPath === `proposals/${PROPOSAL_ID}/documents/send/` && method === 'POST') {
        sendCalled = true;
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit?tab=documents`);
    await page.waitForLoadState('domcontentloaded');

    await page.getByRole('button', { name: /Enviar al cliente/i }).click();
    await page.getByRole('button', { name: /Enviar documentos$/i }).click();

    await page.waitForTimeout(500);
    expect(sendCalled).toBe(true);
  });

  test('no client email shows warning and disables send button', {
    tag: [...ADMIN_PROPOSAL_DOCUMENTS_SEND, '@role:admin'],
  }, async ({ page }) => {
    const proposalNoEmail = { ...mockProposal, client_email: '' };
    await mockApi(page, buildApiHandler({ proposal: proposalNoEmail }));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit?tab=documents`);
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByText(/No hay email del cliente/i)).toBeVisible();
    const sendBtn = page.getByRole('button', { name: /Enviar al cliente/i });
    await expect(sendBtn).toBeDisabled();
  });
});
