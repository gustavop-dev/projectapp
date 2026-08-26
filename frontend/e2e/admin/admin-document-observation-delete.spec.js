/**
 * E2E coverage for recoverable observation deletion.
 *
 * @flow:admin-document-observation-delete
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_OBSERVATION_DELETE } from '../helpers/flow-tags.js';

const json = (body, status = 200) => ({
  status,
  contentType: 'application/json',
  body: JSON.stringify(body),
});

const authCheck = json({ user: { username: 'admin', is_staff: true } });
const stateGroups = [
  { id: 2, name: 'Señales', selection_mode: 'additive', order: 1, is_active: true },
];
const needsFixState = {
  id: 20,
  name: 'Solucionar bug',
  slug: 'solucionar-bug',
  color: 'red',
  system_key: 'needs_fix',
  order: 0,
  group: 2,
  group_id: 2,
  group_name: 'Señales',
  group_mode: 'additive',
  group_order: 1,
  is_active: true,
  merged_into: null,
  incompatibility_ids: [],
};

function note(id, content, overrides = {}) {
  return {
    id,
    document: 1,
    episode: 101,
    title: `Observación ${id}`,
    content,
    status: 'open',
    resolution_note: '',
    order: id,
    deleted_at: null,
    deleted_by: null,
    deleted_by_name: '',
    ...overrides,
  };
}

function episode(notes) {
  return {
    id: 101,
    document: 1,
    state: needsFixState,
    opened_at: '2026-08-20T15:00:00Z',
    closed_at: null,
    opening_time_known: true,
    duration_seconds: 259200,
    opened_by: 8700,
    opened_by_name: 'Admin QA',
    closed_by: null,
    closed_by_name: null,
    outcome: '',
    close_note: '',
    origin: 'note',
    events: [],
    notes,
  };
}

function makeDocument(notes = []) {
  return {
    id: 1,
    title: 'Contrato de soporte',
    status: 'draft',
    content_markdown: '# Contrato\n\nContenido.',
    client_name: 'ACME',
    client_display_name: 'ACME',
    client: null,
    project: null,
    language: 'es',
    include_portada: true,
    include_subportada: true,
    include_contraportada: true,
    is_client_visible: false,
    is_archived: false,
    folder: null,
    template_style: 'professional',
    document_type_code: 'markdown',
    active_states: notes.some((item) => item.status === 'open') ? [episode(notes)] : [],
    notes,
    client_custom_notes: [],
    created_at: '2026-08-20T15:00:00Z',
  };
}

function listDocument(document) {
  return {
    id: document.id,
    title: document.title,
    status: document.status,
    is_archived: document.is_archived,
    document_type_code: document.document_type_code,
    client_display_name: document.client_display_name,
    project_name: '',
    active_states: document.active_states,
    created_at: document.created_at,
  };
}

function baseRoutes(apiPath, document) {
  if (apiPath === 'auth/check/') return authCheck;
  if (apiPath === 'documents/') return json([listDocument(document)]);
  if (apiPath === 'documents/counts/') {
    return json({
      documents: { active: 1, archived: 0, unfiled_active: 1, unfiled_archived: 0 },
      folders: { active: 0, archived: 0 },
    });
  }
  if (apiPath === 'document-folders/') return json([]);
  if (apiPath === 'document-states/') return json([needsFixState]);
  if (apiPath === 'document-state-groups/') return json(stateGroups);
  if (apiPath === 'documents/1/detail/') return json(document);
  if (apiPath === 'documents/1/state-history/') return json([]);
  return null;
}

async function openObservations(page) {
  // quality: allow-deep-link (the authenticated document list is this flow's entry point)
  await page.goto('/en-us/panel/documents', { waitUntil: 'domcontentloaded' });
  await page.getByTestId('document-open-1').click();
  await expect(page.getByTestId('document-state-selector')).toBeVisible({ timeout: 30_000 });
  await page.getByTestId('doc-client-note-open').click();
  await expect(page.getByTestId('document-client-note-modal')).toBeVisible();
}

test.describe('Admin Document Observation Delete', () => {
  // The first edit-route visit cold-compiles a large Nuxt page. Serializing this
  // one flow avoids three workers competing for that compilation and retrying.
  test.describe.configure({ mode: 'serial' });
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 8700, role: 'admin', is_staff: true },
    });
  });

  test('keeps the observation after cancellation', {
    tag: [...ADMIN_DOCUMENT_OBSERVATION_DELETE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (/panel/documents is the module entry; this test
    // then follows list → editor → observations through visible controls)
    const document = makeDocument([note(51, 'Este texto salió en un correo de prueba.')]);
    let deleteCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'documents/1/notes/51/' && method === 'DELETE') {
        deleteCalled = true;
        return json({ deleted_note_ids: [51], closed_episode_ids: [101] });
      }
      return baseRoutes(apiPath, document);
    });
    await openObservations(page);

    await page.getByTestId('document-observation-delete-51').click();
    const confirmation = page.getByTestId('document-observation-delete-confirmation');
    await expect(confirmation).toContainText('Este texto salió en un correo de prueba.');
    await expect(confirmation).toContainText('podrás recuperarlas desde la papelera');
    await expect(confirmation).toContainText('no lo borra de la bandeja');
    await confirmation.getByRole('button', { name: 'Cancelar', exact: true }).click();

    await expect(page.getByTestId('document-observation-51')).toBeVisible();
    expect(deleteCalled).toBe(false);
  });

  test('removes the note-origin pending state after deleting its last observation', {
    tag: [...ADMIN_DOCUMENT_OBSERVATION_DELETE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const document = makeDocument([note(51, 'Duplicado que nunca debió existir.')]);
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'documents/1/notes/51/' && method === 'DELETE') {
        document.notes = [];
        document.active_states = [];
        return json({ deleted_note_ids: [51], closed_episode_ids: [101], state_closed: true });
      }
      return baseRoutes(apiPath, document);
    });
    await openObservations(page);

    await page.getByTestId('document-observation-delete-51').click();
    await page.getByTestId('document-observation-confirm-delete').click();
    await expect(page.getByText('Aún no hay observaciones.')).toBeVisible();
    await page.getByTestId('client-note-cancel').click();

    await expect(page.getByTestId('document-state-selector')).toContainText('Sin estados activos');
  });

  test('submits one atomic request for a bulk deletion', {
    tag: [...ADMIN_DOCUMENT_OBSERVATION_DELETE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const document = makeDocument([
      note(51, 'Prueba uno.'),
      note(52, 'Prueba dos.', { status: 'resolved', resolution_note: 'Atendida por error.' }),
    ]);
    const requests = [];
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'documents/1/notes/bulk-delete/' && method === 'POST') {
        requests.push(route.request().postDataJSON());
        document.notes = [];
        document.active_states = [];
        return json({ deleted_note_ids: [51, 52], closed_episode_ids: [101], state_closed: true });
      }
      return baseRoutes(apiPath, document);
    });
    await openObservations(page);

    await page.getByTestId('document-observation-select-all').click();
    await page.getByTestId('document-observation-bulk-delete').click();
    await expect(page.getByTestId('document-observation-delete-confirmation')).toContainText('Eliminar 2 observaciones');
    await page.getByTestId('document-observation-confirm-delete').click();

    expect(requests).toEqual([{ note_ids: [51, 52] }]);
    await expect(page.getByText('Aún no hay observaciones.')).toBeVisible();
  });

  test('restores a deleted observation from the trash', {
    tag: [...ADMIN_DOCUMENT_OBSERVATION_DELETE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const restored = note(51, 'Recuperar esta observación.');
    const deleted = {
      ...restored,
      deleted_at: '2026-08-26T14:00:00Z',
      deleted_by: 8700,
      deleted_by_name: 'Admin QA',
    };
    const document = makeDocument([]);
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'documents/1/notes/' && method === 'GET') {
        const scope = new URL(route.request().url()).searchParams.get('scope');
        if (scope === 'deleted') return json([deleted]);
      }
      if (apiPath === 'documents/1/notes/51/restore/' && method === 'POST') {
        document.notes = [restored];
        document.active_states = [episode([restored])];
        return json({ note: restored, restored_episode_id: 102, state_reopened: true });
      }
      return baseRoutes(apiPath, document);
    });
    await openObservations(page);

    await page.getByTestId('document-observation-tab-trash').click();
    await expect(page.getByTestId('document-observation-trash')).toContainText('Recuperar esta observación.');
    await page.getByTestId('document-observation-restore-51').click();
    await page.getByTestId('document-observation-tab-active').click();

    await expect(page.getByTestId('document-observation-51')).toContainText('Recuperar esta observación.');
  });

  test('keeps the confirmation open after a deletion failure', {
    tag: [...ADMIN_DOCUMENT_OBSERVATION_DELETE, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    const document = makeDocument([note(51, 'No perder este texto.')]);
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'documents/1/notes/51/' && method === 'DELETE') {
        return json({ detail: 'Servicio temporalmente no disponible.' }, 503);
      }
      return baseRoutes(apiPath, document);
    });
    await openObservations(page);

    await page.getByTestId('document-observation-delete-51').click();
    await page.getByTestId('document-observation-confirm-delete').click();

    const confirmation = page.getByTestId('document-observation-delete-confirmation');
    await expect(confirmation).toBeVisible();
    await expect(confirmation).toContainText('Servicio temporalmente no disponible.');
  });

  test('shows generic deletion activity without note content', {
    tag: [...ADMIN_DOCUMENT_OBSERVATION_DELETE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (/panel/documents is the module entry; this test
    // then follows list → editor → observations through visible controls)
    const sensitiveContent = 'Texto equivocado que no debe vivir en la auditoría.';
    const document = makeDocument([note(51, sensitiveContent)]);
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'documents/1/notes/events/' && method === 'GET') {
        return json([{
          id: 901,
          note: 51,
          event_type: 'deleted',
          actor: 8700,
          actor_name: 'Admin QA',
          recorded_at: '2026-08-26T14:00:00Z',
          details: { closed_episode_id: 101 },
        }]);
      }
      return baseRoutes(apiPath, document);
    });
    await openObservations(page);

    await page.getByTestId('document-observation-tab-activity').click();
    const activity = page.getByTestId('document-observation-activity');

    await expect(activity).toContainText('Admin QA eliminó una observación.');
    await expect(activity).not.toContainText(sensitiveContent);
  });
});
