import { mount } from '@vue/test-utils'
import BaseTooltip from '../../components/base/BaseTooltip.vue'

describe('BaseTooltip', () => {
  it('renders the trigger slot or a default question-mark icon', () => {
    const def = mount(BaseTooltip)
    expect(def.find('svg').exists()).toBe(true)

    const wrapper = mount(BaseTooltip, {
      slots: { trigger: '<button data-testid="trg">?</button>' },
    })
    expect(wrapper.find('[data-testid="trg"]').exists()).toBe(true)
  })

  it('hides the body until the trigger is interacted with', () => {
    const wrapper = mount(BaseTooltip, { slots: { default: 'Tip body' } })
    expect(wrapper.text()).not.toContain('Tip body')
  })

  it('shows the body on pointerenter (mouse)', async () => {
    const wrapper = mount(BaseTooltip, { slots: { default: 'Tip body' } })
    await wrapper.find('div.cursor-help').trigger('pointerenter', { pointerType: 'mouse' })
    expect(wrapper.text()).toContain('Tip body')
  })

  it('hides the body on pointerleave (mouse)', async () => {
    const wrapper = mount(BaseTooltip, { slots: { default: 'Tip body' } })
    const trigger = wrapper.find('div.cursor-help')
    await trigger.trigger('pointerenter', { pointerType: 'mouse' })
    await trigger.trigger('pointerleave', { pointerType: 'mouse' })
    expect(wrapper.text()).not.toContain('Tip body')
  })

  it('toggles on click (touch)', async () => {
    const wrapper = mount(BaseTooltip, { slots: { default: 'Tip body' } })
    const trigger = wrapper.find('div.cursor-help')
    await trigger.trigger('click')
    expect(wrapper.text()).toContain('Tip body')
    await trigger.trigger('click')
    expect(wrapper.text()).not.toContain('Tip body')
  })

  it.each([
    ['top', 'bottom-full'],
    ['bottom', 'top-full'],
    ['left', 'right-full'],
    ['right', 'left-full'],
  ])('positions body using %s placement classes', async (position, expected) => {
    const wrapper = mount(BaseTooltip, {
      props: { position },
      slots: { default: 'x' },
    })
    await wrapper.find('div.cursor-help').trigger('pointerenter', { pointerType: 'mouse' })
    const body = wrapper.findAll('div').find((d) => /absolute z-10/.test(d.attributes('class') || ''))
    expect(body).toBeDefined()
    expect(body.classes()).toContain(expected)
  })
})
