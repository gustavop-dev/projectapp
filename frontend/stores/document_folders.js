import { defineStore } from 'pinia';
import { isRootInScope, matchesScope } from '~/utils/archiveScope';
import { buildFolderRollup, directRollupRecord } from '~/utils/folderRollup';
import {
  get_request, create_request, patch_request, delete_request,
} from './services/request_http';
import { normalizeApiError } from './services/normalize_api_error';

export const useDocumentFolderStore = defineStore('documentFolders', {
  state: () => ({
    // Una sola lista con los dos estados. La jerarquía archivada necesita saber
    // si el padre de una carpeta está activo o archivado, y con listas
    // separadas «el padre no vino en esta página» y «el padre está activo» son
    // indistinguibles. Los consumidores que sólo aceptan destinos activos usan
    // el getter `activeFolders`.
    folders: [],
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    activeFolders: (state) => state.folders.filter((f) => !f.is_archived),

    archivedFolders: (state) => state.folders.filter((f) => f.is_archived),

    rootFolders() {
      return this.scopedRootFolders('active');
    },

    // Carpetas en la cima del scope: sin padre, o con un padre que no se lista
    // en este scope y por lo tanto no puede contenerlas visualmente.
    scopedRootFolders: (state) => (scope) => state.folders.filter(
      (f) => matchesScope(f, scope)
        && isRootInScope(f.parent, (id) => state.folders.find((c) => c.id === id) || null, scope),
    ),

    folderById: (state) => (id) => state.folders.find((f) => f.id === id) || null,

    // El default 'active' preserva a todos los callers previos al eje de estado.
    childrenOf: (state) => (id, scope = 'active') => state.folders.filter(
      (f) => f.parent === id && matchesScope(f, scope),
    ),

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

    // ── Conteos del subárbol ──────────────────────────────────────────────
    // Los cuatro rollups son getters SIN ARGUMENTOS a propósito, y eso es
    // load-bearing: un getter que devuelve una closure no lo cachea Pinia, así
    // que `rollup: (state) => (scope) => build(...)` reconstruiría el mapa
    // entero una vez POR FILA del panel. Sin argumentos son `computed` de
    // verdad, y se recalculan sólo cuando cambia `folders` — que es justo lo
    // que hace que los contadores sigan a cualquier archivado, movimiento o
    // borrado sin código de invalidación: `refreshView` vuelve a pedir la
    // lista y toda la cadena de ancestros se recalcula sola.

    /** Modo normal: se cuenta lo activo y se baja sólo por carpetas activas. */
    activeRollup(state) {
      return buildFolderRollup(state.folders, {
        countingScope: 'active', membershipScope: 'active',
      });
    },

    /**
     * Modo archivado: se cuenta lo archivado, pero se baja por el árbol
     * COMPLETO — una carpeta activa puede guardar documentos archivados, y
     * bajando sólo por archivadas no quedarían en ninguna fila.
     */
    archivedRollup(state) {
      return buildFolderRollup(state.folders, {
        countingScope: 'archived', membershipScope: 'all',
      });
    },

    /** Modo mixto: los dos estados, sobre el árbol completo. */
    mixedRollup(state) {
      return buildFolderRollup(state.folders, {
        countingScope: 'all', membershipScope: 'all',
      });
    },

    /**
     * Lo que se llevaría por delante archivar la carpeta.
     *
     * `archive_folder` arrastra TODO el subárbol (`get_descendant_ids`, sin
     * mirar estados) pero sólo tiene efecto sobre lo que todavía está activo:
     * de ahí la combinación activo-sobre-árbol-completo, que no coincide con
     * ninguno de los tres modos de vista.
     */
    cascadeRollup(state) {
      return buildFolderRollup(state.folders, {
        countingScope: 'active', membershipScope: 'all',
      });
    },

    rollupFor() {
      return (scope) => {
        if (scope === 'archived') return this.archivedRollup;
        if (scope === 'all') return this.mixedRollup;
        return this.activeRollup;
      };
    },

    /**
     * Conteos de la carpeta con todo lo que cuelga de ella.
     *
     * Cae a los conteos DIRECTOS cuando la carpeta no está en el mapa: los
     * resultados de `searchFolders` son carpetas que a propósito no viven en
     * `folders`, y prefieren un número corto a un cero.
     */
    rollupOf() {
      return (folder, scope = 'active') => (
        this.rollupFor(scope).get(folder?.id) ?? directRollupRecord(folder, scope)
      );
    },

    /** El número de documentos de la fila del panel: el subárbol entero. */
    recursiveDocumentCount() {
      return (folder, scope = 'active') => this.rollupOf(folder, scope).docs;
    },

    /** Lo que arrastraría archivar la carpeta, para el aviso de confirmación. */
    cascadeContentOf() {
      return (folder) => (
        this.cascadeRollup.get(folder?.id) ?? directRollupRecord(folder, 'active')
      );
    },

    /** Elementos archivados que la carpeta todavía guarda (estado mixto). */
    archivedContentCount: () => (folder) => (folder?.archived_document_count || 0)
      + (folder?.archived_children_count || 0),

    /**
     * Todo lo que contiene, archivado incluido.
     *
     * Es el criterio del 409 de borrado del backend, así que es el que decide
     * si el ícono de eliminar puede ofrecerse: contarlo sólo con lo activo
     * dejaba habilitado un botón que después fallaba. Usa los contadores
     * absolutos: `document_count` es relativo al estado de la fila y sumarlo
     * con el archivado duplicaría una carpeta archivada.
     */
    totalContentCount() {
      return (folder) => {
        const activeDocs = folder?.active_document_count
          ?? (folder?.is_archived ? 0 : folder?.document_count || 0);
        const activeSubs = folder?.active_children_count
          ?? (folder?.is_archived ? 0 : folder?.children_count || 0);
        return activeDocs + activeSubs + this.archivedContentCount(folder);
      };
    },
  },

  actions: {
    /**
     * Trae las carpetas de los dos estados; `{ scope }` acota si hace falta.
     *
     * El default `all` es deliberado: una lista que sólo a veces contiene
     * archivadas volvería dependiente del estado cada cálculo de raíz y cada
     * insignia. Quien necesite sólo activas usa el getter `activeFolders`.
     */
    async fetchFolders({ scope = 'all', order, search } = {}) {
      this.isLoading = true;
      this.error = null;
      try {
        const params = new URLSearchParams();
        params.set('scope', scope);
        if (search) params.set('search', search);
        if (scope === 'archived' && order === 'oldest') params.set('order', 'oldest');
        const response = await get_request(`document-folders/?${params.toString()}`);
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

    /**
     * Carpetas que coinciden con el texto, en cualquier estado.
     *
     * Vive aparte de `fetchFolders` para no pisar el árbol de navegación con
     * un subconjunto: la búsqueda es una vista, no un filtro del árbol.
     */
    async searchFolders(term) {
      this.error = null;
      try {
        const params = new URLSearchParams({ scope: 'all', search: term });
        const response = await get_request(`document-folders/?${params.toString()}`);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'search_folders_failed';
        console.error('Error searching folders:', error);
        return { success: false, errors: error.response?.data, data: [] };
      }
    },

    /** Archiva la carpeta y su contenido; devuelve los conteos de la cascada. */
    async archiveFolder(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`document-folders/${id}/archive/`, {});
        return {
          success: true,
          data: response.data,
          archivedFolders: response.data?.archived_folders || 0,
          archivedDocuments: response.data?.archived_documents || 0,
        };
      } catch (error) {
        this.error = 'archive_folder_failed';
        console.error('Error archiving folder:', error);
        return {
          success: false,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudo archivar la carpeta.'),
        };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * Restaura la carpeta, su cadena de contenedores y lo que ella arrastró.
     *
     * `restoredChain` son los ancestros que hubo que reabrir; `restoredFolders`
     * y `restoredDocuments` siguen contando sólo la cascada propia.
     */
    async unarchiveFolder(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`document-folders/${id}/unarchive/`, {});
        return {
          success: true,
          data: response.data,
          restoredFolders: response.data?.restored_folders || 0,
          restoredDocuments: response.data?.restored_documents || 0,
          restoredChain: response.data?.restored_chain || [],
        };
      } catch (error) {
        this.error = 'unarchive_folder_failed';
        console.error('Error unarchiving folder:', error);
        return {
          success: false,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudo restaurar la carpeta.'),
        };
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
        // Se replica lo que hace el backend (`order` = índice) y se reordena
        // con el mismo criterio del modelo. Reemplazar la lista entera no
        // servía: `orderedIds` es sólo el nivel que se arrastró, no el árbol.
        orderedIds.forEach((id, index) => {
          const folder = this.folders.find((f) => f.id === id);
          if (folder) folder.order = index;
        });
        this.folders.sort((a, b) => a.order - b.order || a.name.localeCompare(b.name));
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
