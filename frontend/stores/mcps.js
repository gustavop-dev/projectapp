import { defineStore } from 'pinia';
import {
  get_request,
  create_request,
  patch_request,
  delete_request,
} from './services/request_http';

function errorDetail(error, fallback) {
  const payload = error.response?.data || {};
  const detail = payload.detail || payload.label;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.join(' ');
  return fallback;
}

export const useMcpsStore = defineStore('mcps', {
  state: () => ({
    connectors: [],
    loading: false,
    error: null,
  }),

  getters: {},

  actions: {
    async fetchConnectors() {
      this.loading = true;
      this.error = null;
      try {
        const response = await get_request('mcp-connectors/');
        this.connectors = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error.response?.data?.detail || 'Error al cargar los conectores MCP.';
        return { success: false, error: this.error };
      /* c8 ignore next 3 */
      } finally {
        this.loading = false;
      }
    },

    async generateToken(slug) {
      try {
        const response = await create_request(`mcp-connectors/${slug}/generate-token/`, {});
        await this.fetchConnectors();
        return { success: true, data: response.data };
      } catch (error) {
        const detail = error.response?.data?.detail || 'Error al generar el token.';
        return { success: false, error: detail };
      }
    },

    async createCredential(slug, payload) {
      try {
        const response = await create_request(`mcp-connectors/${slug}/credentials/`, payload);
        await this.fetchConnectors();
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          error: errorDetail(error, 'Error al crear la credencial.'),
        };
      }
    },

    async updateCredential(slug, credentialId, payload) {
      try {
        const response = await patch_request(
          `mcp-connectors/${slug}/credentials/${credentialId}/`,
          payload,
        );
        const index = this.connectors.findIndex((connector) => connector.slug === slug);
        if (index !== -1) this.connectors.splice(index, 1, response.data);
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          error: errorDetail(error, 'Error al actualizar la credencial.'),
        };
      }
    },

    async rotateCredential(slug, credentialId) {
      try {
        const response = await create_request(
          `mcp-connectors/${slug}/credentials/${credentialId}/rotate/`,
          {},
        );
        await this.fetchConnectors();
        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          error: errorDetail(error, 'Error al rotar la credencial.'),
        };
      }
    },

    async revokeCredential(slug, credentialId) {
      try {
        await delete_request(`mcp-connectors/${slug}/credentials/${credentialId}/`);
        await this.fetchConnectors();
        return { success: true };
      } catch (error) {
        return {
          success: false,
          error: errorDetail(error, 'Error al revocar la credencial.'),
        };
      }
    },

    async toggleConnector(slug, isActive) {
      try {
        const response = await patch_request(`mcp-connectors/${slug}/`, { is_active: isActive });
        const index = this.connectors.findIndex((c) => c.slug === slug);
        if (index !== -1) this.connectors.splice(index, 1, response.data);
        return { success: true, data: response.data };
      } catch (error) {
        const detail = error.response?.data?.detail || 'Error al actualizar el conector.';
        return { success: false, error: detail };
      }
    },
  },
});
