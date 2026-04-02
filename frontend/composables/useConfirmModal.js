import { ref } from 'vue'

/**
 * Composable for replacing native confirm() with ConfirmModal.
 *
 * Supports two usage patterns:
 *
 * **Pattern 1 — Callback (preferred for simple actions):**
 *   requestConfirm({
 *     title: 'Eliminar propuesta',
 *     message: '¿Estás seguro?',
 *     variant: 'danger',
 *     confirmText: 'Eliminar',
 *     onConfirm: () => store.deleteProposal(id),
 *   })
 *
 * **Pattern 2 — Await/Promise (for inline control flow):**
 *   const confirmed = await requestConfirm({
 *     title: 'Aplicar JSON',
 *     message: '¿Continuar?',
 *   })
 *   if (!confirmed) return
 *   // ... proceed with action
 *
 * Template usage (same for both patterns):
 *   <ConfirmModal v-model="confirmState.open" :title="confirmState.title" ...
 *     @confirm="handleConfirmed" @cancel="handleCancelled" />
 */
export function useConfirmModal() {
  const confirmState = ref({
    open: false,
    title: '',
    message: '',
    confirmText: 'Confirmar',
    cancelText: 'Cancelar',
    variant: 'warning',
    onConfirm: null,
    _resolve: null,
  })

  /**
   * Opens the confirmation modal.
   * When `onConfirm` callback is provided, it runs on confirm.
   * Always returns a Promise<boolean> that resolves to true on confirm, false on cancel.
   */
  function requestConfirm({ title, message, confirmText, cancelText, variant, onConfirm }) {
    return new Promise((resolve) => {
      confirmState.value = {
        open: true,
        title: title || 'Confirmar acción',
        message: message || '¿Estás seguro de que deseas continuar?',
        confirmText: confirmText || 'Confirmar',
        cancelText: cancelText || 'Cancelar',
        variant: variant || 'warning',
        onConfirm: onConfirm || null,
        _resolve: resolve,
      }
    })
  }

  async function handleConfirmed() {
    const fn = confirmState.value.onConfirm
    const resolve = confirmState.value._resolve
    confirmState.value.open = false
    if (fn) await fn()
    if (resolve) resolve(true)
  }

  function handleCancelled() {
    const resolve = confirmState.value._resolve
    confirmState.value.open = false
    confirmState.value.onConfirm = null
    confirmState.value._resolve = null
    if (resolve) resolve(false)
  }

  return { confirmState, requestConfirm, handleConfirmed, handleCancelled }
}
