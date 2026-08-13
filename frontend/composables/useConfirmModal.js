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
    requireTypeText: '',
    hideCancel: false,
    // Acción alternativa no destructiva (p. ej. "Archivar en su lugar"), que
    // se ofrece junto al botón de confirmación.
    secondaryText: '',
    secondaryVariant: 'secondary',
    secondaryHint: '',
    // Sólo con `waitForConfirm: true`: el modal queda abierto y `busy` mientras
    // corre onConfirm (spinner en el botón, sin doble-submit). El camino
    // default —cerrar primero, correr después— queda intacto para los ~25
    // call sites existentes.
    waitForConfirm: false,
    busy: false,
    onConfirm: null,
    onSecondary: null,
    _resolve: null,
  })

  /**
   * Opens the confirmation modal.
   * When `onConfirm` callback is provided, it runs on confirm.
   * Always returns a Promise<boolean> that resolves to true on confirm, false on cancel.
   */
  function requestConfirm({
    title, message, confirmText, cancelText, variant, requireTypeText, hideCancel,
    onConfirm, secondaryText, secondaryVariant, secondaryHint, onSecondary,
    waitForConfirm,
  }) {
    return new Promise((resolve) => {
      confirmState.value = {
        open: true,
        title: title || 'Confirmar acción',
        message: message || '¿Estás seguro de que deseas continuar?',
        confirmText: confirmText || 'Confirmar',
        cancelText: cancelText || 'Cancelar',
        variant: variant || 'warning',
        requireTypeText: requireTypeText || '',
        hideCancel: Boolean(hideCancel),
        secondaryText: secondaryText || '',
        secondaryVariant: secondaryVariant || 'secondary',
        secondaryHint: secondaryHint || '',
        waitForConfirm: Boolean(waitForConfirm),
        busy: false,
        onConfirm: onConfirm || null,
        onSecondary: onSecondary || null,
        _resolve: resolve,
      }
    })
  }

  async function handleConfirmed() {
    const fn = confirmState.value.onConfirm
    const resolve = confirmState.value._resolve
    if (fn && confirmState.value.waitForConfirm) {
      confirmState.value.busy = true
      try {
        await fn()
      } finally {
        confirmState.value.busy = false
        confirmState.value.open = false
      }
      if (resolve) resolve(true)
      return
    }
    confirmState.value.open = false
    if (fn) await fn()
    if (resolve) resolve(true)
  }

  async function handleSecondaryAction() {
    const fn = confirmState.value.onSecondary
    const resolve = confirmState.value._resolve
    confirmState.value.open = false
    if (fn) await fn()
    // Resuelve FALSE, no un centinela truthy: los callers del patrón `await`
    // hacen `if (!confirmed) return`, y elegir la alternativa no es confirmar.
    if (resolve) resolve(false)
  }

  function handleCancelled() {
    // Con la acción en vuelo no hay cancelación: el modal ya la despachó.
    if (confirmState.value.busy) return
    const resolve = confirmState.value._resolve
    confirmState.value.open = false
    confirmState.value.onConfirm = null
    confirmState.value.onSecondary = null
    confirmState.value._resolve = null
    if (resolve) resolve(false)
  }

  return {
    confirmState, requestConfirm,
    handleConfirmed, handleSecondaryAction, handleCancelled,
  }
}
