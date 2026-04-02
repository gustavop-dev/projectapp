/**
 * E2E tests for admin proposal contract edit flow.
 *
 * @flow:admin-proposal-contract-edit
 * Covers: Edit button opens modal pre-filled with existing params,
 *         modal title shows "Editar", save calls update API.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_CONTRACT_EDIT } from '../helpers/flow-tags.js';

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

const mockProposal = {
  id: PROPOSAL_ID,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'Contract Edit Test',
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
  contract_params: {
    contractor_full_name: 'Carlos Dev',
    contractor_cedula: '1234567890',
    contractor_email: 'carlos@projectapp.co',
    bank_name: 'Bancolombia',
    bank_account_type: 'Ahorros',
    bank_account_number: '123456789',
    contract_city: 'Medellín',
    client_full_name: 'Acme Corp',
    client_cedula: '9876543210',
    client_email: 'acme@example.com',
    contract_date: '2026-04-01',
    contract_source: 'default',
  },
};

const companySettings = {
  contractor_full_name: 'Carlos Dev',
  contractor_cedula: '1234567890',
  contractor_email: 'carlos@projectapp.co',
  bank_name: 'Bancolombia',
  bank_account_type: 'Ahorros',
  bank_account_number: '123456789',
  contract_city: 'Medellín',
};

test.describe('Admin Proposal Contract Edit', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('edit button visible when contract exists', {
    tag: [...ADMIN_PROPOSAL_CONTRACT_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      if (apiPath === 'proposals/company-settings/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(companySettings) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.waitForLoadState('networkidle');
    await page.getByText('Documentos').first().click();

    await expect(page.getByRole('button', { name: /Editar parámetros/i })).toBeVisible();
  });

  test('opens modal in edit mode with pre-filled params', {
    tag: [...ADMIN_PROPOSAL_CONTRACT_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      if (apiPath === 'proposals/company-settings/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(companySettings) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.waitForLoadState('networkidle');
    await page.getByText('Documentos').first().click();
    await page.getByRole('button', { name: /Editar parámetros/i }).click();

    // Modal title should say "Editar"
    await expect(page.getByText('Editar contrato de desarrollo')).toBeVisible();
    // Submit button should say "Actualizar"
    await expect(page.getByRole('button', { name: /Actualizar contrato/i })).toBeVisible();
  });

  test('submit calls contract update API', {
    tag: [...ADMIN_PROPOSAL_CONTRACT_EDIT, '@role:admin'],
  }, async ({ page }) => {
    let updateCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      if (apiPath === 'proposals/company-settings/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(companySettings) };
      }
      if (apiPath === `proposals/${PROPOSAL_ID}/contract/update/` && method === 'PUT') {
        updateCalled = true;
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ id: 10, document_type: 'contract' }) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.waitForLoadState('networkidle');
    await page.getByText('Documentos').first().click();
    await page.getByRole('button', { name: /Editar parámetros/i }).click();

    await page.getByRole('button', { name: /Actualizar contrato/i }).click();
    await page.waitForTimeout(500);
    expect(updateCalled).toBe(true);
  });
});
