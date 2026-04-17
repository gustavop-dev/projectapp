import { ref } from 'vue';

const toastMsg = ref(null);
let toastTimer = null;

function clearToast() {
  if (toastTimer) {
    clearTimeout(toastTimer);
    toastTimer = null;
  }
  toastMsg.value = null;
}

function showToast({ type = 'success', text = '', duration = 5000 } = {}) {
  if (toastTimer) {
    clearTimeout(toastTimer);
    toastTimer = null;
  }
  toastMsg.value = { type, text };
  if (duration > 0) {
    toastTimer = setTimeout(() => {
      toastMsg.value = null;
      toastTimer = null;
    }, duration);
  }
}

export function usePanelToast() {
  return { toastMsg, showToast, clearToast };
}
