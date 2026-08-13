import { computed, ref, watch } from 'vue';

import { reconcileSelection, toggleKeys } from '~/utils/rowSelection';

/**
 * Multi-row selection that outlives filter, sort and page changes — but never
 * outlives the records themselves.
 *
 * The bug this exists to prevent: the selection used to be a bare `ref([])` in
 * each page, so deleting a selected row left its id in memory. The bulk bar
 * kept announcing "1 seleccionado · 1 fuera del filtro actual" for a record
 * that no longer existed, and only Cancelar could clear it.
 *
 * The reconciliation hangs off the DATA, not off the action that changed it.
 * That is deliberate: several handlers refetch without going through the
 * mutation funnel (hostings' `changeStatus` and `saveInline` call the store
 * directly), so anything bound to that funnel would miss them. Watching the
 * list catches every path — a delete, a bulk edit, the refresh FAB, a row
 * deleted in another session — with no handler having to remember.
 *
 * `watch` runs on the default 'pre' flush and this composable is called from
 * the page, so the prune lands before the page and its children render: a
 * phantom never reaches the DOM, not even for one tick.
 *
 * INVARIANT — `source` must be the FULL store list, never the filtered or
 * paginated rows. Selecting a row, filtering it out and acting on it anyway is
 * a supported flow, so resolving against the visible rows would silently
 * discard legitimate picks. The accounting, proposals and diagnostics list
 * endpoints are unpaginated and their pages fetch them without params, which
 * is what makes the store list the complete set. Parameterising one of those
 * fetches (`{ year }`, say) would break that and turn this prune into data
 * loss.
 *
 * @param {Function|import('vue').Ref} source Getter or ref over the full list.
 * @param {{ key?: string }} [options] `key` is the row's identity field.
 */
export function useRowSelection(source, { key = 'id' } = {}) {
  const selectedIds = ref([]);

  /** O(1) membership for the per-row reads a table does inside its v-for. */
  const selectedSet = computed(() => new Set(selectedIds.value));

  const existingKeys = computed(() => {
    const value = typeof source === 'function' ? source() : source?.value;
    return new Set((Array.isArray(value) ? value : []).map((row) => row[key]));
  });

  // Only what vanished is dropped: three selected minus one deleted leaves
  // two, never zero.
  watch(existingKeys, (keys) => {
    selectedIds.value = reconcileSelection(selectedIds.value, keys);
  });

  function clearSelection() {
    selectedIds.value = [];
  }

  /**
   * Drop specific ids on purpose — the escape hatch for a server that answers
   * "these no longer exist". Routed through `toggleKeys` so the imperative
   * path uses the same arithmetic as the checkboxes.
   */
  function dropIds(ids = []) {
    selectedIds.value = toggleKeys(selectedIds.value, ids, false);
  }

  return { selectedIds, selectedSet, clearSelection, dropIds };
}
