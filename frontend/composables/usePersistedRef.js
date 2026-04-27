import { ref } from 'vue';

export function usePersistedRef(key, defaultValue = null, opts = {}) {
  const { serialize = JSON.stringify, deserialize = JSON.parse } = opts;

  function read() {
    /* c8 ignore next */
    if (typeof window === 'undefined') return null;
    try {
      const stored = window.localStorage.getItem(key);
      if (stored === null) return null;
      return deserialize(stored);
    } catch (_e) {
      return null;
    }
  }

  function write(v) {
    /* c8 ignore next */
    if (typeof window === 'undefined') return;
    try {
      window.localStorage.setItem(key, serialize(v));
    } catch (_e) { /* ignore */ }
  }

  function remove() {
    /* c8 ignore next */
    if (typeof window === 'undefined') return;
    try {
      window.localStorage.removeItem(key);
    } catch (_e) { /* ignore */ }
  }

  const initial = read();
  const r = ref(initial !== null ? initial : defaultValue);

  return { ref: r, read, write, remove };
}
