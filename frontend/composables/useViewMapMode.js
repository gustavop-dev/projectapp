import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

// Legacy key from when the last-used mode was persisted locally; the default
// mode now lives in the backend ViewMapSettings singleton.
const LEGACY_STORAGE_KEY = 'projectapp-view-map-mode';
const MODES = ['list', 'map'];

export function useViewMapMode() {
  const route = useRoute();
  const router = useRouter();

  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(LEGACY_STORAGE_KEY);
  }

  const queryMode = MODES.includes(route.query.viewMode) ? route.query.viewMode : null;
  const initialMode = queryMode || 'list';

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
    if (mode !== 'map') {
      selectedModuleId.value = null;
    }
    syncQuery();
  });

  watch(selectedModuleId, syncQuery);

  function applyDefaultMode(mode) {
    if (queryMode || !MODES.includes(mode)) return;
    if (viewMode.value !== initialMode) return;
    viewMode.value = mode;
  }

  function selectModule(moduleId) {
    selectedModuleId.value = moduleId;
  }

  function clearModule() {
    selectedModuleId.value = null;
  }

  return {
    viewMode,
    selectedModuleId,
    applyDefaultMode,
    selectModule,
    clearModule,
  };
}
