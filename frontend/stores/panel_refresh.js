import { defineStore } from 'pinia';

/**
 * Global refresh coordinator for the admin panel.
 *
 * Each panel page registers a `handler` (its own data refresh function);
 * the `<PanelRefreshButton>` rendered once in the admin layout calls
 * `trigger()` to run the active handler and toggles `isRefreshing`.
 */
export const usePanelRefreshStore = defineStore('panelRefresh', {
  state: () => ({
    handler: null,
    isRefreshing: false,
  }),

  getters: {
    hasHandler: (state) => typeof state.handler === 'function',
  },

  actions: {
    register(fn) {
      this.handler = typeof fn === 'function' ? fn : null;
    },
    unregister() {
      this.handler = null;
      this.isRefreshing = false;
    },
    async trigger() {
      if (!this.handler || this.isRefreshing) return;
      this.isRefreshing = true;
      try {
        await this.handler();
      } finally {
        this.isRefreshing = false;
      }
    },
  },
});
