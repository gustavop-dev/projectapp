import { computed, ref } from 'vue';

import { usePersistedRef } from '~/composables/usePersistedRef';

function compareValues(a, b, read) {
  const left = read(a);
  const right = read(b);
  const leftNumber = Number(left);
  const rightNumber = Number(right);
  if (Number.isFinite(leftNumber) && Number.isFinite(rightNumber)) {
    return leftNumber - rightNumber;
  }
  // ISO dates and plain text both sort correctly with localeCompare.
  return String(left ?? '').localeCompare(String(right ?? ''), 'es');
}

/**
 * Client-side column sorting over a reactive list of rows.
 *
 * Each click on a column cycles: first direction → opposite → off (back to
 * the list's own order). A baseline sort changes that cycle to first direction
 * → opposite → baseline; clicking the baseline column itself toggles only its
 * two directions. Options:
 * - sortAccessors  { colKey: recordField | (record) => value } — sort by a
 *     different field than the one displayed (e.g. period_label shown,
 *     period_date sorted), or by a value the row does not carry as a field
 *     (e.g. Cliente shows the linked name and falls back to the snapshot).
 * - sortDefaults   { colKey: 'asc' | 'desc' } — first-click direction per
 *     column ('desc' for dates/money so newest/largest comes first).
 * - baselineSort   { key, dir } — active on first render and restored after
 *     another column completes its cycle.
 * - storageKey     localStorage key for remembering the active sort.
 * - allowedKeys    accepted keys for stored state; invalid state falls back
 *     to baselineSort instead of activating an unknown column.
 */
export function useTableSort(records, {
  sortAccessors = {},
  sortDefaults = {},
  baselineSort = null,
  storageKey = '',
  allowedKeys = [],
} = {}) {
  const allowedSet = new Set(allowedKeys);
  const isAllowedKey = (key) => !allowedSet.size || allowedSet.has(key);
  const normalizeSort = (sort) => {
    if (!sort || typeof sort.key !== 'string' || !isAllowedKey(sort.key)) return null;
    if (!['asc', 'desc'].includes(sort.dir)) return null;
    return { key: sort.key, dir: sort.dir };
  };

  const baseline = normalizeSort(baselineSort);
  const persisted = storageKey ? usePersistedRef(storageKey, null) : null;
  const initial = normalizeSort(persisted?.ref.value) || baseline;
  const sortKey = ref(initial?.key || '');
  const sortDir = ref(initial?.dir || 'asc');

  function setSort(sort) {
    sortKey.value = sort?.key || '';
    sortDir.value = sort?.dir || 'asc';
    if (!persisted) return;
    if (sort?.key) persisted.write(sort);
    else persisted.remove();
  }

  function toggleSort(key) {
    if (!isAllowedKey(key)) return;

    if (baseline?.key === key) {
      const dir = sortKey.value === key && sortDir.value === baseline.dir
        ? (baseline.dir === 'asc' ? 'desc' : 'asc')
        : baseline.dir;
      setSort({ key, dir });
      return;
    }

    const firstDir = sortDefaults[key] || 'asc';
    if (sortKey.value !== key) {
      setSort({ key, dir: firstDir });
    } else if (sortDir.value === firstDir) {
      setSort({ key, dir: firstDir === 'asc' ? 'desc' : 'asc' });
    } else {
      setSort(baseline);
    }
  }

  const sortedRecords = computed(() => {
    if (!sortKey.value) return records.value;
    const accessor = sortAccessors[sortKey.value] || sortKey.value;
    const read = typeof accessor === 'function'
      ? accessor
      : (row) => row?.[accessor];
    const direction = sortDir.value === 'desc' ? -1 : 1;
    return [...records.value].sort(
      (a, b) => direction * compareValues(a, b, read),
    );
  });

  return { sortKey, sortDir, toggleSort, sortedRecords };
}
