import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

// Legacy key from when the last-used mode was persisted locally; the default
// mode now lives in the backend ViewMapSettings singleton.
const LEGACY_STORAGE_KEY = 'projectapp-view-map-mode';
export const VIEW_MAP_MODES = Object.freeze(['list', 'map', 'explorer']);

export function useViewMapMode() {
  const route = useRoute();
  const router = useRouter();

  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(LEGACY_STORAGE_KEY);
  }

  const queryMode = VIEW_MAP_MODES.includes(route.query.viewMode) ? route.query.viewMode : null;
  const initialMode = queryMode || 'list';

  const viewMode = ref(initialMode);
  const selectedModuleId = ref(
    initialMode === 'map' && typeof route.query.module === 'string' ? route.query.module : null,
  );
  const selectedExplorerNodeId = ref(
    initialMode === 'explorer' && typeof route.query.node === 'string' ? route.query.node : null,
  );
  const showRelations = ref(route.query.relations !== '0');

  function syncQuery() {
    const query = { ...route.query };
    if (viewMode.value === 'map' || viewMode.value === 'explorer') {
      query.viewMode = viewMode.value;
    } else {
      delete query.viewMode;
    }
    if (viewMode.value === 'map' && selectedModuleId.value) {
      query.module = selectedModuleId.value;
    } else {
      delete query.module;
    }
    if (viewMode.value === 'explorer' && selectedExplorerNodeId.value) {
      query.node = selectedExplorerNodeId.value;
    } else {
      delete query.node;
    }
    if (viewMode.value === 'explorer' && !showRelations.value) {
      query.relations = '0';
    } else {
      delete query.relations;
    }
    router.replace({ query });
  }

  watch(viewMode, (mode) => {
    if (mode !== 'map') {
      selectedModuleId.value = null;
    }
    if (mode !== 'explorer') {
      selectedExplorerNodeId.value = null;
    }
    syncQuery();
  });

  watch(selectedModuleId, syncQuery);
  watch(selectedExplorerNodeId, syncQuery);
  watch(showRelations, syncQuery);

  function applyDefaultMode(mode) {
    if (queryMode || !VIEW_MAP_MODES.includes(mode)) return;
    if (viewMode.value !== initialMode) return;
    viewMode.value = mode;
  }

  function selectModule(moduleId) {
    selectedModuleId.value = moduleId;
  }

  function clearModule() {
    selectedModuleId.value = null;
  }

  function selectExplorerNode(nodeId) {
    selectedExplorerNodeId.value = nodeId === 'projectapp' ? null : nodeId;
  }

  function clearExplorerNode() {
    selectedExplorerNodeId.value = null;
  }

  return {
    viewMode,
    selectedModuleId,
    selectedExplorerNodeId,
    showRelations,
    applyDefaultMode,
    selectModule,
    clearModule,
    selectExplorerNode,
    clearExplorerNode,
  };
}
