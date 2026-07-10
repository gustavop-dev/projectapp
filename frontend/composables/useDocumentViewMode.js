import { ref, watch } from 'vue';

import { usePersistedRef } from '~/composables/usePersistedRef';

const STORAGE_KEY = 'projectapp-documents-view-mode';
const MODES = ['list', 'grid'];

/**
 * Persisted list/gallery toggle for /panel/documents.
 * Default is 'list' so a clean profile (and every Playwright context)
 * keeps seeing the table the existing E2E specs assert on.
 */
export function useDocumentViewMode() {
  const persisted = usePersistedRef(STORAGE_KEY, 'list');
  const initial = MODES.includes(persisted.ref.value) ? persisted.ref.value : 'list';
  const viewMode = ref(initial);

  // usePersistedRef does not auto-persist; mirror writes explicitly.
  watch(viewMode, (mode) => {
    persisted.write(MODES.includes(mode) ? mode : 'list');
  });

  return { viewMode };
}
