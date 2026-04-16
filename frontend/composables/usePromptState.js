/**
 * Factory for a prompt-editor state object.
 *
 * Wraps a single default prompt string in a ref + localStorage override
 * with load / save / reset / copy / download operations, suitable for any
 * "admin-editable instructional prompt" UI.
 */
import { ref } from 'vue';

export function usePromptState({ storageKey, defaultPrompt }) {
  const promptText = ref(defaultPrompt);
  const isEditing = ref(false);

  function loadSaved() {
    try {
      if (typeof localStorage === 'undefined') return;
      const saved = localStorage.getItem(storageKey);
      if (saved) promptText.value = saved;
    } catch (_e) { /* ignore */ }
  }

  function save(text) {
    promptText.value = text;
    try {
      localStorage.setItem(storageKey, text);
    } catch (_e) { /* ignore */ }
  }

  function reset() {
    promptText.value = defaultPrompt;
    try {
      localStorage.removeItem(storageKey);
    } catch (_e) { /* ignore */ }
  }

  function copy() {
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      return navigator.clipboard.writeText(promptText.value);
    }
    return Promise.resolve();
  }

  function download(filename) {
    const blob = new Blob([promptText.value], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return {
    promptText,
    isEditing,
    defaultPrompt,
    loadSaved,
    save,
    reset,
    copy,
    download,
  };
}
