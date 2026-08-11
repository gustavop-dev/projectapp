import { defineStore } from 'pinia';
import {
  get_request, create_request, patch_request, delete_request,
} from './services/request_http';

export const useDocumentFolderStore = defineStore('documentFolders', {
  state: () => ({
    folders: [],
    // Slice aparte y no una lista mezclada: los getters de jerarquía
    // (childrenOf/ancestorsOf/descendantIdsOf) alimentan los selectores de
    // carpeta y los chequeos de ciclo del drag & drop, y meter archivadas
    // ahí los corrompería.
    archivedFolders: [],
    isLoading: false,
    isArchivedLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    rootFolders: (state) => state.folders.filter((f) => f.parent == null),

    folderById: (state) => (id) => state.folders.find((f) => f.id === id) || null,

    childrenOf: (state) => (id) => state.folders.filter((f) => f.parent === id),

    // Cadena raíz → carpeta actual; set de visitados evita bucles con datos cíclicos.
    ancestorsOf: (state) => (id) => {
      const chain = [];
      const visited = new Set();
      let current = state.folders.find((f) => f.id === id) || null;
      while (current && !visited.has(current.id)) {
        visited.add(current.id);
        chain.unshift(current);
        current = current.parent == null
          ? null
          : state.folders.find((f) => f.id === current.parent) || null;
      }
      return chain;
    },

    // IDs de todas las subcarpetas (recursivo) — usado para excluir destinos inválidos.
    descendantIdsOf: (state) => (id) => {
      const result = new Set();
      const pending = state.folders.filter((f) => f.parent === id).map((f) => f.id);
      while (pending.length) {
        const current = pending.pop();
        if (result.has(current)) continue;
        result.add(current);
        state.folders
          .filter((f) => f.parent === current)
          .forEach((f) => pending.push(f.id));
      }
      return result;
    },
  },

  actions: {
    /**
     * Carpetas activas por defecto. `{ archived: true }` trae sólo las
     * archivadas y las deja en su propio slice.
     *
     * El default active-only es deliberado: los selectores de carpeta destino
     * de create.vue y [id]/edit.vue llaman a esta acción, y una carpeta
     * archivada nunca debe ofrecerse como destino.
     */
    async fetchFolders({ archived = false, order } = {}) {
      const loadingKey = archived ? 'isArchivedLoading' : 'isLoading';
      this[loadingKey] = true;
      this.error = null;
      try {
        const params = new URLSearchParams();
        if (archived) params.set('archived', '1');
        if (archived && order === 'oldest') params.set('order', 'oldest');
        const query = params.toString();
        const response = await get_request(
          query ? `document-folders/?${query}` : 'document-folders/',
        );
        if (archived) this.archivedFolders = response.data;
        else this.folders = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_folders_failed';
        console.error('Error fetching folders:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this[loadingKey] = false;
      }
    },

    /** Archiva la carpeta y su contenido; devuelve los conteos de la cascada. */
    async archiveFolder(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`document-folders/${id}/archive/`, {});
        this.folders = this.folders.filter((f) => f.id !== id);
        return {
          success: true,
          data: response.data,
          archivedFolders: response.data?.archived_folders || 0,
          archivedDocuments: response.data?.archived_documents || 0,
        };
      } catch (error) {
        this.error = 'archive_folder_failed';
        console.error('Error archiving folder:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /** Restaura la carpeta y exactamente lo que su archivado arrastró. */
    async unarchiveFolder(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`document-folders/${id}/unarchive/`, {});
        this.archivedFolders = this.archivedFolders.filter((f) => f.id !== id);
        return {
          success: true,
          data: response.data,
          restoredFolders: response.data?.restored_folders || 0,
          restoredDocuments: response.data?.restored_documents || 0,
        };
      } catch (error) {
        this.error = 'unarchive_folder_failed';
        console.error('Error unarchiving folder:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async createFolder(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('document-folders/create/', payload);
        this.folders.push(response.data);
        this.folders.sort((a, b) => a.order - b.order || a.name.localeCompare(b.name));
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
        // También del slice archivado: lo archivado se puede borrar desde su
        // propia vista, y la fila debe desaparecer de ahí.
        this.archivedFolders = this.archivedFolders.filter((f) => f.id !== id);
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

    async reorderFolders(orderedIds) {
      this.isUpdating = true;
      this.error = null;
      try {
        await create_request('document-folders/reorder/', { ids: orderedIds });
        const reordered = orderedIds.map((id) => this.folders.find((f) => f.id === id)).filter(Boolean);
        if (reordered.length === this.folders.length) this.folders = reordered;
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
