import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
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

  it('keeps a forced status visible without hover or focus', async () => {
    const wrapper = mount(BaseTooltip, {
      props: { text: 'Copiado', forceOpen: true },
    })
    expect(wrapper.get('[role="tooltip"]').text()).toContain('Copiado')

    await wrapper.setProps({ forceOpen: false })
    expect(wrapper.find('[role="tooltip"]').exists()).toBe(false)
  })

  it('positions an initially forced floating status', async () => {
    const wrapper = mount(BaseTooltip, {
      attachTo: document.body,
      props: { text: 'Copiado', forceOpen: true, floating: true },
    })
    await nextTick()

    const tooltip = document.body.querySelector('[role="tooltip"]')
    expect(tooltip.style.visibility).toBe('visible')
    wrapper.unmount()
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

  it('keeps the body open when hover and focus precede the first click', async () => {
    const wrapper = mount(BaseTooltip, {
      slots: {
        trigger: '<button data-testid="trg">?</button>',
        default: 'Tip body',
      },
    })
    const triggerBox = wrapper.find('div.cursor-help')
    await triggerBox.trigger('pointerenter', { pointerType: 'mouse' })
    await wrapper.get('[data-testid="trg"]').trigger('focusin')
    await wrapper.get('[data-testid="trg"]').trigger('click')

    expect(wrapper.text()).toContain('Tip body')
  })

  it('shows on keyboard focus and exposes tooltip semantics', async () => {
    const wrapper = mount(BaseTooltip, {
      props: { text: 'Accessible tip' },
      slots: { trigger: '<button data-testid="trg">Action</button>' },
    })
    await wrapper.get('[data-testid="trg"]').trigger('focusin')
    const tooltip = wrapper.get('[role="tooltip"]')
    expect(tooltip.text()).toContain('Accessible tip')
    expect(tooltip.attributes('id')).toBeTruthy()
  })

  it('hides when keyboard focus leaves the trigger', async () => {
    const wrapper = mount(BaseTooltip, {
      props: { text: 'Tip body' },
      slots: { trigger: '<button data-testid="trg">Action</button>' },
    })
    await wrapper.get('[data-testid="trg"]').trigger('focusin')
    await wrapper.get('[data-testid="trg"]').trigger('focusout', { relatedTarget: document.body })
    expect(wrapper.find('[role="tooltip"]').exists()).toBe(false)
  })

  it('does not toggle or swallow clicks for an executable action', async () => {
    const wrapper = mount(BaseTooltip, {
      props: { text: 'Tip body', toggleOnClick: false },
      slots: { trigger: '<button data-testid="trg">Action</button>' },
    })
    await wrapper.get('[data-testid="trg"]').trigger('click')
    expect(wrapper.find('[role="tooltip"]').exists()).toBe(false)
  })

  it('does not open when tooltip behavior is disabled', async () => {
    const wrapper = mount(BaseTooltip, {
      props: { disabled: true },
      slots: {
        trigger: '<button type="button">Acción</button>',
        default: 'Motivo del bloqueo',
      },
    })

    await wrapper.get('button').trigger('pointerenter', { pointerType: 'mouse' })
    await wrapper.get('button').trigger('click')

    expect(wrapper.get('button').text()).toBe('Acción')
    expect(wrapper.text()).not.toContain('Motivo del bloqueo')
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

  it('places a floating body inside the viewport', async () => {
    Object.defineProperties(window, {
      innerWidth: { configurable: true, value: 100 },
      innerHeight: { configurable: true, value: 80 },
    })
    const wrapper = mount(BaseTooltip, {
      attachTo: document.body,
      props: {
        floating: true,
        position: 'top',
        text: 'A complete document title',
        width: 'max-w-none',
        minWidth: 'min-w-0',
      },
      slots: { trigger: '<button data-testid="trg">Action</button>' },
    })
    const trigger = wrapper.get('[data-base-tooltip-trigger]')
    trigger.element.getBoundingClientRect = () => ({
      top: 2, right: 20, bottom: 22, left: 0, width: 20, height: 20,
    })

    await trigger.trigger('pointerenter', { pointerType: 'mouse' })
    await nextTick()
    const body = document.body.querySelector('[role="tooltip"]')
    body.getBoundingClientRect = () => ({
      top: 0, right: 80, bottom: 30, left: 0, width: 80, height: 30,
    })
    window.dispatchEvent(new Event('resize'))
    await nextTick()

    expect(body.classList).toContain('fixed')
    expect(body.style.top).toBe('30px')
    expect(body.style.left).toBe('8px')
    expect(body.style.visibility).toBe('visible')
    wrapper.unmount()
  })

  it('does not create a positioning boundary for a floating trigger', () => {
    const wrapper = mount(BaseTooltip, {
      props: { floating: true },
      slots: { trigger: '<button>Action</button>' },
    })

    expect(wrapper.get('[data-base-tooltip-trigger]').text()).toContain('Action')
    expect(wrapper.classes()).not.toContain('relative')
  })

  it('removes a teleported body when unmounted', async () => {
    const wrapper = mount(BaseTooltip, {
      attachTo: document.body,
      props: { floating: true, text: 'Temporary tip' },
    })
    await wrapper.get('[data-base-tooltip-trigger]')
      .trigger('pointerenter', { pointerType: 'mouse' })
    expect(document.body.querySelector('[role="tooltip"]')?.textContent).toContain('Temporary tip')

    wrapper.unmount()

    expect(document.body.querySelector('[role="tooltip"]')).toBeNull()
  })
})
