/**
 * Tests for useDiagnosticCommercialPrompt and useDiagnosticTechnicalPrompt composables.
 */
const COMMERCIAL_KEY = 'projectapp-diagnostic-commercial-prompt'
const TECHNICAL_KEY = 'projectapp-diagnostic-technical-prompt'

describe('useDiagnosticCommercialPrompt', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.resetModules()
  })

  afterEach(() => {
    localStorage.removeItem(COMMERCIAL_KEY)
  })

  it('loadSaved reads override text from localStorage with the commercial key', () => {
    localStorage.setItem(COMMERCIAL_KEY, 'custom-commercial')
    const { useDiagnosticCommercialPrompt } = require('../../composables/useDiagnosticPrompt')
    const { loadSaved, promptText } = useDiagnosticCommercialPrompt()
    loadSaved()
    expect(promptText.value).toBe('custom-commercial')
  })

  it('loadSaved falls back to defaultPrompt when localStorage read throws', () => {
    const spy = jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('denied')
    })
    const { useDiagnosticCommercialPrompt } = require('../../composables/useDiagnosticPrompt')
    const { loadSaved, defaultPrompt, promptText } = useDiagnosticCommercialPrompt()
    loadSaved()
    expect(promptText.value).toBe(defaultPrompt)
    spy.mockRestore()
  })

  it('save updates ref and writes to localStorage', () => {
    const { useDiagnosticCommercialPrompt } = require('../../composables/useDiagnosticPrompt')
    const { save, promptText } = useDiagnosticCommercialPrompt()
    save('my commercial prompt')
    expect(promptText.value).toBe('my commercial prompt')
    expect(localStorage.getItem(COMMERCIAL_KEY)).toBe('my commercial prompt')
  })

  it('save silently handles localStorage write errors', () => {
    const spy = jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('quota')
    })
    const { useDiagnosticCommercialPrompt } = require('../../composables/useDiagnosticPrompt')
    const { save, promptText } = useDiagnosticCommercialPrompt()
    save('still saved in ref')
    expect(promptText.value).toBe('still saved in ref')
    spy.mockRestore()
  })

  it('reset restores defaultPrompt and removes localStorage key', () => {
    const { useDiagnosticCommercialPrompt } = require('../../composables/useDiagnosticPrompt')
    const { reset, promptText, defaultPrompt } = useDiagnosticCommercialPrompt()
    localStorage.setItem(COMMERCIAL_KEY, 'override')
    reset()
    expect(promptText.value).toBe(defaultPrompt)
    expect(localStorage.getItem(COMMERCIAL_KEY)).toBeNull()
  })

  it('reset still resets text when removeItem throws', () => {
    const { useDiagnosticCommercialPrompt } = require('../../composables/useDiagnosticPrompt')
    const { reset, promptText, defaultPrompt } = useDiagnosticCommercialPrompt()
    const rm = jest.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
      throw new Error('denied')
    })
    reset()
    expect(promptText.value).toBe(defaultPrompt)
    rm.mockRestore()
  })

  it('copy calls navigator.clipboard.writeText with promptText value', async () => {
    const { useDiagnosticCommercialPrompt } = require('../../composables/useDiagnosticPrompt')
    const { copy } = useDiagnosticCommercialPrompt()
    const writeText = jest.fn().mockResolvedValue(undefined)
    Object.assign(navigator, { clipboard: { writeText } })
    await expect(copy()).resolves.toBeUndefined()
    expect(writeText).toHaveBeenCalled()
  })

  it('copy falls back gracefully when clipboard API is absent', async () => {
    const { useDiagnosticCommercialPrompt } = require('../../composables/useDiagnosticPrompt')
    const { copy } = useDiagnosticCommercialPrompt()
    const prev = navigator.clipboard
    delete navigator.clipboard
    await expect(copy()).resolves.toBeUndefined()
    if (prev) navigator.clipboard = prev
  })

  it('download creates and clicks an anchor element with .md extension', () => {
    const { useDiagnosticCommercialPrompt } = require('../../composables/useDiagnosticPrompt')
    const { download, promptText } = useDiagnosticCommercialPrompt()
    promptText.value = 'commercial content'
    const prevCreate = URL.createObjectURL
    const prevRevoke = URL.revokeObjectURL
    URL.createObjectURL = jest.fn(() => 'blob:commercial')
    URL.revokeObjectURL = jest.fn()
    const link = { click: jest.fn(), href: '', download: '' }
    jest.spyOn(document, 'createElement').mockReturnValue(link)
    jest.spyOn(document.body, 'appendChild').mockImplementation(() => {})
    jest.spyOn(document.body, 'removeChild').mockImplementation(() => {})
    download('prompt-comercial.md')
    expect(link.click).toHaveBeenCalled()
    URL.createObjectURL = prevCreate
    URL.revokeObjectURL = prevRevoke
    document.createElement.mockRestore()
    document.body.appendChild.mockRestore()
    document.body.removeChild.mockRestore()
  })
})

describe('useDiagnosticTechnicalPrompt', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.resetModules()
  })

  afterEach(() => {
    localStorage.removeItem(TECHNICAL_KEY)
  })

  it('loadSaved reads override text from localStorage with the technical key', () => {
    localStorage.setItem(TECHNICAL_KEY, 'custom-technical')
    const { useDiagnosticTechnicalPrompt } = require('../../composables/useDiagnosticPrompt')
    const { loadSaved, promptText } = useDiagnosticTechnicalPrompt()
    loadSaved()
    expect(promptText.value).toBe('custom-technical')
  })

  it('loadSaved falls back to defaultPrompt when localStorage read throws', () => {
    const spy = jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('denied')
    })
    const { useDiagnosticTechnicalPrompt } = require('../../composables/useDiagnosticPrompt')
    const { loadSaved, defaultPrompt, promptText } = useDiagnosticTechnicalPrompt()
    loadSaved()
    expect(promptText.value).toBe(defaultPrompt)
    spy.mockRestore()
  })

  it('save updates ref and writes to localStorage', () => {
    const { useDiagnosticTechnicalPrompt } = require('../../composables/useDiagnosticPrompt')
    const { save, promptText } = useDiagnosticTechnicalPrompt()
    save('my technical prompt')
    expect(promptText.value).toBe('my technical prompt')
    expect(localStorage.getItem(TECHNICAL_KEY)).toBe('my technical prompt')
  })

  it('save silently handles localStorage write errors', () => {
    const spy = jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('quota')
    })
    const { useDiagnosticTechnicalPrompt } = require('../../composables/useDiagnosticPrompt')
    const { save, promptText } = useDiagnosticTechnicalPrompt()
    save('still in ref')
    expect(promptText.value).toBe('still in ref')
    spy.mockRestore()
  })

  it('reset restores defaultPrompt and removes localStorage key', () => {
    const { useDiagnosticTechnicalPrompt } = require('../../composables/useDiagnosticPrompt')
    const { reset, promptText, defaultPrompt } = useDiagnosticTechnicalPrompt()
    localStorage.setItem(TECHNICAL_KEY, 'override')
    reset()
    expect(promptText.value).toBe(defaultPrompt)
    expect(localStorage.getItem(TECHNICAL_KEY)).toBeNull()
  })

  it('reset still resets text when removeItem throws', () => {
    const { useDiagnosticTechnicalPrompt } = require('../../composables/useDiagnosticPrompt')
    const { reset, promptText, defaultPrompt } = useDiagnosticTechnicalPrompt()
    const rm = jest.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
      throw new Error('denied')
    })
    reset()
    expect(promptText.value).toBe(defaultPrompt)
    rm.mockRestore()
  })

  it('copy calls navigator.clipboard.writeText with promptText value', async () => {
    const { useDiagnosticTechnicalPrompt } = require('../../composables/useDiagnosticPrompt')
    const { copy } = useDiagnosticTechnicalPrompt()
    const writeText = jest.fn().mockResolvedValue(undefined)
    Object.assign(navigator, { clipboard: { writeText } })
    await expect(copy()).resolves.toBeUndefined()
    expect(writeText).toHaveBeenCalled()
  })

  it('copy falls back gracefully when clipboard API is absent', async () => {
    const { useDiagnosticTechnicalPrompt } = require('../../composables/useDiagnosticPrompt')
    const { copy } = useDiagnosticTechnicalPrompt()
    const prev = navigator.clipboard
    delete navigator.clipboard
    await expect(copy()).resolves.toBeUndefined()
    if (prev) navigator.clipboard = prev
  })

  it('download creates and clicks an anchor element with .md extension', () => {
    const { useDiagnosticTechnicalPrompt } = require('../../composables/useDiagnosticPrompt')
    const { download, promptText } = useDiagnosticTechnicalPrompt()
    promptText.value = 'technical content'
    const prevCreate = URL.createObjectURL
    const prevRevoke = URL.revokeObjectURL
    URL.createObjectURL = jest.fn(() => 'blob:technical')
    URL.revokeObjectURL = jest.fn()
    const link = { click: jest.fn(), href: '', download: '' }
    jest.spyOn(document, 'createElement').mockReturnValue(link)
    jest.spyOn(document.body, 'appendChild').mockImplementation(() => {})
    jest.spyOn(document.body, 'removeChild').mockImplementation(() => {})
    download('prompt-tecnico.md')
    expect(link.click).toHaveBeenCalled()
    URL.createObjectURL = prevCreate
    URL.revokeObjectURL = prevRevoke
    document.createElement.mockRestore()
    document.body.appendChild.mockRestore()
    document.body.removeChild.mockRestore()
  })
})
