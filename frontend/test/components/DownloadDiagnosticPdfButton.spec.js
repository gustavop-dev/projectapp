const mockStore = {
  current: { uuid: 'test-uuid-123', title: 'Mi Diagnóstico', client_name: 'Acme Corp' },
}

jest.mock('../../stores/diagnostics', () => ({
  useDiagnosticsStore: () => mockStore,
}))

import { mount } from '@vue/test-utils'
import DownloadDiagnosticPdfButton from '../../components/WebAppDiagnostic/public/DownloadDiagnosticPdfButton.vue'

async function flushMicrotasks() {
  await Promise.resolve()
  await Promise.resolve()
  await Promise.resolve()
}

function mountButton() {
  return mount(DownloadDiagnosticPdfButton)
}

function mockSuccessfulFetch() {
  const mockBlob = new Blob(['pdf'], { type: 'application/pdf' })
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    blob: jest.fn().mockResolvedValue(mockBlob),
  })
  return mockBlob
}

describe('DownloadDiagnosticPdfButton', () => {
  let capturedLink

  beforeEach(() => {
    mockStore.current = { uuid: 'test-uuid-123', title: 'Mi Diagnóstico', client_name: 'Acme Corp' }
    capturedLink = null

    const origAppend = document.body.appendChild.bind(document.body)
    jest.spyOn(document.body, 'appendChild').mockImplementation((el) => {
      capturedLink = el
      return origAppend(el)
    })
    jest.spyOn(document.body, 'removeChild').mockImplementation((el) => el)
    jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    global.URL.createObjectURL = jest.fn(() => 'blob:mock-url')
    global.URL.revokeObjectURL = jest.fn()

    jest.useFakeTimers()
    jest.setSystemTime(new Date('2026-04-25T12:00:00'))
  })

  afterEach(() => {
    jest.restoreAllMocks()
    jest.useRealTimers()
  })

  it('renders button with data-testid="download-diagnostic-pdf-btn"', () => {
    global.fetch = jest.fn()
    const wrapper = mountButton()
    expect(wrapper.find('[data-testid="download-diagnostic-pdf-btn"]').exists()).toBe(true)
  })

  it('button title is "Descargar PDF" when not generating', () => {
    global.fetch = jest.fn()
    const wrapper = mountButton()
    expect(wrapper.find('[data-testid="download-diagnostic-pdf-btn"]').attributes('title')).toBe('Descargar PDF')
  })

  it('button is not disabled when not generating', () => {
    global.fetch = jest.fn()
    const wrapper = mountButton()
    expect(wrapper.find('[data-testid="download-diagnostic-pdf-btn"]').attributes('disabled')).toBeUndefined()
  })

  it('button is disabled while fetch is in progress', async () => {
    global.fetch = jest.fn(() => new Promise(() => {}))
    const wrapper = mountButton()
    await wrapper.find('[data-testid="download-diagnostic-pdf-btn"]').trigger('click')
    expect(wrapper.find('[data-testid="download-diagnostic-pdf-btn"]').attributes('disabled')).toBeDefined()
  })

  it('downloadPdf fetches from the correct URL using the store UUID', async () => {
    mockSuccessfulFetch()
    const wrapper = mountButton()
    await wrapper.find('[data-testid="download-diagnostic-pdf-btn"]').trigger('click')
    expect(global.fetch).toHaveBeenCalledWith('/api/diagnostics/public/test-uuid-123/pdf/')
  })

  it('downloadPdf creates an object URL from the response blob', async () => {
    const mockBlob = mockSuccessfulFetch()
    const wrapper = mountButton()
    await wrapper.find('[data-testid="download-diagnostic-pdf-btn"]').trigger('click')
    await flushMicrotasks()
    expect(global.URL.createObjectURL).toHaveBeenCalledWith(mockBlob)
  })

  it('downloadPdf revokes the object URL after triggering the download', async () => {
    mockSuccessfulFetch()
    const wrapper = mountButton()
    await wrapper.find('[data-testid="download-diagnostic-pdf-btn"]').trigger('click')
    await flushMicrotasks()
    expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
  })

  it('downloadPdf sets filename from title and the current date', async () => {
    mockSuccessfulFetch()
    const wrapper = mountButton()
    await wrapper.find('[data-testid="download-diagnostic-pdf-btn"]').trigger('click')
    await flushMicrotasks()
    expect(capturedLink.download).toBe('Diagnostico_Mi_Diagnóstico_25-04-26.pdf')
  })

  it('downloadPdf re-enables button after successful download', async () => {
    mockSuccessfulFetch()
    const wrapper = mountButton()
    await wrapper.find('[data-testid="download-diagnostic-pdf-btn"]').trigger('click')
    await flushMicrotasks()
    expect(wrapper.find('[data-testid="download-diagnostic-pdf-btn"]').attributes('disabled')).toBeUndefined()
  })

  it('downloadPdf catches fetch errors and re-enables the button', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error'))
    jest.spyOn(console, 'error').mockImplementation(() => {})
    const wrapper = mountButton()
    await wrapper.find('[data-testid="download-diagnostic-pdf-btn"]').trigger('click')
    await flushMicrotasks()
    expect(wrapper.find('[data-testid="download-diagnostic-pdf-btn"]').attributes('disabled')).toBeUndefined()
  })

  it('downloadPdf does nothing when store.current has no UUID', async () => {
    mockStore.current = { uuid: null, title: null, client_name: null }
    global.fetch = jest.fn()
    const wrapper = mountButton()
    await wrapper.find('[data-testid="download-diagnostic-pdf-btn"]').trigger('click')
    expect(global.fetch).not.toHaveBeenCalled()
  })
})
