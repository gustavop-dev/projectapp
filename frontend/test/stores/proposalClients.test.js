/**
 * Tests for the proposalClients store.
 *
 * Covers: fetchClients (with search/orphans/limit params), searchClients
 * (with cancellation), fetchClient, createClient, updateClient,
 * deleteClient (orphan vs guarded), getters orphanClients/activeClients/
 * getClientById, error handling.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useProposalClientsStore } from '../../stores/proposalClients';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const {
  get_request,
  create_request,
  patch_request,
  delete_request,
} = require('../../stores/services/request_http');

const buildClient = (overrides = {}) => ({
  id: 1,
  name: 'Test Client',
  email: 'test@example.com',
  phone: '+57 300',
  company: 'TestCo',
  is_onboarded: false,
  is_email_placeholder: false,
  total_proposals: 0,
  is_orphan: true,
  created_at: '2026-04-09T00:00:00Z',
  updated_at: '2026-04-09T00:00:00Z',
  ...overrides,
});

describe('useProposalClientsStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useProposalClientsStore();
    jest.clearAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  // -------------------------------------------------------------------
  // Initial state
  // -------------------------------------------------------------------

  describe('initial state', () => {
    it('starts with empty clients array', () => {
      expect(store.clients).toEqual([]);
    });

    it('starts with null currentClient', () => {
      expect(store.currentClient).toBeNull();
    });

    it('starts with empty searchResults', () => {
      expect(store.searchResults).toEqual([]);
    });

    it('starts with isLoading false', () => {
      expect(store.isLoading).toBe(false);
    });

    it('starts with isSearching false', () => {
      expect(store.isSearching).toBe(false);
    });
  });

  // -------------------------------------------------------------------
  // Getters
  // -------------------------------------------------------------------

  describe('getters', () => {
    beforeEach(() => {
      store.clients = [
        buildClient({ id: 1, is_orphan: true }),
        buildClient({ id: 2, is_orphan: false, total_proposals: 3 }),
        buildClient({ id: 3, is_orphan: true }),
      ];
    });

    it('orphanClients returns only clients with is_orphan true', () => {
      expect(store.orphanClients).toHaveLength(2);
      expect(store.orphanClients.map((c) => c.id)).toEqual([1, 3]);
    });

    it('activeClients returns only clients with is_orphan false', () => {
      expect(store.activeClients).toHaveLength(1);
      expect(store.activeClients[0].id).toBe(2);
    });

    it('getClientById returns the matching client when present', () => {
      expect(store.getClientById(2)).toEqual(
        expect.objectContaining({ id: 2 }),
      );
    });

    it('getClientById returns null when id is unknown', () => {
      expect(store.getClientById(999)).toBeNull();
    });
  });

  // -------------------------------------------------------------------
  // fetchClients
  // -------------------------------------------------------------------

  describe('fetchClients', () => {
    it('fetches clients with no params and stores them', async () => {
      const data = [buildClient({ id: 10 })];
      get_request.mockResolvedValueOnce({ data });
      const result = await store.fetchClients();
      expect(get_request).toHaveBeenCalledWith('proposals/client-profiles/?limit=100');
      expect(result.success).toBe(true);
      expect(store.clients).toEqual(data);
    });

    it('passes search query in the URL', async () => {
      get_request.mockResolvedValueOnce({ data: [] });
      await store.fetchClients({ search: 'acme' });
      expect(get_request).toHaveBeenCalledWith(
        'proposals/client-profiles/?search=acme&limit=100',
      );
    });

    it('passes orphans=true in the URL', async () => {
      get_request.mockResolvedValueOnce({ data: [] });
      await store.fetchClients({ orphans: true });
      expect(get_request).toHaveBeenCalledWith(
        'proposals/client-profiles/?orphans=true&limit=100',
      );
    });

    it('passes orphans=false in the URL', async () => {
      get_request.mockResolvedValueOnce({ data: [] });
      await store.fetchClients({ orphans: false });
      expect(get_request).toHaveBeenCalledWith(
        'proposals/client-profiles/?orphans=false&limit=100',
      );
    });

    it('returns failure shape on network error', async () => {
      get_request.mockRejectedValueOnce({
        response: { data: { error: 'fetch_failed' } },
      });
      const result = await store.fetchClients();
      expect(result.success).toBe(false);
      expect(store.error).toBe('fetch_failed');
    });

    it('toggles isLoading around the request', async () => {
      let inFlightLoading;
      get_request.mockImplementationOnce(() => {
        inFlightLoading = store.isLoading;
        return Promise.resolve({ data: [] });
      });
      await store.fetchClients();
      expect(inFlightLoading).toBe(true);
      expect(store.isLoading).toBe(false);
    });
  });

  // -------------------------------------------------------------------
  // searchClients (autocomplete)
  // -------------------------------------------------------------------

  describe('searchClients', () => {
    it('passes the query to the search endpoint', async () => {
      get_request.mockResolvedValueOnce({ data: [] });
      await store.searchClients('john');
      expect(get_request).toHaveBeenCalledWith(
        'proposals/client-profiles/search/?q=john',
        expect.objectContaining({ signal: expect.any(AbortSignal) }),
      );
    });

    it('stores the returned results', async () => {
      const hits = [buildClient({ id: 1 }), buildClient({ id: 2 })];
      get_request.mockResolvedValueOnce({ data: hits });
      const result = await store.searchClients('q');
      expect(store.searchResults).toEqual(hits);
      expect(result.data).toEqual(hits);
    });

    it('returns cancelled flag when axios cancels the request', async () => {
      const error = new Error('canceled');
      error.name = 'CanceledError';
      get_request.mockRejectedValueOnce(error);
      const result = await store.searchClients('q');
      expect(result.success).toBe(false);
      expect(result.cancelled).toBe(true);
    });

    it('aborts the previous request when called twice in a row', async () => {
      let firstSignal;
      get_request.mockImplementationOnce((_url, opts) => {
        firstSignal = opts.signal;
        return new Promise(() => {}); // never resolves
      });
      get_request.mockResolvedValueOnce({ data: [] });
      const first = store.searchClients('a');
      const second = store.searchClients('ab');
      await second;
      expect(firstSignal.aborted).toBe(true);
      // Detach the un-resolved promise so jest doesn't warn
      first.catch(() => {});
    });
  });

  // -------------------------------------------------------------------
  // fetchClient
  // -------------------------------------------------------------------

  describe('fetchClient', () => {
    it('stores the fetched client as currentClient', async () => {
      const data = buildClient({ id: 7 });
      get_request.mockResolvedValueOnce({ data });
      const result = await store.fetchClient(7);
      expect(get_request).toHaveBeenCalledWith('proposals/client-profiles/7/');
      expect(store.currentClient).toEqual(data);
      expect(result.success).toBe(true);
    });
  });

  // -------------------------------------------------------------------
  // createClient
  // -------------------------------------------------------------------

  describe('createClient', () => {
    it('prepends the new client to the list', async () => {
      store.clients = [buildClient({ id: 1 })];
      const created = buildClient({ id: 99 });
      create_request.mockResolvedValueOnce({ data: created });
      const result = await store.createClient({ name: 'New One' });
      expect(create_request).toHaveBeenCalledWith(
        'proposals/client-profiles/create/',
        { name: 'New One' },
      );
      expect(store.clients[0]).toEqual(created);
      expect(result.success).toBe(true);
    });

    it('returns failure shape on validation error', async () => {
      create_request.mockRejectedValueOnce({
        response: { data: { error: 'name_or_email_required' } },
      });
      const result = await store.createClient({});
      expect(result.success).toBe(false);
    });
  });

  // -------------------------------------------------------------------
  // updateClient
  // -------------------------------------------------------------------

  describe('updateClient', () => {
    it('replaces the matching client in the list with the response', async () => {
      const original = buildClient({ id: 4, phone: 'old' });
      const updated = buildClient({ id: 4, phone: 'new' });
      store.clients = [original];
      patch_request.mockResolvedValueOnce({ data: updated });
      const result = await store.updateClient(4, { phone: 'new' });
      expect(patch_request).toHaveBeenCalledWith(
        'proposals/client-profiles/4/update/',
        { phone: 'new' },
      );
      expect(store.clients[0].phone).toBe('new');
      expect(result.success).toBe(true);
    });
  });

  // -------------------------------------------------------------------
  // deleteClient
  // -------------------------------------------------------------------

  describe('deleteClient', () => {
    it('removes the client from the list when the API returns 204', async () => {
      store.clients = [buildClient({ id: 1 }), buildClient({ id: 2 })];
      delete_request.mockResolvedValueOnce({ status: 204 });
      const result = await store.deleteClient(1);
      expect(delete_request).toHaveBeenCalledWith(
        'proposals/client-profiles/1/delete/',
      );
      expect(store.clients).toHaveLength(1);
      expect(store.clients[0].id).toBe(2);
      expect(result.success).toBe(true);
    });

    it('returns errorCode and count when the backend blocks the delete', async () => {
      store.clients = [buildClient({ id: 1, is_orphan: false })];
      delete_request.mockRejectedValueOnce({
        response: { data: { error: 'client_has_proposals', count: 3 } },
      });
      const result = await store.deleteClient(1);
      expect(result.success).toBe(false);
      expect(result.errorCode).toBe('client_has_proposals');
      expect(result.count).toBe(3);
      // Client must remain in the list when the delete fails.
      expect(store.clients).toHaveLength(1);
    });
  });
});
