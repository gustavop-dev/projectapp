import { defineStore } from 'pinia';
import {
  get_request,
  create_request,
  put_request,
  patch_request,
  delete_request,
} from './services/request_http';
import { normalizeApiError } from './services/normalize_api_error';
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
    /**
     * Build the standard failure result: `{ success, errors (raw payload),
     * message, code, hint, fieldErrors, status, error (alias of message) }`.
     * Callers that surface global state also assign `this.error`.
     */
    _fail(error, fallback, extra = {}) {
      const norm = normalizeApiError(error, fallback);
      return {
        success: false,
        ...extra,
        errors: error?.response?.data ?? null,
        ...norm,
        error: norm.message,
      };
    },

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
        const failure = this._fail(error, 'No se pudieron cargar los diagnósticos.');
        this.error = failure.message;
        return failure;
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
        const failure = this._fail(error, 'No se pudo cargar el diagnóstico.');
        this.error = failure.message;
        return failure;
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
        const failure = this._fail(error, 'No se pudo crear el diagnóstico.');
        this.error = failure.message;
        return failure;
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
        const failure = this._fail(error, 'No se pudo guardar el diagnóstico.');
        this.error = failure.message;
        return failure;
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
        const failure = this._fail(error, 'No se pudo eliminar el diagnóstico.');
        this.error = failure.message;
        return failure;
      } finally {
        this.isUpdating = false;
      }
    },

    async bulkAction(ids, action) {
      this.isUpdating = true;
      try {
        const response = await create_request('diagnostics/bulk-action/', { ids, action });
        if (action === 'delete') {
          const removed = new Set(ids);
          this.diagnostics = this.diagnostics.filter((d) => !removed.has(d.id));
          if (this.current && removed.has(this.current.id)) this.current = null;
        }
        return { success: true, data: response.data };
      } catch (error) {
        const failure = this._fail(error, 'No se pudo aplicar la acción en lote.');
        this.error = failure.message;
        return failure;
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
        const failure = this._fail(error, 'No se pudo guardar la sección.');
        this.error = failure.message;
        return failure;
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
        const failure = this._fail(error, 'No se pudieron guardar las secciones.');
        this.error = failure.message;
        return failure;
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
        return this._fail(error, 'No se pudo restaurar la sección.');
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
        return this._fail(error, 'No se pudo cargar la actividad.');
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
        return this._fail(error, 'No se pudo registrar la actividad.');
      }
    },

    // ── Scorecard ───────────────────────────────────────────────────
    async fetchScorecard(id) {
      try {
        const response = await get_request(`diagnostics/${id}/scorecard/`);
        return { success: true, data: response.data };
      } catch (error) {
        return this._fail(error, 'No se pudo cargar el scorecard.', { data: null });
      }
    },

    // ── Analytics ───────────────────────────────────────────────────
    async fetchAnalytics(id) {
      try {
        const response = await get_request(`diagnostics/${id}/analytics/`);
        return { success: true, data: response.data };
      } catch (error) {
        return this._fail(error, 'No se pudo cargar la analítica.', { data: null });
      }
    },

    // ── Status transitions ──────────────────────────────────────────
    async _postTransition(id, slug, fallbackMessage) {
      this.isUpdating = true;
      try {
        const response = await create_request(`diagnostics/${id}/${slug}/`, {});
        this.current = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        const failure = this._fail(error, fallbackMessage);
        this.error = failure.message;
        return failure;
      } finally {
        this.isUpdating = false;
      }
    },

    markInAnalysis(id) { return this._postTransition(id, 'mark-in-analysis', 'No se pudo cambiar el estado.'); },
    sendInitial(id)    { return this._postTransition(id, 'send-initial',     'No se pudo enviar el diagnóstico.'); },
    sendFinal(id)      { return this._postTransition(id, 'send-final',       'No se pudo enviar el diagnóstico.'); },

    // ── Attachments (file uploads) ──────────────────────────────────
    async fetchAttachments(id) {
      try {
        const response = await get_request(`diagnostics/${id}/attachments/`);
        if (this.current?.id === id) {
          this.current = { ...this.current, attachments: response.data };
        }
        return { success: true, data: response.data };
      } catch (error) {
        return this._fail(error, 'No se pudieron cargar los documentos.');
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
        return this._fail(error, 'No se pudo subir el documento.');
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
        return this._fail(error, 'No se pudo eliminar el documento.');
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
        return this._fail(error, 'No se pudieron enviar los documentos.');
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
        return this._fail(error, 'No se pudieron guardar los parámetros.');
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
        return this._fail(error, 'No se pudo generar el acuerdo.');
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
        return this._fail(error, 'No se pudo enviar el correo.');
      }
    },

    async fetchEmailDefaults(id) {
      try {
        const response = await get_request(`diagnostics/${id}/email/defaults/`);
        return { success: true, data: response.data };
      } catch (error) {
        return this._fail(error, 'No se pudieron cargar los valores del correo.', { data: {} });
      }
    },

    async fetchEmailHistory(id, page = 1) {
      try {
        const response = await get_request(
          `diagnostics/${id}/email/history/?page=${page}`,
        );
        return { success: true, data: response.data };
      } catch (error) {
        return this._fail(error, 'No se pudo cargar el historial de correos.', {
          data: { results: [], total: 0, page: 1, has_next: false },
        });
      }
    },

    // ── Public ──────────────────────────────────────────────────────
    /**
     * fetchPublic: Retrieve a diagnostic by UUID or slug for client viewing.
     * Detects the identifier format and routes to the correct endpoint.
     * Keeps the 'not_found' sentinel consumed by the public page.
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

    async trackSectionView(uuid, { session_id, section_type, section_title, time_spent_seconds, entered_at }) {
      try {
        await create_request(`diagnostics/public/${uuid}/track-section/`, {
          session_id,
          section_type,
          section_title,
          time_spent_seconds,
          entered_at,
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
        const failure = this._fail(error, 'No se pudo registrar tu respuesta.');
        this.error = failure.message;
        return failure;
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
        const failure = this._fail(error, 'No se pudieron cargar los valores por defecto.');
        this.error = failure.message;
        return failure;
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
        const failure = this._fail(error, 'No se pudieron guardar los valores por defecto.');
        this.error = failure.message;
        return failure;
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
        const failure = this._fail(error, 'No se pudieron restablecer los valores por defecto.');
        this.error = failure.message;
        return failure;
      } finally {
        this.isUpdating = false;
      }
    },
  },
});
