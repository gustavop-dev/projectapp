import { ref } from 'vue';
import { usePersistedRef } from './usePersistedRef';

export const DIAGNOSTIC_THEME_STORAGE_KEY = 'diagnostic_theme';
const STORAGE_KEY = DIAGNOSTIC_THEME_STORAGE_KEY;
const LEGACY_STORAGE_KEY = 'diagnostic-dark-mode';

const persisted = usePersistedRef(STORAGE_KEY, null, {
  serialize: (v) => (v ? 'dark' : 'light'),
  deserialize: (s) => (s === 'dark' ? true : s === 'light' ? false : null),
});
const legacy = usePersistedRef(LEGACY_STORAGE_KEY);

const isDark = ref(false);

function migrateLegacy() {
  const v = legacy.read();
  if (v === null) return null;
  const parsed = v === true;
  persisted.write(parsed);
  legacy.remove();
  return parsed;
}

function prefersSystemDark() {
  /* c8 ignore next */
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false;
  try {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  } catch (_e) {
    return false;
  }
}

export function useDiagnosticDarkMode() {
  function hydrate() {
    const stored = persisted.read();
    if (stored !== null) {
      isDark.value = stored;
      return;
    }
    const migrated = migrateLegacy();
    if (migrated !== null) {
      isDark.value = migrated;
      return;
    }
    isDark.value = prefersSystemDark();
  }

  function toggle() {
    isDark.value = !isDark.value;
    persisted.write(isDark.value);
  }

  return { isDark, toggle, hydrate };
}
