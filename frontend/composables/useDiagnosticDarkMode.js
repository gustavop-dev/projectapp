import { ref } from 'vue';

export const DIAGNOSTIC_THEME_STORAGE_KEY = 'diagnostic_theme';
const STORAGE_KEY = DIAGNOSTIC_THEME_STORAGE_KEY;
const LEGACY_STORAGE_KEY = 'diagnostic-dark-mode';

const isDark = ref(false);

function readStoredPreference() {
  /* c8 ignore next */
  if (typeof window === 'undefined') return null;
  try {
    const current = localStorage.getItem(STORAGE_KEY);
    if (current === 'dark') return true;
    if (current === 'light') return false;

    const legacy = localStorage.getItem(LEGACY_STORAGE_KEY);
    if (legacy !== null) {
      const parsed = JSON.parse(legacy) === true;
      localStorage.setItem(STORAGE_KEY, parsed ? 'dark' : 'light');
      localStorage.removeItem(LEGACY_STORAGE_KEY);
      return parsed;
    }
  } catch (_e) { /* ignore */ }
  return null;
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
    const stored = readStoredPreference();
    isDark.value = stored !== null ? stored : prefersSystemDark();
  }

  function toggle() {
    isDark.value = !isDark.value;
    /* c8 ignore next */
    if (typeof window === 'undefined') return;
    try {
      localStorage.setItem(STORAGE_KEY, isDark.value ? 'dark' : 'light');
    } catch (_e) { /* ignore */ }
  }

  return { isDark, toggle, hydrate };
}
