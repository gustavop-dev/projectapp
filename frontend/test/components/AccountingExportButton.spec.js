import { flushPromises, mount } from '@vue/test-utils'

import AccountingExportButton from '../../components/accounting/AccountingExportButton.vue'
import { get_request } from '../../stores/services/request_http'
import { downloadBlob } from '../../utils/downloadFile'
import { usePanelNotify } from '../../composables/usePanelNotify'

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
}))
jest.mock('../../utils/downloadFile', () => ({
  downloadBlob: jest.fn(),
  filenameFromDisposition: jest.requireActual('../../utils/downloadFile').filenameFromDisposition,
}))
jest.mock('../../composables/usePanelNotify', () => {
  const notify = { error: jest.fn(), success: jest.fn() }
  return { usePanelNotify: jest.fn(() => notify) }
})

const BaseDropdownStub = {
  props: ['items'],
  template: `
    <div>
      <slot name="trigger" />
      <button v-for="item in items" :key="item.label" @click="item.onClick()">{{ item.label }}</button>
    </div>
  `,
}

function mountButton(props = {}) {
  return mount(AccountingExportButton, {
    props: { section: 'income', ...props },
    global: { stubs: { BaseDropdown: BaseDropdownStub } },
  })
}

describe('AccountingExportButton', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('exports CSV with the section and active filters in the query', async () => {
    get_request.mockResolvedValue({ data: new Blob(['csv']), headers: {} })
    const wrapper = mountButton({ params: { year: '2026', ledger: 'company' } })

    await wrapper.get('button:first-of-type').trigger('click')
    await flushPromises()

    const url = get_request.mock.calls[0][0]
    expect(url).toContain('section=income')
    expect(url).toContain('file_format=csv')
    expect(url).toContain('year=2026')
    expect(url).toContain('ledger=company')
  })

  it('names the download from the content-disposition header', async () => {
    get_request.mockResolvedValue({
      data: new Blob(['x']),
      headers: { 'content-disposition': 'attachment; filename="ingresos_2026.csv"' },
    })
    const wrapper = mountButton()

    await wrapper.get('button:first-of-type').trigger('click')
    await flushPromises()

    expect(downloadBlob).toHaveBeenCalledWith(expect.any(Blob), 'ingresos_2026.csv')
  })

  it('falls back to a section-based filename without the header', async () => {
    get_request.mockResolvedValue({ data: new Blob(['x']), headers: {} })
    const wrapper = mountButton()

    await wrapper.findAll('button')[1].trigger('click')
    await flushPromises()

    expect(downloadBlob).toHaveBeenCalledWith(expect.any(Blob), 'contabilidad_income.xlsx')
  })

  it('notifies the error and re-enables the trigger when the export fails', async () => {
    get_request.mockRejectedValue(new Error('500'))
    const wrapper = mountButton()

    await wrapper.get('button:first-of-type').trigger('click')
    await flushPromises()

    expect(usePanelNotify().error).toHaveBeenCalledWith(
      expect.objectContaining({ title: 'No se pudo exportar' }),
    )
    expect(downloadBlob).not.toHaveBeenCalled()
    expect(wrapper.get('[data-testid="accounting-export-button"]').text()).toBe('Exportar')
  })
})
