import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { usePersistedRef } from '~/composables/usePersistedRef';

const STORAGE_KEY = 'projectapp-view-map-mode';
const MODES = ['list', 'map'];

export function useViewMapMode() {
  const route = useRoute();
  const router = useRouter();

  const persisted = usePersistedRef(STORAGE_KEY, 'list');

  const queryMode = MODES.includes(route.query.viewMode) ? route.query.viewMode : null;
  const initialMode = queryMode || (MODES.includes(persisted.ref.value) ? persisted.ref.value : 'list');

  const viewMode = ref(initialMode);
  const selectedModuleId = ref(
    initialMode === 'map' && typeof route.query.module === 'string' ? route.query.module : null,
  );

  function syncQuery() {
    const query = { ...route.query };
    if (viewMode.value === 'map') {
      query.viewMode = 'map';
    } else {
      delete query.viewMode;
    }
    if (viewMode.value === 'map' && selectedModuleId.value) {
      query.module = selectedModuleId.value;
    } else {
      delete query.module;
    }
    router.replace({ query });
  }

  watch(viewMode, (mode) => {
    persisted.write(mode);
    if (mode !== 'map') {
      selectedModuleId.value = null;
    }
    syncQuery();
  });

  watch(selectedModuleId, syncQuery);

  function selectModule(moduleId) {
    selectedModuleId.value = moduleId;
  }

  function clearModule() {
    selectedModuleId.value = null;
  }

  return {
    viewMode,
    selectedModuleId,
    selectModule,
    clearModule,
  };
}
