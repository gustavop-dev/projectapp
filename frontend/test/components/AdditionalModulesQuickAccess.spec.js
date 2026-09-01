import { flushPromises, mount } from '@vue/test-utils'
import BaseBadge from '../../components/base/BaseBadge.vue'
import BaseButton from '../../components/base/BaseButton.vue'
import BaseInput from '../../components/base/BaseInput.vue'
import AdditionalModulesQuickAccess from '../../components/AdditionalModules/QuickAccess.vue'
import { get_request } from '../../stores/services/request_http'
import { downloadBlob, filenameFromDisposition } from '../../utils/downloadFile'

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
}))

jest.mock('../../utils/downloadFile', () => ({
  downloadBlob: jest.fn(),
  filenameFromDisposition: jest.fn(),
}))

global.useI18n = jest.fn(() => ({
  t: (key) => key,
}))

const stats = {
  active_module_count: 23,
  active_share_count: 4,
  unopened_active_share_count: 2,
  last_viewed_at: '2026-08-31T14:30:00Z',
}

const BaseAlertStub = {
  props: ['variant', 'title', 'dismissible'],
  emits: ['dismiss'],
  template: '<div role="alert"><strong>{{ title }}</strong><slot /></div>',
}

function mountQuickAccess(props = {}) {
  return mount(AdditionalModulesQuickAccess, {
    props: { language: 'es', stats, ...props },
    global: {
      components: { BaseBadge, BaseButton, BaseInput },
      stubs: {
        BaseActionIcon: true,
        BaseAlert: BaseAlertStub,
        NuxtLink: true,
      },
    },
  })
}

describe('AdditionalModulesQuickAccess', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: jest.fn().mockResolvedValue(undefined) },
    })
  })

  it('shows the canonical public URL and commercial metrics', async () => {
    const wrapper = mountQuickAccess()
    await flushPromises()

    expect(wrapper.get('[data-testid="additional-modules-public-url"]').element.value)
      .toBe('http://localhost/es-co/additional-modules')
    expect(wrapper.get('[data-testid="additional-modules-active-count"]').text()).toBe('23')
    expect(wrapper.get('[data-testid="additional-modules-active-share-count"]').text()).toBe('4')
    expect(wrapper.get('[data-testid="additional-modules-unopened-count"]').text()).toBe('2')
    expect(wrapper.text()).not.toMatch(/COP|USD|\$/)
  })

  it('keeps the canonical resource in Spanish inside an English panel', async () => {
    const wrapper = mountQuickAccess({ language: 'en' })
    await flushPromises()

    expect(wrapper.get('[data-testid="additional-modules-public-url"]').element.value)
      .toBe('http://localhost/es-co/additional-modules')
  })

  it('copies the canonical public URL', async () => {
    const wrapper = mountQuickAccess()

    await wrapper.get('[data-testid="additional-modules-copy-public-url"]').trigger('click')
    await flushPromises()

    expect(navigator.clipboard.writeText)
      .toHaveBeenCalledWith('http://localhost/es-co/additional-modules')
    expect(wrapper.get('[role="alert"]').text()).toContain('additionalModules.publicUrlCopied')
  })

  it('keeps the URL visible when clipboard access fails', async () => {
    navigator.clipboard.writeText.mockRejectedValue(new Error('denied'))
    const wrapper = mountQuickAccess()

    await wrapper.get('[data-testid="additional-modules-copy-public-url"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toContain('additionalModules.copyFailedBody')
    expect(wrapper.get('[data-testid="additional-modules-public-url"]').element.value)
      .toBe('http://localhost/es-co/additional-modules')
  })

  it('downloads the complete public PDF with the response filename', async () => {
    const pdf = new Blob(['pdf'], { type: 'application/pdf' })
    filenameFromDisposition.mockReturnValue('catalogo-vigente.pdf')
    get_request.mockResolvedValue({
      data: pdf,
      headers: { 'content-disposition': 'attachment; filename="catalogo-vigente.pdf"' },
    })
    const wrapper = mountQuickAccess({ language: 'en' })

    await wrapper.get('[data-testid="additional-modules-download-full-pdf"]').trigger('click')
    await flushPromises()

    expect(get_request).toHaveBeenCalledWith(
      'additional-modules/public/pdf/?lang=es',
      { responseType: 'blob' },
    )
    expect(downloadBlob).toHaveBeenCalledWith(pdf, 'catalogo-vigente.pdf')
  })

  it('reports a failed complete PDF download', async () => {
    get_request.mockRejectedValue(new Error('unavailable'))
    const wrapper = mountQuickAccess()

    await wrapper.get('[data-testid="additional-modules-download-full-pdf"]').trigger('click')
    await flushPromises()

    expect(downloadBlob).not.toHaveBeenCalled()
    expect(wrapper.get('[role="alert"]').text())
      .toContain('additionalModules.pdfDownloadErrorTitle')
  })

  it('requests a client-specific selection', async () => {
    const wrapper = mountQuickAccess()

    await wrapper.get('[data-testid="additional-modules-create-share"]').trigger('click')

    expect(wrapper.emitted('share')).toHaveLength(1)
  })

  it('requests a personalized PDF', async () => {
    const wrapper = mountQuickAccess()

    await wrapper.get('[data-testid="additional-modules-customize-pdf"]').trigger('click')

    expect(wrapper.emitted('customize-pdf')).toHaveLength(1)
  })

  it('requests tracking history', async () => {
    const wrapper = mountQuickAccess()

    await wrapper.get('[data-testid="additional-modules-tracking"]').trigger('click')

    expect(wrapper.emitted('tracking')).toHaveLength(1)
  })

  it('offers catalog administration from the dashboard variant', async () => {
    const wrapper = mountQuickAccess({ compact: true })

    await wrapper.get('[data-testid="additional-modules-manage"]').trigger('click')

    expect(wrapper.emitted('manage')).toHaveLength(1)
  })
})
