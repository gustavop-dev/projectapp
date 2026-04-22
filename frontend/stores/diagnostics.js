import { defineStore } from 'pinia';
import {
  get_request,
  create_request,
  put_request,
  patch_request,
  delete_request,
} from './services/request_http';
import { isUuid } from '~/utils/slugify';

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

    enabledSections: (state) => {
      const sections = state.current?.sections || [];
      return [...sections]
        .filter((s) => s.is_enabled)
        .sort((a, b) => a.order - b.order);
    },

    sectionsByPhase: (state) => (phase) => {
      const sections = state.current?.sections || [];
      const allowed = new Set([phase, 'both']);
      return [...sections]
        .filter((s) => s.is_enabled && allowed.has(s.visibility))
        .sort((a, b) => a.order - b.order);
    },
  },

  actions: {
    // ── Admin CRUD ──────────────────────────────────────────────────
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

    // ── Sections ────────────────────────────────────────────────────
    async updateSection(diagnosticId, sectionId, payload) {
      this.isUpdating = true;
      try {
        const response = await patch_request(
          `diagnostics/${diagnosticId}/sections/${sectionId}/update/`,
          payload
        );
        if (this.current?.id === diagnosticId) {
          const sections = this.current.sections || [];
          const idx = sections.findIndex((s) => s.id === sectionId);
          if (idx >= 0) sections[idx] = { ...sections[idx], ...response.data };
        }
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error?.response?.data?.error || 'update_section_failed';
        return { success: false, error: this.error };
      } finally {
        this.isUpdating = false;
      }
    },

    async bulkUpdateSections(diagnosticId, sections) {
      this.isUpdating = true;
      try {
        const response = await create_request(
          `diagnostics/${diagnosticId}/sections/bulk-update/`,
          { sections }
        );
        this.current = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error?.response?.data?.error || 'bulk_update_failed';
        return { success: false, error: this.error };
      } finally {
        this.isUpdating = false;
      }
    },

    async resetSection(diagnosticId, sectionId) {
      try {
        const response = await create_request(
          `diagnostics/${diagnosticId}/sections/${sectionId}/reset/`,
          {}
        );
        if (this.current?.id === diagnosticId) {
          const sections = this.current.sections || [];
          const idx = sections.findIndex((s) => s.id === sectionId);
          if (idx >= 0) sections[idx] = { ...sections[idx], ...response.data };
        }
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          error: error?.response?.data?.error || 'reset_failed',
        };
      }
    },

    // ── Activity (change log) ───────────────────────────────────────
    async fetchActivity(id) {
      try {
        const response = await get_request(`diagnostics/${id}/activity/`);
        if (this.current?.id === id) {
          this.current = { ...this.current, change_logs: response.data };
        }
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          error: error?.response?.data?.error || 'fetch_failed',
        };
      }
    },

    async logActivity(id, change_type, description) {
      try {
        const response = await create_request(
          `diagnostics/${id}/activity/create/`,
          { change_type, description }
        );
        if (this.current?.id === id) {
          const next = [response.data, ...(this.current.change_logs || [])];
          this.current = { ...this.current, change_logs: next };
        }
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          error: error?.response?.data?.error || 'log_failed',
        };
      }
    },

    // ── Analytics ───────────────────────────────────────────────────
    async fetchAnalytics(id) {
      try {
        const response = await get_request(`diagnostics/${id}/analytics/`);
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          data: null,
          error: error?.response?.data?.error || 'fetch_failed',
        };
      }
    },

    // ── Status transitions ──────────────────────────────────────────
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

    // ── Acuerdo de Confidencialidad (NDA) ───────────────────────────
    async updateConfidentialityParams(id, params) {
      try {
        const response = await create_request(
          `diagnostics/${id}/confidentiality/params/`,
          { confidentiality_params: params },
        );
        if (this.current?.id === id) {
          const attachment = response.data?.attachment;
          const existingAttachments = this.current.attachments || [];
          let nextAttachments;
          if (attachment) {
            const idx = existingAttachments.findIndex((a) => a.id === attachment.id);
            if (idx >= 0) {
              nextAttachments = [...existingAttachments];
              nextAttachments[idx] = attachment;
            } else {
              nextAttachments = [attachment, ...existingAttachments];
            }
          } else {
            nextAttachments = existingAttachments;
          }
          this.current = {
            ...this.current,
            confidentiality_params: response.data?.confidentiality_params || params,
            attachments: nextAttachments,
          };
        }
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          error: error?.response?.data?.error || 'save_failed',
        };
      }
    },

    async generateConfidentiality(id) {
      try {
        const response = await create_request(
          `diagnostics/${id}/confidentiality/generate/`,
          {},
        );
        if (this.current?.id === id && response.data?.attachment) {
          const attachment = response.data.attachment;
          const existingAttachments = this.current.attachments || [];
          const idx = existingAttachments.findIndex((a) => a.id === attachment.id);
          const nextAttachments = idx >= 0
            ? existingAttachments.map((a, i) => (i === idx ? attachment : a))
            : [attachment, ...existingAttachments];
          this.current = { ...this.current, attachments: nextAttachments };
        }
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          error: error?.response?.data?.error || 'generate_failed',
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
    /**
     * fetchPublic: Retrieve a diagnostic by UUID or slug for client viewing.
     * Detects the identifier format and routes to the correct endpoint.
     */
    async fetchPublic(identifier) {
      this.isLoading = true;
      this.error = null;
      const path = isUuid(identifier)
        ? `diagnostics/public/${identifier}/`
        : `diagnostics/public/by-slug/${identifier}/`;
      try {
        const response = await get_request(path);
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

    async trackView(uuid, session_id = '') {
      try {
        await create_request(`diagnostics/public/${uuid}/track/`, {
          session_id,
        });
      } catch (_) {
        // best-effort
      }
    },

    async trackSectionView(uuid, { session_id, section_type, section_title, time_spent_seconds }) {
      try {
        await create_request(`diagnostics/public/${uuid}/track-section/`, {
          session_id,
          section_type,
          section_title,
          time_spent_seconds,
        });
      } catch (_) {
        // best-effort
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

    // ── Diagnostic Defaults (admin) ─────────────────────────────────
    async fetchDiagnosticDefaults(lang = 'es') {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(
          `diagnostics/defaults/?lang=${encodeURIComponent(lang)}`
        );
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_defaults_failed';
        return { success: false, errors: error?.response?.data };
      } finally {
        this.isLoading = false;
      }
    },

    async saveDiagnosticDefaults(lang, sectionsJson, generalConfig = null) {
      this.isUpdating = true;
      this.error = null;
      try {
        const payload = { language: lang };
        if (Array.isArray(sectionsJson)) {
          payload.sections_json = sectionsJson;
        }
        if (generalConfig && typeof generalConfig === 'object') {
          const passthrough = [
            'payment_initial_pct',
            'payment_final_pct',
            'default_currency',
            'default_investment_amount',
            'default_duration_label',
            'expiration_days',
            'reminder_days',
            'urgency_reminder_days',
            'default_slug_pattern',
          ];
          for (const key of passthrough) {
            if (generalConfig[key] !== undefined && generalConfig[key] !== null) {
              payload[key] = generalConfig[key];
            }
          }
        }
        const response = await put_request('diagnostics/defaults/', payload);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'save_defaults_failed';
        return { success: false, errors: error?.response?.data };
      } finally {
        this.isUpdating = false;
      }
    },

    async resetDiagnosticDefaults(lang = 'es') {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request(
          'diagnostics/defaults/reset/',
          { language: lang }
        );
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'reset_defaults_failed';
        return { success: false, errors: error?.response?.data };
      } finally {
        this.isUpdating = false;
      }
    },
  },
});
