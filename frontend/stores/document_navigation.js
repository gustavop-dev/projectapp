import { defineStore } from 'pinia';
import { get_request, patch_request } from './services/request_http';
import { normalizeApiError } from './services/normalize_api_error';

function emptyCounts() {
  return {
    active: { folders: 0, documents: 0 },
    archived: { folders: 0, documents: 0 },
  };
}

function emptyFacets() {
  return {
    totals: emptyCounts(),
    unassigned: {
      project: emptyCounts(),
      client: emptyCounts(),
    },
    projects: [],
    clients: [],
  };
}

export const useDocumentNavigationStore = defineStore('documentNavigation', {
  state: () => ({
    mode: 'project',
    persistedMode: 'project',
    preferenceReady: false,
    isSavingPreference: false,
    isLoading: false,
    facets: emptyFacets(),
    error: null,
  }),

  actions: {
    async fetchPreference() {
      try {
        const response = await get_request('accounts/panel-preferences/documents/');
        const mode = response.data?.navigation_mode === 'client' ? 'client' : 'project';
        this.mode = mode;
        this.persistedMode = mode;
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(
            error,
            'No se pudo recuperar la forma de navegación guardada.',
          ),
        };
      } finally {
        this.preferenceReady = true;
      }
    },

    setTransientMode(mode) {
      if (mode === 'project' || mode === 'client') this.mode = mode;
    },

    async persistMode(mode) {
      if (!['project', 'client'].includes(mode)) return { success: false };
      const previousMode = this.mode;
      this.mode = mode;
      this.isSavingPreference = true;
      try {
        const response = await patch_request(
          'accounts/panel-preferences/documents/',
          { navigation_mode: mode },
        );
        this.persistedMode = mode;
        return { success: true, data: response.data };
      } catch (error) {
        this.mode = previousMode;
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudo guardar el modo de navegación.'),
        };
      } finally {
        this.isSavingPreference = false;
      }
    },

    async fetchNavigation() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request('documents/navigation/');
        this.facets = response.data || emptyFacets();
        return { success: true, data: response.data };
      } catch (error) {
        const normalized = normalizeApiError(
          error,
          'No se pudieron cargar los proyectos y clientes.',
        );
        this.error = normalized.message;
        return { success: false, ...normalized };
      } finally {
        this.isLoading = false;
      }
    },
  },
});
