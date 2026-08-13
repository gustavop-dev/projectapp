/**
 * Row-selection arithmetic shared by the accounting tables.
 *
 * Both AccountingTable (a real <table>, selection scoped to the current page)
 * and IncomeGroupedTable (an ARIA grid, selection scoped to a client group or
 * to the whole filtered set) answer the same two questions: what is the next
 * selection after toggling a set of keys, and is a given set fully, partly or
 * not selected. Written once here so the two cannot drift.
 */

/**
 * Next selection after ticking (or unticking) `keys`.
 *
 * Order is preserved and duplicates are impossible — the caller can hand the
 * result straight to `update:selected`.
 */
export function toggleKeys(selected = [], keys = [], checked = true) {
  const next = new Set(selected);
  keys.forEach((key) => {
    if (checked) next.add(key);
    else next.delete(key);
  });
  return [...next];
}

/**
 * How much of `keys` the selection covers: `{ count, all, some }`.
 *
 * `all` drives the checkbox's checked state and `some && !all` its
 * indeterminate one; `count` is what a collapsed group header reports. An
 * empty `keys` is never "all": a checkbox over nothing must not read as ticked.
 */
export function selectionSummary(keys = [], selectedSet = new Set()) {
  const count = keys.reduce((total, key) => total + (selectedSet.has(key) ? 1 : 0), 0);
  return { count, all: keys.length > 0 && count === keys.length, some: count > 0 };
}

/**
 * The selection minus the keys that no longer exist.
 *
 * The parameter is `existingKeys`, never the filtered ones, and that word is
 * load-bearing: a selection legitimately outlives filter and page changes, so
 * resolving it against what the filters show would discard rows the operator
 * picked on purpose. Only "this record is gone" may drop a key.
 *
 * Returns the SAME array when nothing was dropped. `ref.value = sameRef` is a
 * no-op for Vue, so a refetch that rebuilds the list without losing any id
 * writes nothing and wakes no downstream effect.
 */
export function reconcileSelection(selected = [], existingKeys = []) {
  const existing = existingKeys instanceof Set ? existingKeys : new Set(existingKeys);
  const next = selected.filter((key) => existing.has(key));
  return next.length === selected.length ? selected : next;
}
