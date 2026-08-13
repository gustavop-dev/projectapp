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
