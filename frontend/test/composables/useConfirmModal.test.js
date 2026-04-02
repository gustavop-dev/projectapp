/**
 * Tests for useConfirmModal composable.
 *
 * Covers: requestConfirm, handleConfirmed, handleCancelled,
 * default values, async onConfirm execution.
 */

const { useConfirmModal } = require('../../composables/useConfirmModal')

describe('useConfirmModal', () => {
  let confirmState, requestConfirm, handleConfirmed, handleCancelled

  beforeEach(() => {
    const result = useConfirmModal()
    confirmState = result.confirmState
    requestConfirm = result.requestConfirm
    handleConfirmed = result.handleConfirmed
    handleCancelled = result.handleCancelled
  })

  describe('initial state', () => {
    it('starts with modal closed', () => {
      expect(confirmState.value.open).toBe(false)
    })

    it('starts with empty title and message', () => {
      expect(confirmState.value.title).toBe('')
      expect(confirmState.value.message).toBe('')
    })

    it('starts with default button texts', () => {
      expect(confirmState.value.confirmText).toBe('Confirmar')
      expect(confirmState.value.cancelText).toBe('Cancelar')
    })

    it('starts with warning variant', () => {
      expect(confirmState.value.variant).toBe('warning')
    })

    it('starts with null onConfirm', () => {
      expect(confirmState.value.onConfirm).toBeNull()
    })
  })

  describe('requestConfirm', () => {
    it('opens modal with all provided fields', () => {
      const onConfirm = jest.fn()

      requestConfirm({
        title: 'Delete item',
        message: 'Are you sure?',
        confirmText: 'Delete',
        cancelText: 'Keep',
        variant: 'danger',
        onConfirm,
      })

      expect(confirmState.value.open).toBe(true)
      expect(confirmState.value.title).toBe('Delete item')
      expect(confirmState.value.message).toBe('Are you sure?')
      expect(confirmState.value.confirmText).toBe('Delete')
      expect(confirmState.value.cancelText).toBe('Keep')
      expect(confirmState.value.variant).toBe('danger')
      expect(confirmState.value.onConfirm).toBe(onConfirm)
    })

    it('uses default title when not provided', () => {
      requestConfirm({ message: 'test' })

      expect(confirmState.value.title).toBe('Confirmar acción')
    })

    it('uses default message when not provided', () => {
      requestConfirm({ title: 'test' })

      expect(confirmState.value.message).toBe('¿Estás seguro de que deseas continuar?')
    })

    it('uses default confirmText when not provided', () => {
      requestConfirm({})

      expect(confirmState.value.confirmText).toBe('Confirmar')
    })

    it('uses default cancelText when not provided', () => {
      requestConfirm({})

      expect(confirmState.value.cancelText).toBe('Cancelar')
    })

    it('uses default variant when not provided', () => {
      requestConfirm({})

      expect(confirmState.value.variant).toBe('warning')
    })

    it('sets onConfirm to null when not provided', () => {
      requestConfirm({})

      expect(confirmState.value.onConfirm).toBeNull()
    })
  })

  describe('handleConfirmed', () => {
    it('closes modal after confirmation', async () => {
      requestConfirm({ title: 'Test' })

      await handleConfirmed()

      expect(confirmState.value.open).toBe(false)
    })

    it('calls onConfirm callback when provided', async () => {
      const onConfirm = jest.fn()
      requestConfirm({ onConfirm })

      await handleConfirmed()

      expect(onConfirm).toHaveBeenCalledTimes(1)
    })

    it('awaits async onConfirm callback', async () => {
      let resolved = false
      const onConfirm = jest.fn().mockImplementation(async () => {
        resolved = true
      })
      requestConfirm({ onConfirm })

      await handleConfirmed()

      expect(resolved).toBe(true)
      expect(onConfirm).toHaveBeenCalledTimes(1)
    })

    it('handles missing onConfirm gracefully', async () => {
      requestConfirm({})

      await expect(handleConfirmed()).resolves.toBeUndefined()
      expect(confirmState.value.open).toBe(false)
    })
  })

  describe('handleCancelled', () => {
    it('closes modal on cancel', () => {
      requestConfirm({ title: 'Test' })

      handleCancelled()

      expect(confirmState.value.open).toBe(false)
    })

    it('clears onConfirm callback on cancel', () => {
      requestConfirm({ onConfirm: jest.fn() })

      handleCancelled()

      expect(confirmState.value.onConfirm).toBeNull()
    })
  })

  describe('promise pattern', () => {
    it('returns a promise from requestConfirm', () => {
      const result = requestConfirm({ title: 'Test' })

      expect(result).toBeInstanceOf(Promise)
    })

    it('resolves to true when confirmed', async () => {
      const promise = requestConfirm({ title: 'Test' })

      await handleConfirmed()

      await expect(promise).resolves.toBe(true)
    })

    it('resolves to false when cancelled', async () => {
      const promise = requestConfirm({ title: 'Test' })

      handleCancelled()

      await expect(promise).resolves.toBe(false)
    })

    it('runs onConfirm callback and resolves to true together', async () => {
      const onConfirm = jest.fn()
      const promise = requestConfirm({ title: 'Test', onConfirm })

      await handleConfirmed()

      expect(onConfirm).toHaveBeenCalledTimes(1)
      await expect(promise).resolves.toBe(true)
    })
  })
})
