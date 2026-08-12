import { computed, ref } from 'vue';

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
 * the list's own order). Options:
 * - sortAccessors  { colKey: recordField | (record) => value } — sort by a
 *     different field than the one displayed (e.g. period_label shown,
 *     period_date sorted), or by a value the row does not carry as a field
 *     (e.g. Cliente shows the linked name and falls back to the snapshot).
 * - sortDefaults   { colKey: 'asc' | 'desc' } — first-click direction per
 *     column ('desc' for dates/money so newest/largest comes first).
 */
export function useTableSort(records, { sortAccessors = {}, sortDefaults = {} } = {}) {
  const sortKey = ref('');
  const sortDir = ref('asc');

  function toggleSort(key) {
    const firstDir = sortDefaults[key] || 'asc';
    if (sortKey.value !== key) {
      sortKey.value = key;
      sortDir.value = firstDir;
    } else if (sortDir.value === firstDir) {
      sortDir.value = firstDir === 'asc' ? 'desc' : 'asc';
    } else {
      sortKey.value = '';
      sortDir.value = 'asc';
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
