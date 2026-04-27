import { watch, onMounted } from 'vue';
import { usePersistedRef } from './usePersistedRef';

const STORAGE_KEY = 'proposal-dark-mode';

const persisted = usePersistedRef(STORAGE_KEY, false);
const isDark = persisted.ref;

export function useProposalDarkMode() {
  function applyTheme(dark) {
    /* c8 ignore next */
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
    persisted.write(val);
  });

  onMounted(() => {
    const stored = persisted.read();
    if (stored !== null) isDark.value = stored;
    applyTheme(isDark.value);
  });

  return { isDark, toggle, applyTheme };
}
