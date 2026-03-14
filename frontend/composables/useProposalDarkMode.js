import { ref, watch, onMounted } from 'vue';

const STORAGE_KEY = 'proposal-dark-mode';

// Shared state across components
const isDark = ref(false);

/**
 * Composable for dark mode toggle in the client-facing proposal view.
 * Toggles a `data-theme="dark"` attribute on the proposal wrapper element.
 * Persists preference in localStorage.
 */
export function useProposalDarkMode() {
  function applyTheme(dark) {
    if (typeof document === 'undefined') return;
    const wrapper = document.querySelector('[data-proposal-wrapper]');
    if (wrapper) {
      wrapper.setAttribute('data-theme', dark ? 'dark' : 'light');
    }
  }

  function toggle() {
    isDark.value = !isDark.value;
  }

  watch(isDark, (val) => {
    applyTheme(val);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(val));
    } catch (_e) { /* ignore */ }
  });

  onMounted(() => {
    applyTheme(isDark.value);
  });

  return { isDark, toggle, applyTheme };
}
