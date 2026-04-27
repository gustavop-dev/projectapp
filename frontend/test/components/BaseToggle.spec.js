import { mount } from '@vue/test-utils'
import BaseToggle from '../../components/base/BaseToggle.vue'

describe('BaseToggle', () => {
  it('renders with role=switch and aria-checked reflecting modelValue', () => {
    const wrapper = mount(BaseToggle, { props: { modelValue: true } })
    const btn = wrapper.find('button')
    expect(btn.attributes('role')).toBe('switch')
    expect(btn.attributes('aria-checked')).toBe('true')
  })

  it('shows primary background when on, raised surface when off', () => {
    const on = mount(BaseToggle, { props: { modelValue: true } })
    expect(on.find('button').classes()).toContain('bg-primary')

    const off = mount(BaseToggle, { props: { modelValue: false } })
    expect(off.find('button').classes()).toContain('bg-surface-raised')
  })

  it('emits update:modelValue with the inverted value on click', async () => {
    const wrapper = mount(BaseToggle, { props: { modelValue: false } })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([true])
  })

  it('does not emit when disabled', async () => {
    const wrapper = mount(BaseToggle, { props: { modelValue: false, disabled: true } })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })

  it('translates the thumb when on', () => {
    const wrapper = mount(BaseToggle, { props: { modelValue: true } })
    const thumb = wrapper.find('span')
    expect(thumb.classes()).toContain('translate-x-5')
  })

  it('honors onClass / offClass overrides for status semantics', () => {
    const on = mount(BaseToggle, {
      props: { modelValue: true, onClass: 'bg-warning-strong', offClass: 'bg-primary' },
    })
    expect(on.find('button').classes()).toContain('bg-warning-strong')

    const off = mount(BaseToggle, {
      props: { modelValue: false, onClass: 'bg-warning-strong', offClass: 'bg-primary' },
    })
    expect(off.find('button').classes()).toContain('bg-primary')
  })
})
