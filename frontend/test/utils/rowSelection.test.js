import { selectionSummary, toggleKeys } from '../../utils/rowSelection';

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
