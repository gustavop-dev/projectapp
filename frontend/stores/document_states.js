import { defineStore } from 'pinia';
import {
  create_request,
  delete_request,
  get_request,
  patch_request,
} from './services/request_http';
import { normalizeApiError } from './services/normalize_api_error';

export const useDocumentStateStore = defineStore('documentStates', {
  state: () => ({
    states: [],
    groups: [],
    history: [],
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    activeStates: (state) => state.states.filter((item) => item.is_active && !item.merged_into),
    statesByGroup() {
      return this.groups.map((group) => ({
        ...group,
        states: this.activeStates.filter((state) => state.group === group.id),
      }));
    },
    stateByKey: (state) => (key) => state.states.find((item) => item.system_key === key),
  },

  actions: {
    async fetchCatalog({ includeRetired = false } = {}) {
      this.isLoading = true;
      this.error = null;
      try {
        const suffix = includeRetired ? '?include_retired=1' : '';
        const [statesResponse, groupsResponse] = await Promise.all([
          get_request(`document-states/${suffix}`),
          get_request('document-state-groups/'),
        ]);
        this.states = Array.isArray(statesResponse.data) ? statesResponse.data : [];
        this.groups = Array.isArray(groupsResponse.data) ? groupsResponse.data : [];
        return { success: true, data: this.states };
      } catch (error) {
        this.error = 'fetch_failed';
        return { success: false, ...normalizeApiError(error, 'No se pudo cargar el catálogo.') };
      } finally {
        this.isLoading = false;
      }
    },

    async suggest(query) {
      if (!query?.trim()) return { success: true, data: [] };
      try {
        const response = await get_request(
          `document-states/suggestions/?q=${encodeURIComponent(query.trim())}`,
        );
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudieron buscar parecidos.') };
      }
    },

    async createState(payload) {
      this.isUpdating = true;
      try {
        const response = await create_request('document-states/', payload);
        await this.fetchCatalog();
        return { success: true, data: response.data };
      } catch (error) {
        if (error.response?.status === 409 && error.response?.data?.code === 'similar_states') {
          return {
            success: false,
            needsConfirmation: true,
            suggestions: error.response.data.suggestions || [],
            message: error.response.data.detail,
          };
        }
        return { success: false, ...normalizeApiError(error, 'No se pudo crear el estado.') };
      } finally {
        this.isUpdating = false;
      }
    },

    async updateState(id, payload) {
      this.isUpdating = true;
      try {
        const response = await patch_request(`document-states/${id}/`, payload);
        await this.fetchCatalog({ includeRetired: true });
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo actualizar el estado.') };
      } finally {
        this.isUpdating = false;
      }
    },

    async retireState(id) {
      this.isUpdating = true;
      try {
        const response = await create_request(`document-states/${id}/retire/`, {});
        await this.fetchCatalog({ includeRetired: true });
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo retirar el estado.') };
      } finally {
        this.isUpdating = false;
      }
    },

    async mergeState(id, targetStateId) {
      this.isUpdating = true;
      try {
        const response = await create_request(`document-states/${id}/merge/`, {
          target_state_id: targetStateId,
        });
        await this.fetchCatalog({ includeRetired: true });
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudieron fusionar los estados.') };
      } finally {
        this.isUpdating = false;
      }
    },

    async createGroup(payload) {
      try {
        const response = await create_request('document-state-groups/', payload);
        await this.fetchCatalog();
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo crear el grupo.') };
      }
    },

    async updateGroup(id, payload) {
      try {
        const response = await patch_request(`document-state-groups/${id}/`, payload);
        await this.fetchCatalog({ includeRetired: true });
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo actualizar el grupo.') };
      }
    },

    async openEpisode(documentId, stateId, openedAt = null, origin = 'manual') {
      this.isUpdating = true;
      try {
        const payload = { state_id: stateId, origin };
        if (openedAt) payload.opened_at = openedAt;
        const response = await create_request(`documents/${documentId}/state-episodes/`, payload);
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo agregar el estado.') };
      } finally {
        this.isUpdating = false;
      }
    },

    async closeEpisode(documentId, episodeId, outcome = 'completed', note = '') {
      this.isUpdating = true;
      try {
        const response = await create_request(
          `documents/${documentId}/state-episodes/${episodeId}/close/`,
          { outcome, note },
        );
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo cerrar el estado.') };
      } finally {
        this.isUpdating = false;
      }
    },

    async correctEpisode(documentId, episodeId, openedAt) {
      try {
        const response = await patch_request(
          `documents/${documentId}/state-episodes/${episodeId}/opened-at/`,
          { opened_at: openedAt },
        );
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo corregir la fecha.') };
      }
    },

    async fetchHistory(documentId) {
      this.isLoading = true;
      try {
        const response = await get_request(`documents/${documentId}/state-history/`);
        this.history = Array.isArray(response.data) ? response.data : [];
        return { success: true, data: this.history };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo cargar el historial.') };
      } finally {
        this.isLoading = false;
      }
    },

    async createNote(documentId, payload) {
      try {
        const response = await create_request(`documents/${documentId}/notes/`, payload);
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo agregar la observación.') };
      }
    },

    async updateNote(documentId, noteId, payload) {
      try {
        const response = await patch_request(`documents/${documentId}/notes/${noteId}/`, payload);
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo actualizar la observación.') };
      }
    },

    async finishNote(documentId, noteId, payload) {
      try {
        const response = await create_request(
          `documents/${documentId}/notes/${noteId}/finish/`, payload,
        );
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo cerrar la observación.') };
      }
    },

    async fetchDeletedNotes(documentId) {
      try {
        const response = await get_request(`documents/${documentId}/notes/?scope=deleted`);
        return { success: true, data: Array.isArray(response.data) ? response.data : [] };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo cargar la papelera.') };
      }
    },

    async fetchNoteEvents(documentId) {
      try {
        const response = await get_request(`documents/${documentId}/notes/events/`);
        return { success: true, data: Array.isArray(response.data) ? response.data : [] };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo cargar la actividad.') };
      }
    },

    async deleteNote(documentId, noteId) {
      try {
        const response = await delete_request(`documents/${documentId}/notes/${noteId}/`);
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo eliminar la observación.') };
      }
    },

    async bulkDeleteNotes(documentId, noteIds) {
      try {
        const response = await create_request(
          `documents/${documentId}/notes/bulk-delete/`,
          { note_ids: noteIds },
        );
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudieron eliminar las observaciones.') };
      }
    },

    async restoreNote(documentId, noteId) {
      try {
        const response = await create_request(
          `documents/${documentId}/notes/${noteId}/restore/`,
          {},
        );
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, ...normalizeApiError(error, 'No se pudo restaurar la observación.') };
      }
    },
  },
});
