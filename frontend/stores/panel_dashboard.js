import { defineStore } from 'pinia';
import { get_request } from './services/request_http';

export const usePanelDashboardStore = defineStore('panel_dashboard', {
  /**
   * State of the global panel dashboard store.
   *
   * Properties:
   * - summary (Object|null): consolidated payload from /api/panel/dashboard/
   *   with finance (null for non-superusers), proposals, operations and
   *   the cross-module attention list.
   * - loading (Boolean): fetch in flight.
   * - error (Boolean): last fetch failed.
   */
  state: () => ({
    summary: null,
    loading: false,
    error: false,
  }),

  getters: {
    finance: (state) => state.summary?.finance ?? null,
    proposals: (state) => state.summary?.proposals ?? null,
    operations: (state) => state.summary?.operations ?? null,
    attention: (state) => state.summary?.attention ?? [],
    hasFinance: (state) => Boolean(state.summary?.finance),
  },

  actions: {
    /**
     * Fetch the consolidated dashboard summary.
     * @returns {Promise<{success: boolean}>}
     */
    async fetchSummary() {
      this.loading = true;
      this.error = false;
      try {
        const response = await get_request('panel/dashboard/');
        this.summary = response.data;
        return { success: true };
      } catch (error) {
        this.error = true;
        console.error('Error fetching panel dashboard:', error);
        return { success: false };
      } finally {
        this.loading = false;
      }
    },
  },
});
