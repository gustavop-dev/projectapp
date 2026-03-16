import { ref } from 'vue'

/**
 * Composable for replacing native confirm() with ConfirmModal.
 *
 * Usage:
 *   const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal()
 *
 *   // In the action handler:
 *   function handleDelete(id) {
 *     requestConfirm({
 *       title: 'Eliminar propuesta',
 *       message: '¿Estás seguro?',
 *       variant: 'danger',
 *       confirmText: 'Eliminar',
 *       onConfirm: () => store.deleteProposal(id),
 *     })
 *   }
 *
 *   // In the template:
 *   <ConfirmModal v-model="confirmState.open" :title="confirmState.title" ... @confirm="handleConfirmed" @cancel="handleCancelled" />
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
  })

  function requestConfirm({ title, message, confirmText, cancelText, variant, onConfirm }) {
    confirmState.value = {
      open: true,
      title: title || 'Confirmar acción',
      message: message || '¿Estás seguro de que deseas continuar?',
      confirmText: confirmText || 'Confirmar',
      cancelText: cancelText || 'Cancelar',
      variant: variant || 'warning',
      onConfirm: onConfirm || null,
    }
  }

  async function handleConfirmed() {
    const fn = confirmState.value.onConfirm
    confirmState.value.open = false
    if (fn) await fn()
  }

  function handleCancelled() {
    confirmState.value.open = false
    confirmState.value.onConfirm = null
  }

  return { confirmState, requestConfirm, handleConfirmed, handleCancelled }
}
