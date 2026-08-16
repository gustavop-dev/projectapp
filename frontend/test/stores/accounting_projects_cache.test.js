/**
 * The projects picker cache: memoized forever by design, so the two new
 * actions are the only doors — createProjectForClient must update the
 * per-client list in place (and drop 'all'), and invalidateProjectsCache
 * must force the next fetch back to the network.
 */
jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

import { setActivePinia, createPinia } from 'pinia';
import { useAccountingStore } from '../../stores/accounting';
import { get_request, create_request } from '../../stores/services/request_http';

describe('accounting store — projects picker cache', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    jest.clearAllMocks();
  });

  it('createProjectForClient appends sorted to the client cache and drops all', async () => {
    const store = useAccountingStore();
    store.projectsByClient = {
      7: [{ id: 11, name: 'Kore', status: 'active', status_label: 'Activo' }],
      all: [{ id: 11, name: 'Kore', status: 'active', status_label: 'Activo' }],
    };
    create_request.mockResolvedValueOnce({
      data: { id: 31, name: 'Crushme', status: 'active', status_label: 'Activo' },
    });

    const result = await store.createProjectForClient(7, { name: 'Crushme' });

    expect(create_request).toHaveBeenCalledWith('projects/create/', {
      name: 'Crushme',
      client_profile_id: 7,
    });
    expect(result.success).toBe(true);
    expect(store.projectsByClient[7].map((p) => p.name)).toEqual(['Crushme', 'Kore']);
    expect(store.projectsByClient.all).toBeUndefined();
  });

  it('createProjectForClient returns the full annotated row, cache stays lean', async () => {
    const store = useAccountingStore();
    store.projectsByClient = { 7: [] };
    create_request.mockResolvedValueOnce({
      data: {
        id: 31,
        name: 'Vastago',
        status: 'active',
        status_label: 'Activo',
        unlinked_hostings_count: 2,
        unlinked_incomes_count: 3,
      },
    });

    const result = await store.createProjectForClient(7, { name: 'Vastago' });

    // The caller decides the assign offer from these counters...
    expect(result.data.unlinked_hostings_count).toBe(2);
    expect(result.data.unlinked_incomes_count).toBe(3);
    // ...while the picker cache lists only what the dropdown shows.
    expect(store.projectsByClient[7]).toEqual([
      { id: 31, name: 'Vastago', status: 'active', status_label: 'Activo' },
    ]);
  });

  it('a rejected create leaves the cache untouched and keeps the message', async () => {
    const store = useAccountingStore();
    store.projectsByClient = { 7: [] };
    create_request.mockRejectedValueOnce({
      response: { status: 400, data: { name: ['Requerido.'] } },
    });

    const result = await store.createProjectForClient(7, { name: '' });

    expect(result.success).toBe(false);
    expect(result.message).toBe('Requerido.');
    expect(store.projectsByClient[7]).toEqual([]);
  });

  it('invalidateProjectsCache(id) drops that client and the all bucket', () => {
    const store = useAccountingStore();
    store.projectsByClient = { 7: [], 8: [], all: [] };

    store.invalidateProjectsCache(7);

    expect(store.projectsByClient[7]).toBeUndefined();
    expect(store.projectsByClient.all).toBeUndefined();
    expect(store.projectsByClient[8]).toEqual([]);
  });

  it('a total invalidation forces the next fetch back to the network', async () => {
    const store = useAccountingStore();
    get_request.mockResolvedValue({ data: { results: [] } });

    await store.fetchProjectsForClient(7);
    await store.fetchProjectsForClient(7);
    expect(get_request).toHaveBeenCalledTimes(1);

    store.invalidateProjectsCache();
    await store.fetchProjectsForClient(7);

    expect(get_request).toHaveBeenCalledTimes(2);
  });
});
