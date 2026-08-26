import { defineStore } from 'pinia';
import {
  create_request,
  get_request,
  patch_request,
} from './services/request_http';
import { normalizeApiError } from './services/normalize_api_error';

export const useProjectStateStore = defineStore('projectStates', {
  state: () => ({
    states: [],
    groups: [],
    history: [],
    preview: null,
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    activeStates: (state) => state.states.filter(
      (item) => item.is_active && !item.merged_into,
    ),
    statesByGroup() {
      return this.groups.map((group) => ({
        ...group,
        states: this.activeStates.filter((state) => state.group === group.id),
      }));
    },
    stateByKey: (state) => (key) => state.states.find(
      (item) => item.system_key === key,
    ),
  },

  actions: {
    async fetchCatalog({ includeRetired = false } = {}) {
      this.isLoading = true;
      this.error = null;
      try {
        const suffix = includeRetired ? '?include_retired=1' : '';
        const [statesResponse, groupsResponse] = await Promise.all([
          get_request(`project-states/${suffix}`),
          get_request('project-state-groups/'),
        ]);
        this.states = Array.isArray(statesResponse.data) ? statesResponse.data : [];
        this.groups = Array.isArray(groupsResponse.data) ? groupsResponse.data : [];
        return { success: true, data: this.states };
      } catch (error) {
        this.error = 'fetch_failed';
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudo cargar el catálogo.'),
        };
      } finally {
        this.isLoading = false;
      }
    },

    async suggest(query) {
      if (!query?.trim()) return { success: true, data: [] };
      try {
        const response = await get_request(
          `project-states/suggestions/?q=${encodeURIComponent(query.trim())}`,
        );
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudieron buscar parecidos.'),
        };
      }
    },

    async createState(payload) {
      this.isUpdating = true;
      try {
        const response = await create_request('project-states/', payload);
        await this.fetchCatalog({ includeRetired: true });
        return { success: true, data: response.data };
      } catch (error) {
        if (
          error.response?.status === 409
          && error.response?.data?.code === 'similar_states'
        ) {
          return {
            success: false,
            needsConfirmation: true,
            suggestions: error.response.data.suggestions || [],
            message: error.response.data.detail,
          };
        }
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudo crear el estado.'),
        };
      } finally {
        this.isUpdating = false;
      }
    },

    async updateState(id, payload) {
      this.isUpdating = true;
      try {
        const response = await patch_request(`project-states/${id}/`, payload);
        await this.fetchCatalog({ includeRetired: true });
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudo actualizar el estado.'),
        };
      } finally {
        this.isUpdating = false;
      }
    },

    async retireState(id) {
      this.isUpdating = true;
      try {
        const response = await create_request(`project-states/${id}/retire/`, {});
        await this.fetchCatalog({ includeRetired: true });
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudo retirar el estado.'),
        };
      } finally {
        this.isUpdating = false;
      }
    },

    async mergeState(id, targetStateId) {
      this.isUpdating = true;
      try {
        const response = await create_request(`project-states/${id}/merge/`, {
          target_state_id: targetStateId,
        });
        await this.fetchCatalog({ includeRetired: true });
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudieron fusionar los estados.'),
        };
      } finally {
        this.isUpdating = false;
      }
    },

    async previewTransition(projectId, payload) {
      this.isUpdating = true;
      this.preview = null;
      try {
        const response = await create_request(
          `projects/${projectId}/state-transitions/preview/`,
          payload,
        );
        this.preview = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudo calcular el impacto.'),
        };
      } finally {
        this.isUpdating = false;
      }
    },

    async applyTransition(projectId, payload) {
      this.isUpdating = true;
      try {
        const response = await create_request(
          `projects/${projectId}/state-transitions/`,
          payload,
        );
        this.preview = null;
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudo cambiar el estado.'),
        };
      } finally {
        this.isUpdating = false;
      }
    },

    async fetchHistory(projectId) {
      this.isLoading = true;
      try {
        const response = await get_request(`projects/${projectId}/state-history/`);
        this.history = Array.isArray(response.data) ? response.data : [];
        return { success: true, data: this.history };
      } catch (error) {
        return {
          success: false,
          ...normalizeApiError(error, 'No se pudo cargar el historial.'),
        };
      } finally {
        this.isLoading = false;
      }
    },

    clearPreview() {
      this.preview = null;
    },
  },
});
