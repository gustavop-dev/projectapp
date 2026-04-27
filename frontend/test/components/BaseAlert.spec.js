import { mount } from '@vue/test-utils'
import BaseAlert from '../../components/base/BaseAlert.vue'

describe('BaseAlert', () => {
  it('renders default slot inside role=alert with info variant by default', () => {
    const wrapper = mount(BaseAlert, { slots: { default: 'Mensaje informativo' } })
    const alert = wrapper.find('[role="alert"]')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toContain('Mensaje informativo')
    expect(alert.classes()).toContain('bg-primary-soft')
  })

  it.each([
    ['success', 'bg-success-soft', 'text-success-strong'],
    ['warning', 'bg-warning-soft', 'text-warning-strong'],
    ['danger', 'bg-danger-soft', 'text-danger-strong'],
  ])('applies %s variant tokens', (variant, bg, text) => {
    const wrapper = mount(BaseAlert, { props: { variant }, slots: { default: 'x' } })
    const alert = wrapper.find('[role="alert"]')
    expect(alert.classes()).toContain(bg)
    expect(alert.classes()).toContain(text)
  })

  it('renders title above default slot when title prop is set', () => {
    const wrapper = mount(BaseAlert, {
      props: { title: 'Atención' },
      slots: { default: 'Cuerpo del alerta' },
    })
    const title = wrapper.find('p')
    expect(title.text()).toBe('Atención')
    expect(wrapper.text()).toContain('Cuerpo del alerta')
  })

  it('does not render dismiss button by default', () => {
    const wrapper = mount(BaseAlert, { slots: { default: 'x' } })
    expect(wrapper.find('button[aria-label="Cerrar"]').exists()).toBe(false)
  })

  it('emits dismiss when the close button is clicked', async () => {
    const wrapper = mount(BaseAlert, { props: { dismissible: true }, slots: { default: 'x' } })
    await wrapper.find('button[aria-label="Cerrar"]').trigger('click')
    expect(wrapper.emitted('dismiss')).toBeTruthy()
  })

  it('renders the icon slot when provided', () => {
    const wrapper = mount(BaseAlert, {
      slots: { default: 'x', icon: '<svg data-testid="alert-icon" />' },
    })
    expect(wrapper.find('[data-testid="alert-icon"]').exists()).toBe(true)
  })
})
