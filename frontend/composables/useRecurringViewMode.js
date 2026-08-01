import { ref, watch } from 'vue';

import { usePersistedRef } from '~/composables/usePersistedRef';

const STORAGE_KEY = 'projectapp-recurring-view-mode';
const MODES = ['grouped', 'table'];

/**
 * Persisted grouped/classic toggle for /panel/accounting/recurring.
 *
 * Default is 'grouped': the categorized view with monthly subtotals is the
 * point of the tab. 'table' keeps the sortable, paginated table for the times
 * you want to scan a single column across every category.
 */
export function useRecurringViewMode() {
  const persisted = usePersistedRef(STORAGE_KEY, 'grouped');
  const initial = MODES.includes(persisted.ref.value) ? persisted.ref.value : 'grouped';
  const viewMode = ref(initial);

  // usePersistedRef does not auto-persist; mirror writes explicitly.
  watch(viewMode, (mode) => {
    persisted.write(MODES.includes(mode) ? mode : 'grouped');
  });

  return { viewMode };
}
