import { mount } from '@vue/test-utils'
import BaseEmptyState from '../../components/base/BaseEmptyState.vue'

describe('BaseEmptyState', () => {
  it('renders title and description', () => {
    const wrapper = mount(BaseEmptyState, {
      props: { title: 'Sin resultados', description: 'No encontramos nada con esos filtros.' },
    })
    expect(wrapper.text()).toContain('Sin resultados')
    expect(wrapper.text()).toContain('No encontramos nada con esos filtros.')
  })

  it('uses surface + dashed border tokens for the container', () => {
    const wrapper = mount(BaseEmptyState, { props: { title: 'x' } })
    const cls = wrapper.classes()
    expect(cls).toContain('bg-surface')
    expect(cls).toContain('border-dashed')
    expect(cls).toContain('border-border-default')
  })

  it('prefers default slot over description prop when both are provided', () => {
    const wrapper = mount(BaseEmptyState, {
      props: { title: 'X', description: 'fallback' },
      slots: { default: 'Cuerpo personalizado' },
    })
    expect(wrapper.text()).toContain('Cuerpo personalizado')
    expect(wrapper.text()).not.toContain('fallback')
  })

  it('renders the icon slot above the title when provided', () => {
    const wrapper = mount(BaseEmptyState, {
      props: { title: 'X' },
      slots: { icon: '<svg data-testid="empty-icon" />' },
    })
    expect(wrapper.find('[data-testid="empty-icon"]').exists()).toBe(true)
  })

  it('renders the actions slot when provided', () => {
    const wrapper = mount(BaseEmptyState, {
      props: { title: 'X' },
      slots: { actions: '<button data-testid="cta">Crear</button>' },
    })
    expect(wrapper.find('[data-testid="cta"]').exists()).toBe(true)
  })
})
