import { ref, watch, onMounted } from 'vue';

const STORAGE_KEY = 'projectapp-dark-mode';

// Shared state across components
const isDark = ref(false);

/**
 * Composable for dark mode toggle in the admin panel.
 * Persists preference in localStorage and applies `dark` class to <html>.
 */
export function useDarkMode() {
  function applyTheme(dark) {
    if (typeof document === 'undefined') return;
    const html = document.documentElement;
    if (dark) {
      html.classList.add('dark');
    } else {
      html.classList.remove('dark');
    }
  }

  function toggle() {
    isDark.value = !isDark.value;
  }

  // Persist to localStorage on change
  watch(isDark, (val) => {
    applyTheme(val);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(val));
    } catch (_e) { /* ignore */ }
  });

  onMounted(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored !== null) {
        isDark.value = JSON.parse(stored);
      } else {
        // Respect system preference
        isDark.value = window.matchMedia?.('(prefers-color-scheme: dark)').matches || false;
      }
    } catch (_e) { /* ignore */ }
    applyTheme(isDark.value);
  });

  return { isDark, toggle };
}
