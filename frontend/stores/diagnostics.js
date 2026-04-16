import { defineStore } from 'pinia';
import {
  get_request,
  create_request,
  patch_request,
  delete_request,
} from './services/request_http';

export const useDiagnosticsStore = defineStore('diagnostics', {
  state: () => ({
    diagnostics: [],
    current: null,
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    getById: (state) => (id) =>
      state.diagnostics.find((d) => Number(d.id) === Number(id)),

    visibleDocuments: (state) => {
      const docs = state.current?.documents || [];
      return [...docs].sort((a, b) => a.order - b.order);
    },
  },

  actions: {
    // ── Admin ────────────────────────────────────────────────────────
    async fetchAll(params = {}) {
      this.isLoading = true;
      this.error = null;
      try {
        const qs = new URLSearchParams(
          Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
        ).toString();
        const url = qs ? `diagnostics/?${qs}` : 'diagnostics/';
        const response = await get_request(url);
        this.diagnostics = response.data || [];
        return { success: true, data: this.diagnostics };
      } catch (error) {
        this.error = error?.response?.data?.error || 'fetch_failed';
        return { success: false, error: this.error };
      } finally {
        this.isLoading = false;
      }
    },

    async fetchDetail(id) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(`diagnostics/${id}/detail/`);
        this.current = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error?.response?.data?.error || 'fetch_failed';
        return { success: false, error: this.error };
      } finally {
        this.isLoading = false;
      }
    },

    async create(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('diagnostics/create/', payload);
        this.current = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error?.response?.data?.error || 'create_failed';
        return { success: false, error: this.error };
      } finally {
        this.isUpdating = false;
      }
    },

    async update(id, payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(
          `diagnostics/${id}/update/`,
          payload
        );
        this.current = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error?.response?.data?.error || 'update_failed';
        return { success: false, error: this.error };
      } finally {
        this.isUpdating = false;
      }
    },

    async remove(id) {
      this.isUpdating = true;
      try {
        await delete_request(`diagnostics/${id}/delete/`);
        this.diagnostics = this.diagnostics.filter((d) => d.id !== id);
        if (this.current?.id === id) this.current = null;
        return { success: true };
      } catch (error) {
        this.error = error?.response?.data?.error || 'delete_failed';
        return { success: false, error: this.error };
      } finally {
        this.isUpdating = false;
      }
    },

    async updateDocument(diagnosticId, docId, payload) {
      this.isUpdating = true;
      try {
        const response = await patch_request(
          `diagnostics/${diagnosticId}/documents/${docId}/update/`,
          payload
        );
        if (this.current?.id === diagnosticId) {
          const docs = this.current.documents || [];
          const idx = docs.findIndex((d) => d.id === docId);
          if (idx >= 0) docs[idx] = { ...docs[idx], ...response.data };
        }
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error?.response?.data?.error || 'update_doc_failed';
        return { success: false, error: this.error };
      } finally {
        this.isUpdating = false;
      }
    },

    async restoreDocument(diagnosticId, docId) {
      this.isUpdating = true;
      try {
        const response = await create_request(
          `diagnostics/${diagnosticId}/documents/${docId}/restore/`,
          {}
        );
        if (this.current?.id === diagnosticId) {
          const docs = this.current.documents || [];
          const idx = docs.findIndex((d) => d.id === docId);
          if (idx >= 0) docs[idx] = { ...docs[idx], ...response.data };
        }
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error?.response?.data?.error || 'restore_failed';
        return { success: false, error: this.error };
      } finally {
        this.isUpdating = false;
      }
    },

    async _postTransition(id, slug, defaultError) {
      this.isUpdating = true;
      try {
        const response = await create_request(`diagnostics/${id}/${slug}/`, {});
        this.current = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error?.response?.data?.error || defaultError;
        return {
          success: false,
          error: this.error,
          message: error?.response?.data?.message,
        };
      } finally {
        this.isUpdating = false;
      }
    },

    markInAnalysis(id) { return this._postTransition(id, 'mark-in-analysis', 'transition_failed'); },
    sendInitial(id)    { return this._postTransition(id, 'send-initial',     'send_failed'); },
    sendFinal(id)      { return this._postTransition(id, 'send-final',       'send_failed'); },

    // ── Attachments (file uploads) ──────────────────────────────────
    async fetchAttachments(id) {
      try {
        const response = await get_request(`diagnostics/${id}/attachments/`);
        if (this.current?.id === id) {
          this.current = { ...this.current, attachments: response.data };
        }
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          error: error?.response?.data?.error || 'fetch_failed',
        };
      }
    },

    async uploadAttachment(id, formData) {
      try {
        const response = await create_request(
          `diagnostics/${id}/attachments/upload/`,
          formData,
        );
        if (this.current?.id === id) {
          const next = [...(this.current.attachments || []), response.data];
          this.current = { ...this.current, attachments: next };
        }
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          error: error?.response?.data?.error || 'upload_failed',
        };
      }
    },

    async deleteAttachment(id, attachmentId) {
      try {
        await delete_request(
          `diagnostics/${id}/attachments/${attachmentId}/delete/`,
        );
        if (this.current?.id === id) {
          const next = (this.current.attachments || []).filter(
            (a) => a.id !== attachmentId,
          );
          this.current = { ...this.current, attachments: next };
        }
        return { success: true };
      } catch (error) {
        return {
          success: false,
          error: error?.response?.data?.error || 'delete_failed',
        };
      }
    },

    async sendAttachmentsToClient(id, payload) {
      try {
        const response = await create_request(
          `diagnostics/${id}/attachments/send/`,
          payload,
        );
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          error: error?.response?.data?.error || 'send_failed',
        };
      }
    },

    // ── Email composer ──────────────────────────────────────────────
    async sendCustomEmail(id, formData) {
      try {
        const response = await create_request(
          `diagnostics/${id}/email/send/`,
          formData,
        );
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          error: error?.response?.data?.error || 'send_failed',
          status: error?.response?.status,
        };
      }
    },

    async fetchEmailDefaults(id) {
      try {
        const response = await get_request(`diagnostics/${id}/email/defaults/`);
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          data: {},
          error: error?.response?.data?.error || 'fetch_failed',
        };
      }
    },

    async fetchEmailHistory(id, page = 1) {
      try {
        const response = await get_request(
          `diagnostics/${id}/email/history/?page=${page}`,
        );
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          data: { results: [], total: 0, page: 1, has_next: false },
          error: error?.response?.data?.error || 'fetch_failed',
        };
      }
    },

    // ── Public ──────────────────────────────────────────────────────
    async fetchPublic(uuid) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(`diagnostics/public/${uuid}/`);
        this.current = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error =
          error?.response?.status === 404 ? 'not_found' : 'fetch_failed';
        return { success: false, error: this.error };
      } finally {
        this.isLoading = false;
      }
    },

    async trackView(uuid) {
      try {
        await create_request(`diagnostics/public/${uuid}/track/`, {});
      } catch (_) {
        // tracking is best-effort
      }
    },

    async respondPublic(uuid, decision) {
      this.isUpdating = true;
      try {
        const response = await create_request(
          `diagnostics/public/${uuid}/respond/`,
          { decision }
        );
        this.current = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error?.response?.data?.error || 'respond_failed';
        return { success: false, error: this.error };
      } finally {
        this.isUpdating = false;
      }
    },
  },
});
