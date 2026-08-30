import { computed, ref } from 'vue';

import {
  COMMUNICATION_PANEL_STORAGE_KEY,
  clampCommunicationPanelWidth,
} from '~/constants/communicationPreferences';

export const COMMUNICATION_PANEL_MIN = 240;
export const COMMUNICATION_PANEL_MAX = 400;
export const COMMUNICATION_PANEL_DEFAULT = 288;
export const COMMUNICATION_PANEL_KEY = COMMUNICATION_PANEL_STORAGE_KEY;

function clamp(value) {
  return clampCommunicationPanelWidth(value);
}

export function useCommunicationPanelWidth(containerRef, options = {}) {
  const width = ref(clamp(options.initialWidth));
  const dragging = ref(false);
  const gridStyle = computed(() => ({ '--communications-panel-w': `${width.value}px` }));

  function persist() {
    if (typeof options.onPersist === 'function') options.onPersist(width.value);
  }

  function onHandleDown() {
    dragging.value = true;
  }

  function onHandleMove(event) {
    if (!dragging.value || !containerRef.value) return;
    const rect = containerRef.value.getBoundingClientRect();
    if (!rect.width) return;
    width.value = clamp(event.clientX - rect.left);
  }

  function onHandleUp() {
    if (!dragging.value) return;
    dragging.value = false;
    persist();
  }

  function resizeWidth(value) {
    width.value = clamp(value);
    persist();
  }

  function resetWidth() {
    width.value = COMMUNICATION_PANEL_DEFAULT;
    persist();
  }

  function hydrateWidth(value) {
    if (!dragging.value) width.value = clamp(value);
  }

  return {
    width,
    dragging,
    gridStyle,
    onHandleDown,
    onHandleMove,
    onHandleUp,
    resizeWidth,
    resetWidth,
    hydrateWidth,
  };
}
