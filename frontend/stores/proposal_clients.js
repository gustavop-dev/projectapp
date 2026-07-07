import { defineStore } from 'pinia';
import {
  get_request,
  create_request,
  patch_request,
  delete_request,
} from './services/request_http';

/**
 * Store for the proposal admin panel's client management surface.
 *
 * Backed by /api/proposals/client-profiles/* endpoints which expose
 * accounts.UserProfile (filtered to role='client') with annotated
 * proposal counts and orphan flags. The store is the single entry point
 * for the new clients page, the autocomplete component used in the
 * proposal create/edit forms, and the orphan-cleanup workflow.
 */
export const useProposalClientsStore = defineStore('proposalClients', {
  state: () => ({
    clients: [],
    currentClient: null,
    searchResults: [],
    isLoading: false,
    isSearching: false,
    isUpdating: false,
    error: null,
    _searchAbortController: null,
  }),

  getters: {
    /** Clients with zero proposals AND zero platform projects. */
    orphanClients: (state) => state.clients.filter((c) => c.is_orphan),

    /** Clients with at least one proposal or project. */
    activeClients: (state) => state.clients.filter((c) => !c.is_orphan),

    /** Lookup helper used by selection-aware UI. */
    getClientById: (state) => (id) =>
      state.clients.find((c) => c.id === id) || null,
  },

  actions: {
    // -----------------------------------------------------------------
    // List + filters
    // -----------------------------------------------------------------

    /**
     * Fetch clients with optional search and orphans filter.
     *
     * @param {Object} [params]
     * @param {string} [params.search] - icontains match on email/name/company.
     * @param {boolean|null} [params.orphans] - true=only orphans,
     *     false=only active, null/undefined=all.
     * @param {number} [params.limit=100] - hard cap 500 (server-side).
     */
    async fetchClients({ search = '', orphans = null, limit = 100 } = {}) {
      this.isLoading = true;
      this.error = null;
      try {
        const query = new URLSearchParams();
        if (search) query.set('search', search);
        if (orphans === true) query.set('orphans', 'true');
        if (orphans === false) query.set('orphans', 'false');
        if (limit) query.set('limit', String(limit));
        const url = `proposals/client-profiles/${
          query.toString() ? `?${query.toString()}` : ''
        }`;
        const response = await get_request(url);
        this.clients = Array.isArray(response.data) ? response.data : [];
        this.isLoading = false;
        return { success: true, data: this.clients };
      } catch (error) {
        const data = error?.response?.data;
        this.error = data?.error || 'fetch_failed';
        this.isLoading = false;
        return { success: false, errors: data };
      }
    },

    // -----------------------------------------------------------------
    // Search / autocomplete
    // -----------------------------------------------------------------

    /**
     * Lightweight search for the autocomplete component. Cancels any
     * in-flight request via AbortController so rapid keystrokes don't
     * race each other in the UI.
     *
     * @param {string} query - free-form search text (any field).
     * @returns {Promise<{success:boolean,data?:Array,errors?:Object}>}
     */
    async searchClients(query) {
      // Cancel any in-flight request from a previous keystroke.
      if (this._searchAbortController) {
        this._searchAbortController.abort();
      }
      const controller = new AbortController();
      this._searchAbortController = controller;

      this.isSearching = true;
      this.error = null;
      try {
        const url = `proposals/client-profiles/search/?q=${encodeURIComponent(
          query || '',
        )}`;
        const response = await get_request(url, { signal: controller.signal });
        this.searchResults = Array.isArray(response.data) ? response.data : [];
        if (this._searchAbortController === controller) {
          this._searchAbortController = null;
          this.isSearching = false;
        }
        return { success: true, data: this.searchResults };
      } catch (error) {
        const data = error?.response?.data;
        // Cancellation is not a real error — keep results untouched.
        if (error.name === 'CanceledError' || error.code === 'ERR_CANCELED') {
          if (this._searchAbortController === controller) {
            this._searchAbortController = null;
            this.isSearching = false;
          }
          return { success: false, cancelled: true };
        }
        if (this._searchAbortController === controller) {
          this._searchAbortController = null;
          this.isSearching = false;
        }
        this.error = data?.error || 'search_failed';
        return { success: false, errors: data };
      }
    },

    // -----------------------------------------------------------------
    // Detail
    // -----------------------------------------------------------------

    /** Fetch one client with the full nested proposals history. */
    async fetchClient(id) {
      this.error = null;
      try {
        const response = await get_request(
          `proposals/client-profiles/${id}/`,
        );
        this.currentClient = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        const data = error?.response?.data;
        this.error = data?.error || 'fetch_failed';
        return { success: false, errors: data };
      }
    },

    // -----------------------------------------------------------------
    // Create / update / delete
    // -----------------------------------------------------------------

    /**
     * Standalone create — does NOT send invitation email. When `email`
     * is omitted the backend generates a placeholder cliente_<id>@temp.example.com.
     */
    async createClient(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request(
          'proposals/client-profiles/create/',
          payload,
        );
        this.clients = [response.data, ...this.clients];
        this.isUpdating = false;
        return { success: true, data: response.data };
      } catch (error) {
        const data = error?.response?.data;
        this.error = data?.error || 'create_failed';
        this.isUpdating = false;
        return { success: false, errors: data };
      }
    },

    /** Update profile + cascade snapshot to all linked proposals. */
    async updateClient(id, payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(
          `proposals/client-profiles/${id}/update/`,
          payload,
        );
        this.clients = this.clients.map((c) =>
          c.id === id ? response.data : c,
        );
        if (this.currentClient?.id === id) {
          this.currentClient = { ...this.currentClient, ...response.data };
        }
        this.isUpdating = false;
        return { success: true, data: response.data };
      } catch (error) {
        const data = error?.response?.data;
        this.error = data?.error || 'update_failed';
        this.isUpdating = false;
        return { success: false, errors: data };
      }
    },

    /**
     * Delete a client (and the underlying User). Backend enforces the
     * orphan rule (zero proposals + zero projects); a 400 with
     * `client_has_proposals` / `client_has_projects` is returned otherwise.
     */
    async deleteClient(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        await delete_request(`proposals/client-profiles/${id}/delete/`);
        this.clients = this.clients.filter((c) => c.id !== id);
        if (this.currentClient?.id === id) {
          this.currentClient = null;
        }
        this.isUpdating = false;
        return { success: true };
      } catch (error) {
        const data = error?.response?.data;
        this.error = data?.error || 'delete_failed';
        this.isUpdating = false;
        return {
          success: false,
          errorCode: data?.error,
          count: data?.count,
          errors: data,
        };
      }
    },
  },
});
