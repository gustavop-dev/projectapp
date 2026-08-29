import { defineStore } from 'pinia';
import {
  create_request,
  delete_request,
  get_request,
  patch_request,
} from './services/request_http';
import { normalizeApiError } from './services/normalize_api_error';


function queryString(filters = {}) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== null && value !== undefined && value !== '') {
      params.set(key, Array.isArray(value) ? value.join(',') : String(value));
    }
  }
  return params.toString();
}


function emptyFacets() {
  return {
    total: 0,
    navigation_total: 0,
    without_project_count: 0,
    projects: [],
    clients: [],
    filters: {
      status: {}, channel: {}, direction: {}, message_status: {},
    },
  };
}


export const useCommunicationsStore = defineStore('communications', {
  state: () => ({
    threads: [],
    currentThread: null,
    count: 0,
    page: 1,
    numPages: 1,
    facets: emptyFacets(),
    isLoading: false,
    isThreadLoading: false,
    isMutating: false,
    error: null,
    threadError: null,
    threadsRequestId: 0,
  }),

  getters: {
    getThreadById: (state) => (id) => (
      state.threads.find((thread) => Number(thread.id) === Number(id)) || null
    ),
  },

  actions: {
    _replaceThread(thread) {
      this.threads = this.threads.map((item) => (
        item.id === thread.id ? { ...item, ...thread } : item
      ));
      if (this.currentThread?.id === thread.id) this.currentThread = thread;
    },

    _failure(error, fallback, target = 'error') {
      const fieldMessage = Object.values(error?.response?.data || {})
        .find((value) => typeof value === 'string');
      this[target] = error?.response?.data?.detail || fieldMessage || 'request_failed';
      return {
        success: false,
        errors: error?.response?.data,
        ...normalizeApiError(error, fallback),
      };
    },

    async fetchThreads(filters = {}) {
      const requestId = ++this.threadsRequestId;
      this.isLoading = true;
      this.error = null;
      try {
        const query = queryString(filters);
        const response = await get_request(
          `communications/threads/${query ? `?${query}` : ''}`,
        );
        if (requestId !== this.threadsRequestId) {
          return { success: true, stale: true, data: response.data };
        }
        this.threads = response.data?.results || [];
        this.count = response.data?.count || 0;
        this.page = response.data?.page || 1;
        this.numPages = response.data?.num_pages || 1;
        this.facets = response.data?.facets || emptyFacets();
        return { success: true, data: response.data };
      } catch (error) {
        if (requestId !== this.threadsRequestId) {
          return { success: false, stale: true };
        }
        return this._failure(error, 'No se pudieron cargar las comunicaciones.');
      } finally {
        if (requestId === this.threadsRequestId) this.isLoading = false;
      }
    },

    async fetchThread(id) {
      this.isThreadLoading = true;
      this.threadError = null;
      try {
        const response = await get_request(`communications/threads/${id}/`);
        this.currentThread = response.data;
        this._replaceThread(response.data);
        return { success: true, data: response.data };
      } catch (error) {
        return this._failure(error, 'No se pudo cargar el hilo.', 'threadError');
      } finally {
        this.isThreadLoading = false;
      }
    },

    clearCurrentThread() {
      this.currentThread = null;
      this.threadError = null;
    },

    async createThread(payload) {
      this.isMutating = true;
      this.error = null;
      try {
        const response = await create_request('communications/threads/', payload);
        this.threads = [response.data, ...this.threads];
        this.count += 1;
        this.currentThread = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        return this._failure(error, 'No se pudo crear el hilo.');
      } finally {
        this.isMutating = false;
      }
    },

    async updateThread(id, payload) {
      this.isMutating = true;
      try {
        const response = await patch_request(`communications/threads/${id}/`, payload);
        this._replaceThread(response.data);
        return { success: true, data: response.data };
      } catch (error) {
        return this._failure(error, 'No se pudo actualizar el hilo.');
      } finally {
        this.isMutating = false;
      }
    },

    async setThreadOpen(id, isOpen) {
      this.isMutating = true;
      try {
        const action = isOpen ? 'reopen' : 'close';
        const response = await create_request(
          `communications/threads/${id}/${action}/`,
          {},
        );
        this._replaceThread(response.data);
        return { success: true, data: response.data };
      } catch (error) {
        return this._failure(
          error,
          isOpen ? 'No se pudo reabrir el hilo.' : 'No se pudo cerrar el hilo.',
        );
      } finally {
        this.isMutating = false;
      }
    },

    async createMessage(threadId, payload) {
      this.isMutating = true;
      try {
        const response = await create_request(
          `communications/threads/${threadId}/messages/`,
          payload,
        );
        await this.fetchThread(threadId);
        return { success: true, data: response.data };
      } catch (error) {
        return this._failure(error, 'No se pudo registrar el mensaje.');
      } finally {
        this.isMutating = false;
      }
    },

    async updateDraft(messageId, payload) {
      this.isMutating = true;
      try {
        const response = await patch_request(
          `communications/messages/${messageId}/`, payload,
        );
        await this.fetchThread(response.data.thread_id);
        return { success: true, data: response.data };
      } catch (error) {
        return this._failure(error, 'No se pudo actualizar el borrador.');
      } finally {
        this.isMutating = false;
      }
    },

    async deleteDraft(message) {
      this.isMutating = true;
      try {
        await delete_request(`communications/messages/${message.id}/`);
        await this.fetchThread(message.thread_id);
        return { success: true };
      } catch (error) {
        return this._failure(error, 'No se pudo eliminar el borrador.');
      } finally {
        this.isMutating = false;
      }
    },

    async markSent(messageId, occurredAt = null) {
      this.isMutating = true;
      try {
        const payload = occurredAt ? { occurred_at: occurredAt } : {};
        const response = await create_request(
          `communications/messages/${messageId}/mark-sent/`, payload,
        );
        await this.fetchThread(response.data.thread_id);
        return { success: true, data: response.data };
      } catch (error) {
        return this._failure(error, 'No se pudo marcar el mensaje como enviado.');
      } finally {
        this.isMutating = false;
      }
    },

    async voidMessage(messageId, reason) {
      this.isMutating = true;
      try {
        const response = await create_request(
          `communications/messages/${messageId}/void/`, { reason },
        );
        await this.fetchThread(response.data.thread_id);
        return { success: true, data: response.data };
      } catch (error) {
        return this._failure(error, 'No se pudo anular el mensaje.');
      } finally {
        this.isMutating = false;
      }
    },

    async correctDate(messageId, occurredAt, reason) {
      this.isMutating = true;
      try {
        const response = await create_request(
          `communications/messages/${messageId}/correct-date/`,
          { occurred_at: occurredAt, reason },
        );
        await this.fetchThread(response.data.thread_id);
        return { success: true, data: response.data };
      } catch (error) {
        return this._failure(error, 'No se pudo corregir la fecha.');
      } finally {
        this.isMutating = false;
      }
    },
  },
});
