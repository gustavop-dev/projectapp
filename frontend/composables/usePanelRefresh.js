import { onBeforeUnmount } from 'vue';
import { usePanelRefreshStore } from '~/stores/panel_refresh';

/**
 * Register a refresh handler for the current panel page.
 *
 * The handler is bound to the global `<PanelRefreshButton>` rendered by
 * the admin layout, and is automatically unregistered when the page
 * unmounts so it never fires on a different route.
 *
 *   usePanelRefresh(loadClients);
 */
export function usePanelRefresh(handler) {
  const store = usePanelRefreshStore();
  store.register(handler);
  onBeforeUnmount(() => {
    store.unregister();
  });
  return store;
}
