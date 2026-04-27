import { watch, onMounted } from 'vue';
import { usePersistedRef } from './usePersistedRef';

const STORAGE_KEY = 'projectapp-dark-mode';

const persisted = usePersistedRef(STORAGE_KEY, false);
const isDark = persisted.ref;

export function themeToggleLabel(dark) {
  return dark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro';
}

export function useDarkMode() {
  function applyTheme(dark) {
    /* c8 ignore next */
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

  watch(isDark, (val) => {
    applyTheme(val);
    persisted.write(val);
  });

  onMounted(() => {
    const stored = persisted.read();
    isDark.value = stored !== null ? stored : false;
    applyTheme(isDark.value);
  });

  return { isDark, toggle };
}
