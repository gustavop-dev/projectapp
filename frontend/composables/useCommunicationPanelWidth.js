import { computed, ref } from 'vue';

import { usePersistedRef } from '~/composables/usePersistedRef';

export const COMMUNICATION_PANEL_MIN = 240;
export const COMMUNICATION_PANEL_MAX = 400;
export const COMMUNICATION_PANEL_DEFAULT = 288;
export const COMMUNICATION_PANEL_KEY = 'projectapp-communications-navigation-width';

function clamp(value) {
  const width = Number(value);
  if (!Number.isFinite(width)) return COMMUNICATION_PANEL_DEFAULT;
  return Math.min(COMMUNICATION_PANEL_MAX, Math.max(COMMUNICATION_PANEL_MIN, width));
}

export function useCommunicationPanelWidth(containerRef) {
  const { ref: width, write, remove } = usePersistedRef(
    COMMUNICATION_PANEL_KEY,
    COMMUNICATION_PANEL_DEFAULT,
  );
  width.value = clamp(width.value);
  const dragging = ref(false);
  const gridStyle = computed(() => ({ '--communications-panel-w': `${width.value}px` }));

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
    write(width.value);
  }

  function resizeWidth(value) {
    width.value = clamp(value);
    write(width.value);
  }

  function resetWidth() {
    width.value = COMMUNICATION_PANEL_DEFAULT;
    remove();
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
  };
}
