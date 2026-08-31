import { effectScope } from 'vue'
import { useClipboardFeedback } from '../../composables/useClipboardFeedback'

describe('useClipboardFeedback', () => {
  let originalClipboard

  beforeEach(() => {
    jest.useFakeTimers()
    originalClipboard = navigator.clipboard
  })

  afterEach(() => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: originalClipboard,
    })
    jest.useRealTimers()
  })

  function setClipboard(writeText) {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    })
  }

  it('shows success only after the clipboard write resolves', async () => {
    let resolveWrite
    setClipboard(jest.fn(() => new Promise((resolve) => { resolveWrite = resolve })))
    const feedback = useClipboardFeedback()

    const copyPromise = feedback.copyText({
      key: 'url',
      text: 'https://projectapp.co',
      successLabel: 'Copiado: URL pública',
    })
    expect(feedback.feedbackFor('url').label).toBe('')

    resolveWrite()
    await expect(copyPromise).resolves.toBe(true)
    expect(feedback.feedbackFor('url')).toEqual({
      label: 'Copiado: URL pública',
      tone: 'success',
    })
  })

  it('keeps feedback independent for repeated controls', async () => {
    setClipboard(jest.fn().mockResolvedValue(undefined))
    const feedback = useClipboardFeedback()

    await feedback.copyText({ key: 'first', text: 'one', successLabel: 'Primero copiado' })
    await feedback.copyText({ key: 'second', text: 'two', successLabel: 'Segundo copiado' })

    expect(feedback.feedbackFor('first').label).toBe('Primero copiado')
    expect(feedback.feedbackFor('second').label).toBe('Segundo copiado')
  })

  it('shows an error and calls the owning error handler when copying fails', async () => {
    const error = new Error('denied')
    const onError = jest.fn()
    setClipboard(jest.fn().mockRejectedValue(error))
    const feedback = useClipboardFeedback()

    await expect(feedback.copyText({
      key: 'url',
      text: 'blocked',
      errorLabel: 'No se pudo copiar el enlace',
      onError,
    })).resolves.toBe(false)

    expect(feedback.feedbackFor('url')).toEqual({
      label: 'No se pudo copiar el enlace',
      tone: 'danger',
    })
    expect(onError).toHaveBeenCalledWith(error)
  })

  it('clears success and error feedback after their respective durations', async () => {
    const writeText = jest.fn()
      .mockResolvedValueOnce(undefined)
      .mockRejectedValueOnce(new Error('denied'))
    setClipboard(writeText)
    const feedback = useClipboardFeedback({ successDuration: 2_000, errorDuration: 3_000 })

    await feedback.copyText({ key: 'success', text: 'one' })
    await feedback.copyText({ key: 'error', text: 'two' })
    jest.advanceTimersByTime(2_000)
    expect(feedback.feedbackFor('success').label).toBe('')
    expect(feedback.feedbackFor('error').tone).toBe('danger')

    jest.advanceTimersByTime(1_000)
    expect(feedback.feedbackFor('error').label).toBe('')
  })

  it('cleans pending feedback when its component scope stops', async () => {
    setClipboard(jest.fn().mockResolvedValue(undefined))
    const scope = effectScope()
    const feedback = scope.run(() => useClipboardFeedback())
    await feedback.copyText({ key: 'url', text: 'value' })

    scope.stop()

    expect(feedback.feedbackFor('url').label).toBe('')
    expect(jest.getTimerCount()).toBe(0)
  })
})
