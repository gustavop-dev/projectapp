/**
 * Panel projects store: the session-side face of accounts.Project.
 *
 * Covers the scope=all single load, the refetch-after-mutation contract the
 * module page relies on (counts and meta must not go stale), and the
 * normalized error shapes useAccountingCrudPage renders.
 */
jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
}));

import { setActivePinia, createPinia } from 'pinia';
import { usePanelProjectsStore } from '../../stores/panel_projects';
import { useAccountingStore } from '../../stores/accounting';
import { useDocumentStore } from '../../stores/documents';
import {
  get_request,
  create_request,
  patch_request,
} from '../../stores/services/request_http';

const LIST_RESPONSE = {
  data: {
    results: [
      {
        id: 1,
        name: 'Vastago',
        status: 'active',
        status_label: 'Activo',
        client: { profile_id: 7, name: 'Deivis Ríos', company: '' },
        hostings_count: 1,
        incomes_count: 2,
      },
    ],
    meta: {
      total: 1,
      by_state: [{ state_id: 2, name: 'Activo', count: 1 }],
      review_required: 0,
      clients_without_projects: 3,
      records_without_project: 0,
    },
  },
};

const apiError = (status, data) => ({ response: { status, data } });

describe('panel_projects store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    jest.clearAllMocks();
  });

  it('fetchProjects loads every scope at once and keeps the meta', async () => {
    get_request.mockResolvedValueOnce(LIST_RESPONSE);
    const store = usePanelProjectsStore();

    const result = await store.fetchProjects();

    expect(get_request).toHaveBeenCalledWith('projects/?scope=all');
    expect(result.success).toBe(true);
    expect(store.records).toHaveLength(1);
    expect(store.meta.clients_without_projects).toBe(3);
    expect(store.meta.by_state).toEqual([
      { state_id: 2, name: 'Activo', count: 1 },
    ]);
    expect(store.error).toBeNull();
  });

  it('a failed load flags fetch_failed for the error state', async () => {
    get_request.mockRejectedValueOnce(apiError(500, 'boom'));
    const store = usePanelProjectsStore();

    const result = await store.fetchProjects();

    expect(result.success).toBe(false);
    expect(store.error).toBe('fetch_failed');
    expect(store.records).toEqual([]);
  });

  it('createRecord posts the payload and refetches the listing', async () => {
    create_request.mockResolvedValueOnce({ data: { id: 9, name: 'Nuevo' } });
    get_request.mockResolvedValueOnce(LIST_RESPONSE);
    const store = usePanelProjectsStore();

    const result = await store.createRecord('projects', {
      name: 'Nuevo',
      client_profile_id: 7,
    });

    expect(create_request).toHaveBeenCalledWith('projects/create/', {
      name: 'Nuevo',
      client_profile_id: 7,
    });
    expect(get_request).toHaveBeenCalledWith('projects/?scope=all');
    expect(result).toMatchObject({ success: true, data: { id: 9 } });
  });

  it('a rejected create surfaces the serializer message', async () => {
    create_request.mockRejectedValueOnce(
      apiError(400, { client_profile_id: ['Ese cliente no existe o no es un perfil de cliente.'] }),
    );
    const store = usePanelProjectsStore();

    const result = await store.createRecord('projects', { name: 'X', client_profile_id: 99 });

    expect(result.success).toBe(false);
    expect(result.message).toBe('Ese cliente no existe o no es un perfil de cliente.');
    expect(get_request).not.toHaveBeenCalled();
  });

  it('updateRecord patches the update endpoint and refetches', async () => {
    patch_request.mockResolvedValueOnce({ data: { id: 1, name: 'Renombrado' } });
    get_request.mockResolvedValueOnce(LIST_RESPONSE);
    const store = usePanelProjectsStore();

    const result = await store.updateRecord('projects', 1, { name: 'Renombrado' });

    expect(patch_request).toHaveBeenCalledWith('projects/1/update/', { name: 'Renombrado' });
    expect(get_request).toHaveBeenCalledWith('projects/?scope=all');
    expect(result.success).toBe(true);
  });

  it('refreshAfterExternalMutation reloads lifecycle counts', async () => {
    get_request.mockResolvedValueOnce(LIST_RESPONSE);
    const store = usePanelProjectsStore();

    const result = await store.refreshAfterExternalMutation();

    expect(result.success).toBe(true);
    expect(get_request).toHaveBeenCalledWith('projects/?scope=all');
    expect(store.meta.by_state[0].count).toBe(1);
  });

  it('fetchUnlinkedRecords returns the preview without touching the listing', async () => {
    const preview = {
      client: { profile_id: 7, name: 'Deivis Ríos' },
      hostings: [{ id: 4, label: 'Deivis — Vastago' }],
      incomes: [],
      total: 1,
    };
    get_request.mockResolvedValueOnce({ data: preview });
    const store = usePanelProjectsStore();

    const result = await store.fetchUnlinkedRecords(1);

    expect(get_request).toHaveBeenCalledWith('projects/1/unlinked-records/');
    expect(result).toEqual({ success: true, data: preview });
    expect(store.records).toEqual([]);
  });

  it('assignUnlinkedRecords posts the confirmed ids and refetches', async () => {
    create_request.mockResolvedValueOnce({
      data: { assigned_hostings: 1, assigned_incomes: 2, project: { id: 1 } },
    });
    get_request.mockResolvedValueOnce(LIST_RESPONSE);
    const store = usePanelProjectsStore();

    const result = await store.assignUnlinkedRecords(1, {
      hosting_ids: [4],
      income_ids: [8, 9],
    });

    expect(create_request).toHaveBeenCalledWith('projects/1/assign-unlinked/', {
      hosting_ids: [4],
      income_ids: [8, 9],
    });
    expect(get_request).toHaveBeenCalledWith('projects/?scope=all');
    expect(result.success).toBe(true);
    expect(result.data.assigned_incomes).toBe(2);
  });

  it('assignUnlinkedRecords rebuilds the open accounting tables from the response rows', async () => {
    const store = usePanelProjectsStore();
    const accounting = useAccountingStore();
    accounting.hostings = [
      { id: 4, project: null, project_name: null },
      { id: 5, project: null, project_name: null },
    ];
    accounting.incomes = [{ id: 8, project: null, project_name: null }];
    create_request.mockResolvedValueOnce({
      data: {
        assigned_hostings: 1,
        assigned_incomes: 1,
        hostings: [{ id: 4, project: 1, project_name: 'Vastago' }],
        incomes: [{ id: 8, project: 1, project_name: 'Vastago' }],
        project: { id: 1 },
      },
    });
    get_request.mockResolvedValueOnce(LIST_RESPONSE);

    await store.assignUnlinkedRecords(1, { hosting_ids: [4], income_ids: [8] });

    // The touched rows are replaced in place; untouched ones survive as-is.
    expect(accounting.hostings.map((row) => row.project)).toEqual([1, null]);
    expect(accounting.incomes[0].project_name).toBe('Vastago');
  });

  it('assignUnlinkedRecords rebuilds the open documents list from the response rows', async () => {
    const store = usePanelProjectsStore();
    const documentStore = useDocumentStore();
    documentStore.documents = [
      { id: 12, project: null, project_name: null },
      { id: 20, project: null, project_name: null },
    ];
    create_request.mockResolvedValueOnce({
      data: {
        assigned_documents: 1,
        documents: [{ id: 12, project: 1, project_name: 'Vastago' }],
        project: { id: 1 },
      },
    });
    get_request.mockResolvedValueOnce(LIST_RESPONSE);

    await store.assignUnlinkedRecords(1, { document_ids: [12] });

    expect(documentStore.documents.map((row) => row.project)).toEqual([1, null]);
  });

  it('a 409 on assign keeps the code so the modal can reload its preview', async () => {
    create_request.mockRejectedValueOnce(apiError(409, {
      error: '1 registro de la lista ya no se puede asignar (ganaron proyecto o cambiaron de cliente).',
      code: 'records_changed',
      changed_ids: [8],
    }));
    const store = usePanelProjectsStore();

    const result = await store.assignUnlinkedRecords(1, { income_ids: [8] });

    expect(result.success).toBe(false);
    expect(result.code).toBe('records_changed');
    expect(get_request).not.toHaveBeenCalled();
  });

  it('previewChangeClient asks with the destination profile and returns the impact', async () => {
    get_request.mockResolvedValueOnce({ data: { totals: { move: 2 } } });
    const store = usePanelProjectsStore();

    const result = await store.previewChangeClient(1, 9);

    expect(get_request).toHaveBeenCalledWith(
      'projects/1/change-client/preview/?client_profile_id=9',
    );
    expect(result).toEqual({ success: true, data: { totals: { move: 2 } } });
  });

  it('changeClient refetches only the accounting lists that are loaded', async () => {
    const store = usePanelProjectsStore();
    const accounting = useAccountingStore();
    accounting.hostings = [{ id: 4 }];
    accounting.incomes = [];
    // The cascade response carries counts, never rows, so the reconciliation
    // is a refetch — pin that it only fires for lists actually in memory.
    accounting.fetchRecords = jest.fn();
    create_request.mockResolvedValueOnce({
      data: {
        project: { id: 1 },
        moved: { hostings: 1, incomes: 0, draft_accounts: 0 },
        detached: { hostings: 0, incomes: 0, draft_accounts: 0 },
        skipped: { issued_accounts: 0, clientless: 0, other_documents: 0 },
      },
    });
    get_request.mockResolvedValueOnce(LIST_RESPONSE);

    const result = await store.changeClient(1, {
      client_profile_id: 9, mode: 'move', hosting_ids: [4], income_ids: [],
    });

    expect(create_request).toHaveBeenCalledWith('projects/1/change-client/', {
      client_profile_id: 9, mode: 'move', hosting_ids: [4], income_ids: [],
    });
    expect(accounting.fetchRecords).toHaveBeenCalledWith('hostings');
    expect(accounting.fetchRecords).not.toHaveBeenCalledWith('incomes');
    expect(result.success).toBe(true);
  });

  it('fetchClientsWithoutProjects loads the uncovered-clients panel', async () => {
    get_request.mockResolvedValueOnce({ data: [{ id: 7, name: 'Wilson García' }] });
    const store = usePanelProjectsStore();

    const result = await store.fetchClientsWithoutProjects();

    expect(get_request).toHaveBeenCalledWith(
      'proposals/client-profiles/?without_projects=true&limit=500',
    );
    expect(result.success).toBe(true);
    expect(store.clientsWithoutProjects).toEqual([{ id: 7, name: 'Wilson García' }]);
  });
});
