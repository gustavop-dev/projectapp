import { computed } from 'vue';
import { usePersistedRef } from './usePersistedRef';

const STORAGE_KEY = 'panel.documents.folderExpanded';

let _state = null;

function _ensureState() {
  if (_state) return _state;
  const persisted = usePersistedRef(STORAGE_KEY, []);
  // Normalize: stored value may be null/undefined → fall back to empty array.
  if (!Array.isArray(persisted.ref.value)) persisted.ref.value = [];
  const set = computed(() => new Set(persisted.ref.value));
  _state = { persisted, set };
  return _state;
}

export function useFolderExpansion() {
  const { persisted, set } = _ensureState();

  function isExpanded(id) {
    if (id == null) return false;
    return set.value.has(id);
  }

  function expand(id) {
    if (id == null) return;
    if (!set.value.has(id)) {
      persisted.ref.value = [...persisted.ref.value, id];
      persisted.write(persisted.ref.value);
    }
  }

  function collapse(id) {
    if (!set.value.has(id)) return;
    persisted.ref.value = persisted.ref.value.filter((x) => x !== id);
    persisted.write(persisted.ref.value);
  }

  function toggle(id) {
    if (set.value.has(id)) collapse(id);
    else expand(id);
  }

  function expandPath(ids) {
    if (!Array.isArray(ids) || ids.length === 0) return;
    const next = new Set(persisted.ref.value);
    let changed = false;
    for (const id of ids) {
      if (id != null && !next.has(id)) {
        next.add(id);
        changed = true;
      }
    }
    if (changed) {
      persisted.ref.value = [...next];
      persisted.write(persisted.ref.value);
    }
  }

  return {
    expanded: persisted.ref,
    isExpanded,
    expand,
    collapse,
    toggle,
    expandPath,
  };
}

/* c8 ignore next 3 */
export function _resetFolderExpansionForTesting() {
  _state = null;
}
