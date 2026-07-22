import { mount } from '@vue/test-utils'

import ViewModuleGrid from '../../components/views/ViewModuleGrid.vue'

const ViewModuleCardStub = {
  props: ['section'],
  emits: ['select'],
  template: '<button class="card-stub" @click="$emit(\'select\', section.id)">{{ section.id }}</button>',
}

function mountGrid(sections) {
  return mount(ViewModuleGrid, {
    props: { sections },
    global: { stubs: { ViewModuleCard: ViewModuleCardStub } },
  })
}

describe('ViewModuleGrid', () => {
  it('renders one card per section', () => {
    const wrapper = mountGrid([{ id: 'sales' }, { id: 'accounting' }, { id: 'blog' }])
    expect(wrapper.findAll('.card-stub')).toHaveLength(3)
  })

  it('re-emits the select payload from a card', async () => {
    const wrapper = mountGrid([{ id: 'sales' }, { id: 'accounting' }])
    await wrapper.findAll('.card-stub')[1].trigger('click')
    expect(wrapper.emitted('select')).toEqual([['accounting']])
  })
})
