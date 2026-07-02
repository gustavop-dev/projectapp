import { defineStore } from 'pinia';
import { get_request, create_request, patch_request } from './services/request_http';

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
