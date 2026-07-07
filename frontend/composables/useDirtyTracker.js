/**
 * Factory-scoped tracker for "unsaved changes" flags keyed by an id
 * (e.g. proposal section ids). The owning page derives guards
 * (beforeunload, route-leave, collapse confirmations) from `hasDirty`.
 *
 * Phase-2 autosave seam: a future `useAutosave(tracker, { debounceMs })`
 * can watch `dirtyIds` and call each editor's exposed `save()` — see
 * SectionEditor's `defineExpose({ save, isDirty })`.
 */
import { computed, ref } from 'vue';

export function useDirtyTracker() {
  const dirtyIds = ref(new Set());

  function setDirty(id, dirty) {
    const next = new Set(dirtyIds.value);
    if (dirty) {
      next.add(id);
    } else {
      next.delete(id);
    }
    dirtyIds.value = next;
  }

  function isDirty(id) {
    return dirtyIds.value.has(id);
  }

  const hasDirty = computed(() => dirtyIds.value.size > 0);

  function clear() {
    dirtyIds.value = new Set();
  }

  return { dirtyIds, hasDirty, isDirty, setDirty, clear };
}
