/**
 * E2E tests for the client picker inside the "Datos de la propuesta" form
 * of the proposal create view in JSON-import mode (/panel/proposals/create).
 *
 * Covers:
 *  - the ClientAutocomplete renders in JSON mode and the "Nombre" field
 *    pre-fills from the imported JSON's general.clientName
 *  - selecting an existing client links it: snapshot fields auto-fill, the
 *    "(#id)" hint shows, and the submit payload carries client_id (plus a
 *    sections.general.clientName synced to the linked client)
 *  - "Crear nuevo" keeps the typed name and submits without a client_id
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_JSON_IMPORT_CLIENT_PICKER } from '../helpers/flow-tags.js';

test.describe.configure({ timeout: 60_000 });

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const mockSearchResults = [
  {
    id: 401,
    name: 'Acme Corp',
    email: 'contacto@acme.co',
    phone: '+57 311 222 3344',
    company: 'Acme Inc.',
    is_email_placeholder: false,
    total_proposals: 3,
  },
  {
    id: 402,
    name: 'Acme Studio',
    email: 'hola@acmestudio.co',
    phone: '',
    company: '',
    is_email_placeholder: false,
    total_proposals: 0,
  },
];

const mockCreatedProposal = {
  id: 555,
  uuid: '55555555-1111-1111-1111-555555555555',
  title: 'Propuesta — Acme Corp',
  client_id: 401,
  client_name: 'Acme Corp',
  client_email: 'contacto@acme.co',
  status: 'draft',
  sections: [],
  requirement_groups: [],
  warnings: [],
};

const validJson = JSON.stringify({
  general: { clientName: 'Cliente Del JSON' },
  executiveSummary: { paragraphs: ['Resumen ejecutivo.'] },
});

function setupMock(page, { onCreateFromJson = null, searchResults = mockSearchResults } = {}) {
  return mockApi(page, async ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') return authCheck;

    if (apiPath.startsWith('proposals/client-profiles/search/')) {
      const url = new URL(route.request().url());
      const q = (url.searchParams.get('q') || '').toLowerCase();
      const results = q
        ? searchResults.filter(
            (c) =>
              c.name.toLowerCase().includes(q) ||
              c.email.toLowerCase().includes(q) ||
              (c.company || '').toLowerCase().includes(q),
          )
        : searchResults;
      return { status: 200, contentType: 'application/json', body: JSON.stringify(results) };
    }

    if (apiPath === 'proposals/create-from-json/' && method === 'POST') {
      if (onCreateFromJson) return onCreateFromJson(route);
      return { status: 201, contentType: 'application/json', body: JSON.stringify(mockCreatedProposal) };
    }

    if (apiPath === 'proposals/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }

    if (apiPath.startsWith('proposals/defaults/')) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ expiration_days: 21, language: 'es', sections_json: [] }),
      };
    }

    return null;
  });
}

async function gotoJsonModeWithParsedJson(page) {
  await page.goto('/panel/proposals/create');
  await expect(page.getByRole('heading', { name: 'Nueva Propuesta' })).toBeVisible({ timeout: 30_000 });

  // JSON import is the default tab, but click it to be explicit.
  await page.getByRole('button', { name: 'Importar JSON' }).click();

  const textarea = page.getByPlaceholder(/general/);
  await textarea.fill(validJson);
  await textarea.dispatchEvent('input');

  // The "Datos de la propuesta" metadata form only appears after a valid parse.
  await expect(page.getByRole('heading', { name: 'Datos de la propuesta' })).toBeVisible({ timeout: 10_000 });
}

test.describe('Admin Proposal JSON Import — Client Picker', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8600, role: 'admin', is_staff: true },
    });
  });

  test('client autocomplete is rendered and the name pre-fills from the imported JSON', {
    tag: [...ADMIN_PROPOSAL_JSON_IMPORT_CLIENT_PICKER, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await gotoJsonModeWithParsedJson(page);

    await expect(page.getByTestId('json-client-autocomplete')).toBeVisible();
    await expect(page.locator('#json-client-name')).toHaveValue('Cliente Del JSON');
  });

  test('selecting an existing client links it, shows the (#id) hint, and sends client_id on submit', {
    tag: [...ADMIN_PROPOSAL_JSON_IMPORT_CLIENT_PICKER, '@role:admin'],
  }, async ({ page }) => {
    let capturedPayload = null;
    await setupMock(page, {
      onCreateFromJson: (route) => {
        capturedPayload = route.request().postDataJSON();
        return { status: 201, contentType: 'application/json', body: JSON.stringify(mockCreatedProposal) };
      },
    });
    await gotoJsonModeWithParsedJson(page);

    await page.getByTestId('json-client-autocomplete').fill('acme');

    const firstOption = page.getByTestId('client-autocomplete-option-401');
    await expect(firstOption).toBeVisible({ timeout: 5_000 });
    await expect(firstOption).toContainText('(#401)');
    await firstOption.click();

    // Snapshot fields auto-fill from the selected client + linked hint shows the id.
    await expect(page.locator('#json-client-name')).toHaveValue('Acme Corp');
    await expect(page.locator('#json-client-email')).toHaveValue('contacto@acme.co');
    await expect(page.getByTestId('client-autocomplete-linked')).toContainText('(#401)');

    const [response] = await Promise.all([
      page.waitForResponse((r) => r.url().includes('proposals/create-from-json/')),
      page.getByRole('button', { name: /Crear desde JSON/i }).click(),
    ]);
    await response.finished();

    expect(capturedPayload).not.toBeNull();
    expect(capturedPayload.client_id).toBe(401);
    expect(capturedPayload.client_name).toBe('Acme Corp');
    // The greeting in the imported sections stays consistent with the linked client.
    expect(capturedPayload.sections.general.clientName).toBe('Acme Corp');

    await expect(page.getByText('Propuesta creada')).toBeVisible({ timeout: 5_000 });
  });

  test('"Crear nuevo" keeps the typed name and submits without a client_id', {
    tag: [...ADMIN_PROPOSAL_JSON_IMPORT_CLIENT_PICKER, '@role:admin'],
  }, async ({ page }) => {
    let capturedPayload = null;
    await setupMock(page, {
      searchResults: [],
      onCreateFromJson: (route) => {
        capturedPayload = route.request().postDataJSON();
        return {
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({ ...mockCreatedProposal, client_id: null, client_name: 'Cliente Nuevo Inline' }),
        };
      },
    });
    await gotoJsonModeWithParsedJson(page);

    await page.getByTestId('json-client-autocomplete').fill('Cliente Nuevo Inline');

    const createNew = page.getByTestId('client-autocomplete-create-new');
    await expect(createNew).toBeVisible({ timeout: 5_000 });
    await createNew.click();

    await expect(page.locator('#json-client-name')).toHaveValue('Cliente Nuevo Inline');
    await expect(page.getByTestId('client-autocomplete-linked')).toHaveCount(0);

    const [response] = await Promise.all([
      page.waitForResponse((r) => r.url().includes('proposals/create-from-json/')),
      page.getByRole('button', { name: /Crear desde JSON/i }).click(),
    ]);
    await response.finished();

    expect(capturedPayload).not.toBeNull();
    expect(capturedPayload.client_id).toBeUndefined();
    expect(capturedPayload.client_name).toBe('Cliente Nuevo Inline');
  });
});
