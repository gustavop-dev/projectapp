import { ref } from 'vue';
import { usePanelNotify } from '~/composables/usePanelNotify';

/**
 * Backward-compatible wrapper over the richer usePanelNotify system.
 *
 * Existing call sites use `showToast({ type, text })`; these now render through
 * the single global <PanelNotificationHost /> (mounted in layouts/admin.vue),
 * with `text` mapped to the notification title. New code should prefer
 * usePanelNotify directly to get title + detail + action support.
 */

// Kept only so legacy `toastMsg` imports stay defined; the old per-page
// <PanelToast /> is now a no-op and this ref stays null.
const toastMsg = ref(null);

export function usePanelToast() {
  const notify = usePanelNotify();

  function showToast({ type = 'success', text = '', duration } = {}) {
    const mapped = type === 'success' ? 'success' : (type === 'error' ? 'error' : type);
    return notify.push({ type: mapped, title: text, duration });
  }

  function clearToast() {
    notify.clearAll();
  }

  return { toastMsg, showToast, clearToast };
}
