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
    meta: { total: 1, active: 1, archived: 0, clients_without_projects: 3 },
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

  it('archive and unarchive hit their dedicated endpoints', async () => {
    patch_request.mockResolvedValue({ data: { id: 1, status: 'archived' } });
    get_request.mockResolvedValue(LIST_RESPONSE);
    const store = usePanelProjectsStore();

    await store.archiveProject(1);
    await store.unarchiveProject(1);

    expect(patch_request).toHaveBeenNthCalledWith(1, 'projects/1/archive/', {});
    expect(patch_request).toHaveBeenNthCalledWith(2, 'projects/1/unarchive/', {});
    expect(get_request).toHaveBeenCalledTimes(2);
  });

  it('a failed archive keeps the error message for the toast', async () => {
    patch_request.mockRejectedValueOnce(
      apiError(400, { error: 'El proyecto ya está archivado.', code: 'already_archived' }),
    );
    const store = usePanelProjectsStore();

    const result = await store.archiveProject(1);

    expect(result.success).toBe(false);
    expect(result.message).toBe('El proyecto ya está archivado.');
    expect(result.code).toBe('already_archived');
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
