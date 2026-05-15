/**
 * Tests for the useFolderExpansion composable.
 *
 * The composable is a module-level singleton backed by usePersistedRef
 * (localStorage). All consumers see the same expanded set so the sidebar,
 * manager, and move modal can stay in sync without prop-drilling.
 */

let useFolderExpansion;
let _resetFolderExpansionForTesting;

const STORAGE_KEY = 'panel.documents.folderExpanded';

beforeEach(() => {
  localStorage.clear();
  jest.resetModules();
  jest.isolateModules(() => {
    const mod = require('../../composables/useFolderExpansion');
    useFolderExpansion = mod.useFolderExpansion;
    _resetFolderExpansionForTesting = mod._resetFolderExpansionForTesting;
  });
});

afterEach(() => {
  localStorage.clear();
  if (_resetFolderExpansionForTesting) _resetFolderExpansionForTesting();
});

describe('useFolderExpansion', () => {
  it('starts empty when no localStorage entry exists', () => {
    const { expanded, isExpanded } = useFolderExpansion();
    expect(expanded.value).toEqual([]);
    expect(isExpanded(1)).toBe(false);
  });

  it('expand(id) adds id and persists to localStorage', () => {
    const { expand, isExpanded } = useFolderExpansion();
    expand(5);
    expect(isExpanded(5)).toBe(true);
    expect(JSON.parse(localStorage.getItem(STORAGE_KEY))).toEqual([5]);
  });

  it('expand(id) is idempotent — does not duplicate', () => {
    const { expand, expanded } = useFolderExpansion();
    expand(5);
    expand(5);
    expect(expanded.value).toEqual([5]);
  });

  it('expand(null) is a no-op', () => {
    const { expand, expanded } = useFolderExpansion();
    expand(null);
    expand(undefined);
    expect(expanded.value).toEqual([]);
  });

  it('collapse(id) removes id and persists', () => {
    const { expand, collapse, isExpanded } = useFolderExpansion();
    expand(1);
    expand(2);
    collapse(1);
    expect(isExpanded(1)).toBe(false);
    expect(isExpanded(2)).toBe(true);
    expect(JSON.parse(localStorage.getItem(STORAGE_KEY))).toEqual([2]);
  });

  it('collapse(id) for an unexpanded folder is a no-op', () => {
    const { collapse, expanded } = useFolderExpansion();
    collapse(99);
    expect(expanded.value).toEqual([]);
  });

  it('toggle(id) flips expanded state', () => {
    const { toggle, isExpanded } = useFolderExpansion();
    toggle(7);
    expect(isExpanded(7)).toBe(true);
    toggle(7);
    expect(isExpanded(7)).toBe(false);
  });

  it('expandPath(ids) adds many at once and persists once', () => {
    const { expandPath, expanded } = useFolderExpansion();
    expandPath([1, 2, 3]);
    expect(new Set(expanded.value)).toEqual(new Set([1, 2, 3]));
    expect(JSON.parse(localStorage.getItem(STORAGE_KEY))).toEqual([1, 2, 3]);
  });

  it('expandPath skips ids already expanded (no duplicates)', () => {
    const { expand, expandPath, expanded } = useFolderExpansion();
    expand(1);
    expandPath([1, 2]);
    expect(new Set(expanded.value)).toEqual(new Set([1, 2]));
  });

  it('expandPath with empty array is a no-op', () => {
    const { expandPath, expanded } = useFolderExpansion();
    expandPath([]);
    expect(expanded.value).toEqual([]);
  });

  it('shares state across invocations (singleton)', () => {
    const first = useFolderExpansion();
    first.expand(42);
    const second = useFolderExpansion();
    expect(second.isExpanded(42)).toBe(true);
  });

  it('rehydrates from localStorage on first invocation', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([10, 20]));
    // Force a fresh module load so the singleton initializes from storage.
    jest.resetModules();
    jest.isolateModules(() => {
      const mod = require('../../composables/useFolderExpansion');
      const { expanded, isExpanded } = mod.useFolderExpansion();
      expect(expanded.value).toEqual([10, 20]);
      expect(isExpanded(10)).toBe(true);
    });
  });

  it('normalizes a non-array stored value to empty', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(null));
    jest.resetModules();
    jest.isolateModules(() => {
      const mod = require('../../composables/useFolderExpansion');
      const { expanded } = mod.useFolderExpansion();
      expect(expanded.value).toEqual([]);
    });
  });
});
