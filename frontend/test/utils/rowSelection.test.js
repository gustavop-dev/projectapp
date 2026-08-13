import { reconcileSelection, selectionSummary, toggleKeys } from '../../utils/rowSelection';

describe('toggleKeys', () => {
  it('adds the keys without disturbing what was already selected', () => {
    expect(toggleKeys([1, 2], [5, 7], true)).toEqual([1, 2, 5, 7]);
  });

  it('removes the keys and leaves the rest alone', () => {
    expect(toggleKeys([1, 2, 5], [2, 5], false)).toEqual([1]);
  });

  it('never duplicates a key that is already selected', () => {
    expect(toggleKeys([1, 2], [2, 3], true)).toEqual([1, 2, 3]);
  });

  it('ignores keys that are not selected when unticking', () => {
    expect(toggleKeys([1], [9], false)).toEqual([1]);
  });

  it('returns a new array instead of mutating the current selection', () => {
    const selected = [1];
    const next = toggleKeys(selected, [2], true);

    expect(next).toEqual([1, 2]);
    expect(selected).toEqual([1]);
  });
});

describe('selectionSummary', () => {
  it('reports every key selected as `all`', () => {
    expect(selectionSummary([1, 2], new Set([1, 2, 9])))
      .toEqual({ count: 2, all: true, some: true });
  });

  it('reports a partial hit as `some` but not `all` — the indeterminate case', () => {
    expect(selectionSummary([1, 2, 3], new Set([2])))
      .toEqual({ count: 1, all: false, some: true });
  });

  it('reports nothing selected', () => {
    expect(selectionSummary([1, 2], new Set([9])))
      .toEqual({ count: 0, all: false, some: false });
  });

  // A checkbox over an empty group must not read as ticked.
  it('never calls an empty set of keys `all`', () => {
    expect(selectionSummary([], new Set([1])))
      .toEqual({ count: 0, all: false, some: false });
  });
});

describe('reconcileSelection', () => {
  // The reported bug: one of three selected incomes is deleted and the bulk
  // bar keeps counting it.
  it('drops only the keys that vanished and keeps the order of the rest', () => {
    expect(reconcileSelection([1, 2, 3], [3, 1])).toEqual([1, 3]);
  });

  it('keeps a key that still exists even when the filters hide it', () => {
    // `existingKeys` is the FULL record list, so an off-filter row is present
    // here and must survive — that is the whole distinction the bar draws
    // between "fuera del filtro actual" and "ya no existe".
    expect(reconcileSelection([7], [7, 8, 9])).toEqual([7]);
  });

  it('returns the very same array when nothing vanished', () => {
    const selected = [1, 2];

    // Identity, not equality: a refetch rebuilds the list on every mutation,
    // and re-assigning an equal-but-new array would wake every watcher
    // downstream — including the one that resets the bar's client picker.
    expect(reconcileSelection(selected, [1, 2, 3])).toBe(selected);
  });

  it('empties the selection when every record is gone', () => {
    expect(reconcileSelection([1, 2], [])).toEqual([]);
  });

  it('accepts the existing keys as a Set', () => {
    expect(reconcileSelection([1, 2, 3], new Set([2]))).toEqual([2]);
  });

  it('never mutates the selection it was given', () => {
    const selected = [1, 2];

    expect(reconcileSelection(selected, [1])).toEqual([1]);
    expect(selected).toEqual([1, 2]);
  });
});
