import { ref, watch, onMounted } from 'vue';

const STORAGE_KEY = 'diagnostic-dark-mode';

const isDark = ref(false);

function applyTheme(dark) {
  /* c8 ignore next */
  if (typeof document === 'undefined') return;
  const wrapper = document.querySelector('[data-diagnostic-wrapper]');
  if (wrapper) {
    wrapper.setAttribute('data-theme', dark ? 'dark' : 'light');
  }
}

// Single writer — registered at module load so re-mounting the page
// (SPA navigation away and back) does not stack duplicate watchers.
watch(isDark, (val) => {
  applyTheme(val);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(val));
  } catch (_e) { /* ignore */ }
});

export function useDiagnosticDarkMode() {
  function toggle() {
    isDark.value = !isDark.value;
  }

  onMounted(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored !== null) {
        isDark.value = JSON.parse(stored);
      }
    } catch (_e) { /* ignore */ }
    applyTheme(isDark.value);
  });

  return { isDark, toggle, applyTheme };
}
