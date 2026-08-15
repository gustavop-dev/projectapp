import { defineStore } from 'pinia';
import { get_request, create_request, patch_request } from './services/request_http';
import { normalizeApiError } from './services/normalize_api_error';
import { useAccountingStore } from './accounting';

/**
 * The accounting pickers memoize projects per client forever; any module
 * mutation must drop that cache or a rename/archive would keep serving the
 * stale entry in every form. Total invalidation on purpose: mutations here
 * are rare and the picker lists are tiny.
 */
function invalidatePickerCache() {
  useAccountingStore().invalidateProjectsCache();
}

/**
 * Panel-side store for the Projects module (Plataforma space).
 *
 * Session/CSRF client like every content store — the platform keeps its own
 * JWT store (platform-projects.js) for /platform views. `createRecord` and
 * `updateRecord` keep the `(entity, ...)` signature so the page can drive
 * them through useAccountingCrudPage.
 */
export const usePanelProjectsStore = defineStore('panel_projects', {
  state: () => ({
    records: [],
    meta: {
      total: 0,
      active: 0,
      archived: 0,
      clients_without_projects: 0,
      records_without_project: 0,
    },
    isLoading: false,
    isUpdating: false,
    error: null,
    clientsWithoutProjects: [],
    isLoadingClientsWithoutProjects: false,
  }),

  actions: {
    async fetchProjects() {
      this.isLoading = true;
      this.error = null;
      try {
        // One load with scope=all: the module filters client-side, same
        // approach as the accounting tabs (the volume is tiny).
        const response = await get_request('projects/?scope=all');
        this.records = response.data.results;
        this.meta = response.data.meta;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_failed';
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudieron cargar los proyectos.'),
        };
      } finally {
        this.isLoading = false;
      }
    },

    /** `(entity, payload)` — signature shared with useAccountingCrudPage. */
    async createRecord(entity, payload) {
      this.isUpdating = true;
      try {
        const response = await create_request('projects/create/', payload);
        await this.fetchProjects();
        invalidatePickerCache();
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudo crear el proyecto.'),
        };
      } finally {
        this.isUpdating = false;
      }
    },

    async updateRecord(entity, id, payload) {
      this.isUpdating = true;
      try {
        const response = await patch_request(`projects/${id}/update/`, payload);
        await this.fetchProjects();
        invalidatePickerCache();
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudo actualizar el proyecto.'),
        };
      } finally {
        this.isUpdating = false;
      }
    },

    async archiveProject(id) {
      this.isUpdating = true;
      try {
        const response = await patch_request(`projects/${id}/archive/`, {});
        await this.fetchProjects();
        invalidatePickerCache();
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudo archivar el proyecto.'),
        };
      } finally {
        this.isUpdating = false;
      }
    },

    async unarchiveProject(id) {
      this.isUpdating = true;
      try {
        const response = await patch_request(`projects/${id}/unarchive/`, {});
        await this.fetchProjects();
        invalidatePickerCache();
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudo restaurar el proyecto.'),
        };
      } finally {
        this.isUpdating = false;
      }
    },

    /** Preview of the assign flow: the client's records without a project. */
    async fetchUnlinkedRecords(id) {
      try {
        const response = await get_request(`projects/${id}/unlinked-records/`);
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudieron cargar los registros sin proyecto.'),
        };
      }
    },

    /** Assign the project to the confirmed ids; refetch so counts move. */
    async assignUnlinkedRecords(id, payload) {
      this.isUpdating = true;
      try {
        const response = await create_request(`projects/${id}/assign-unlinked/`, payload);
        await this.fetchProjects();
        invalidatePickerCache();
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudieron asignar los registros.'),
        };
      } finally {
        this.isUpdating = false;
      }
    },

    async fetchClientsWithoutProjects() {
      this.isLoadingClientsWithoutProjects = true;
      try {
        const response = await get_request(
          'proposals/client-profiles/?without_projects=true&limit=500',
        );
        this.clientsWithoutProjects = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudieron cargar los clientes sin proyecto.'),
        };
      } finally {
        this.isLoadingClientsWithoutProjects = false;
      }
    },
  },
});
