import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  EXPLORER_SPACE_IDS,
  explorerTourSteps,
} from '~/config/viewCapabilityCatalog';

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
  const queryTour = initialMode === 'explorer'
    && typeof route.query.tour === 'string'
    && EXPLORER_SPACE_IDS.includes(route.query.tour)
    ? route.query.tour
    : null;
  const queryNode = initialMode === 'explorer' && typeof route.query.node === 'string'
    ? route.query.node
    : null;
  const initialTourSteps = queryTour ? explorerTourSteps(queryTour) : [];
  const initialExplorerNode = queryTour
    ? initialTourSteps.find((node) => node.id === queryNode)?.id || initialTourSteps[0]?.id || null
    : queryNode;

  const viewMode = ref(initialMode);
  const selectedModuleId = ref(
    initialMode === 'map' && typeof route.query.module === 'string' ? route.query.module : null,
  );
  const selectedExplorerNodeId = ref(
    initialExplorerNode,
  );
  const selectedExplorerTourId = ref(queryTour);
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
    if (viewMode.value === 'explorer' && selectedExplorerTourId.value) {
      query.tour = selectedExplorerTourId.value;
    } else {
      delete query.tour;
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
      selectedExplorerTourId.value = null;
    }
    syncQuery();
  });

  watch(selectedModuleId, syncQuery);
  watch(selectedExplorerNodeId, syncQuery);
  watch(selectedExplorerTourId, syncQuery);
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
    const normalizedNodeId = nodeId === 'projectapp' ? null : nodeId;
    if (selectedExplorerTourId.value) {
      const tourStepIds = explorerTourSteps(selectedExplorerTourId.value).map((node) => node.id);
      if (!tourStepIds.includes(normalizedNodeId)) selectedExplorerTourId.value = null;
    }
    selectedExplorerNodeId.value = normalizedNodeId;
  }

  function clearExplorerNode() {
    selectedExplorerTourId.value = null;
    selectedExplorerNodeId.value = null;
  }

  function startExplorerTour(spaceId) {
    if (!EXPLORER_SPACE_IDS.includes(spaceId)) return;
    const firstStep = explorerTourSteps(spaceId)[0];
    if (!firstStep) return;
    selectedExplorerTourId.value = spaceId;
    selectedExplorerNodeId.value = firstStep.id;
  }

  function stopExplorerTour() {
    selectedExplorerTourId.value = null;
  }

  return {
    viewMode,
    selectedModuleId,
    selectedExplorerNodeId,
    selectedExplorerTourId,
    showRelations,
    applyDefaultMode,
    selectModule,
    clearModule,
    selectExplorerNode,
    clearExplorerNode,
    startExplorerTour,
    stopExplorerTour,
  };
}
