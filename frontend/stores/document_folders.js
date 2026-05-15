import { defineStore } from 'pinia';
import {
  get_request, create_request, patch_request, delete_request,
} from './services/request_http';

export const useDocumentFolderStore = defineStore('documentFolders', {
  state: () => ({
    folders: [],
    isLoading: false,
    isUpdating: false,
    error: null,
    newlyCreatedId: null,
    // Non-reactive timer handle (Pinia doesn't proxy non-state assignments).
    _newlyCreatedTimer: null,
  }),

  getters: {
    getById: (state) => (id) => state.folders.find((f) => f.id === id) || null,

    /**
     * Build a tree from the flat folders array.
     * Returns root-level nodes; each node is { folder, children: [...] }.
     */
    tree: (state) => {
      const byParent = new Map();
      for (const f of state.folders) {
        const key = f.parent ?? null;
        if (!byParent.has(key)) byParent.set(key, []);
        byParent.get(key).push(f);
      }
      const sortSiblings = (arr) =>
        arr.slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0) || a.name.localeCompare(b.name));
      const build = (parentId) =>
        sortSiblings(byParent.get(parentId) || []).map((folder) => ({
          folder,
          children: build(folder.id),
        }));
      return build(null);
    },

    /**
     * IDs of all descendants of `id` (excluding self).
     */
    descendantIdsOf: (state) => (id) => {
      const childrenByParent = new Map();
      for (const f of state.folders) {
        const key = f.parent ?? null;
        if (!childrenByParent.has(key)) childrenByParent.set(key, []);
        childrenByParent.get(key).push(f);
      }
      const result = new Set();
      const stack = [...(childrenByParent.get(id) || [])];
      while (stack.length) {
        const node = stack.pop();
        if (result.has(node.id)) continue;
        result.add(node.id);
        stack.push(...(childrenByParent.get(node.id) || []));
      }
      return result;
    },

    /**
     * Ancestor folders ordered root→parent (excluding self).
     */
    ancestorsOf: (state) => (id) => {
      const chain = [];
      let current = state.folders.find((f) => f.id === id);
      const seen = new Set();
      while (current && current.parent != null && !seen.has(current.parent)) {
        seen.add(current.parent);
        const parent = state.folders.find((f) => f.id === current.parent);
        if (!parent) break;
        chain.push(parent);
        current = parent;
      }
      chain.reverse();
      return chain;
    },
  },

  actions: {
    async fetchFolders() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request('document-folders/');
        this.folders = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_folders_failed';
        console.error('Error fetching folders:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    async createFolder(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('document-folders/create/', payload);
        this.folders.push(response.data);
        this.folders.sort((a, b) => a.order - b.order || a.name.localeCompare(b.name));
        this.newlyCreatedId = response.data.id;
        if (this._newlyCreatedTimer) clearTimeout(this._newlyCreatedTimer);
        this._newlyCreatedTimer = setTimeout(() => {
          this.newlyCreatedId = null;
        }, 2500);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'create_folder_failed';
        console.error('Error creating folder:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async updateFolder(id, payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`document-folders/${id}/update/`, payload);
        const idx = this.folders.findIndex((f) => f.id === id);
        if (idx !== -1) this.folders.splice(idx, 1, response.data);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_folder_failed';
        console.error('Error updating folder:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async deleteFolder(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        await delete_request(`document-folders/${id}/delete/`);
        this.folders = this.folders.filter((f) => f.id !== id);
        return { success: true };
      } catch (error) {
        this.error = 'delete_folder_failed';
        console.error('Error deleting folder:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * Reparent a folder and optionally set its position among new siblings.
     * Re-fetches all folders on success so counts/order stay consistent.
     */
    async moveFolder(id, { parent_id = null, position = null } = {}) {
      this.isUpdating = true;
      this.error = null;
      try {
        const body = { parent_id };
        if (position !== null) body.position = position;
        await create_request(`document-folders/${id}/move/`, body);
        await this.fetchFolders();
        return { success: true };
      } catch (error) {
        this.error = 'move_folder_failed';
        console.error('Error moving folder:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * Reorder siblings within a parent scope (parent_id may be null for root).
     */
    async reorderFolders({ parent_id = null, ids } = {}) {
      this.isUpdating = true;
      this.error = null;
      try {
        await create_request('document-folders/reorder/', { parent_id, ids });
        // Apply order locally for the affected siblings.
        const orderMap = new Map(ids.map((id, idx) => [id, idx]));
        for (const folder of this.folders) {
          if (orderMap.has(folder.id)) folder.order = orderMap.get(folder.id);
        }
        return { success: true };
      } catch (error) {
        console.error('Error reordering folders:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },
  },
});
