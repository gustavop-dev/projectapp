import { mount } from '@vue/test-utils'

import BaseExploratoryList from '~/components/base/BaseExploratoryList.vue'

const rows = [{ id: 7, name: 'Proyecto Aurora', status: 'Activo', internal: 'Privado' }]
const columns = [
  { key: 'name', label: 'Proyecto', mobile: 'primary' },
  { key: 'status', label: 'Estado', mobile: 'secondary' },
  { key: 'internal', label: 'Interno', mobile: 'hidden' },
]

function mockViewport(mobile) {
  window.matchMedia = jest.fn().mockReturnValue({
    matches: mobile,
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
  })
}

async function mountList(mobile) {
  mockViewport(mobile)
  const wrapper = mount(BaseExploratoryList, {
    props: { columns, rows, cardTestIdPrefix: 'project' },
  })
  await wrapper.vm.$nextTick()
  return wrapper
}

describe('BaseExploratoryList', () => {
  afterEach(() => { delete window.matchMedia })

  it('renders only the wide table outside the compact and portrait profiles', async () => {
    const wrapper = await mountList(false)

    expect(wrapper.find('table').exists()).toBe(true)
    expect(wrapper.find('article').exists()).toBe(false)
    expect(wrapper.text()).toContain('Privado')
  })

  it('renders only one stacked card on compact and portrait screens', async () => {
    const wrapper = await mountList(true)

    expect(wrapper.find('table').exists()).toBe(false)
    expect(wrapper.findAll('article')).toHaveLength(1)
    expect(wrapper.get('[data-testid="project-7"]').text()).toContain('Proyecto Aurora')
  })

  it('keeps explicit mobile details and omits hidden fields from the card', async () => {
    const wrapper = await mountList(true)
    const card = wrapper.get('[data-testid="project-7"]')

    expect(card.text()).toContain('Estado')
    expect(card.text()).toContain('Activo')
    expect(card.text()).not.toContain('Privado')
  })
})
