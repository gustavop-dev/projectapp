import { mount } from '@vue/test-utils'

import DocumentsToolbar from '../../components/panel/documents/DocumentsToolbar.vue'
import BaseInput from '../../components/base/BaseInput.vue'
import BaseSegmented from '../../components/base/BaseSegmented.vue'

function mountToolbar(props = {}, options = {}) {
  return mount(DocumentsToolbar, {
    props: { search: '', viewMode: 'list', ...props },
    global: { components: { BaseInput, BaseSegmented } },
    ...options,
  })
}

describe('DocumentsToolbar', () => {
  it('re-emits search updates from the search input', async () => {
    const wrapper = mountToolbar()
    await wrapper.find('input[type="search"]').setValue('contrato')
    expect(wrapper.emitted('update:search')).toEqual([['contrato']])
  })

  it('binds the search prop into the input value', () => {
    const wrapper = mountToolbar({ search: 'acme' })
    expect(wrapper.find('input[type="search"]').element.value).toBe('acme')
  })

  it('re-emits the view mode when picking the gallery segment', async () => {
    const wrapper = mountToolbar()
    await wrapper.find('[data-testid="doc-view-grid"]').trigger('click')
    expect(wrapper.emitted('update:viewMode')).toEqual([['grid']])
  })

  it('renders content passed through the actions slot', () => {
    const wrapper = mountToolbar({}, undefined)
    const withSlot = mount(DocumentsToolbar, {
      props: { search: '', viewMode: 'list' },
      global: { components: { BaseInput, BaseSegmented } },
      slots: { actions: '<button data-testid="new-doc">Nuevo</button>' },
    })
    expect(withSlot.find('[data-testid="new-doc"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="new-doc"]').exists()).toBe(false)
  })
})
