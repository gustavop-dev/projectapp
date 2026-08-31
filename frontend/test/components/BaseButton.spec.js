import { mount } from '@vue/test-utils'
import BaseButton from '../../components/base/BaseButton.vue'

describe('BaseButton', () => {
  it('renders a <button type="button"> by default with default-slot content', () => {
    const wrapper = mount(BaseButton, { slots: { default: 'Guardar' } })
    const btn = wrapper.find('button')
    expect(btn.exists()).toBe(true)
    expect(btn.attributes('type')).toBe('button')
    expect(btn.text()).toBe('Guardar')
  })

  it.each([
    ['primary', 'bg-primary'],
    ['secondary', 'bg-surface'],
    ['ghost', 'bg-transparent'],
    ['danger', 'bg-danger-strong'],
    ['danger-ghost', 'text-danger-strong'],
    ['link', 'text-text-brand'],
    ['accent', 'bg-accent'],
  ])('applies %s variant tokens', (variant, expected) => {
    const wrapper = mount(BaseButton, { props: { variant }, slots: { default: 'x' } })
    expect(wrapper.find('button').classes()).toContain(expected)
  })

  // The filled variants must use the on-* foreground tokens, not text-white:
  // --color-danger-strong flips to a light red in dark mode, so hardcoded
  // white would render unreadable there.
  it.each([
    ['primary', 'text-on-primary'],
    ['danger', 'text-on-danger'],
  ])('uses the on-* foreground token for %s instead of text-white', (variant, expected) => {
    const cls = mount(BaseButton, { props: { variant }, slots: { default: 'x' } })
      .find('button').classes()
    expect(cls).toContain(expected)
    expect(cls).not.toContain('text-white')
  })

  it('renders danger-ghost without a filled background so inline deletes stay quiet', () => {
    const cls = mount(BaseButton, { props: { variant: 'danger-ghost' }, slots: { default: 'x' } })
      .find('button').classes()
    expect(cls).toContain('bg-transparent')
    expect(cls).toContain('hover:bg-danger-soft')
    expect(cls).not.toContain('bg-danger-strong')
  })

  it.each([
    ['sm', 'text-xs'],
    ['md', 'text-sm'],
    ['lg', 'text-base'],
  ])('applies %s size', (size, expected) => {
    const wrapper = mount(BaseButton, { props: { size }, slots: { default: 'x' } })
    expect(wrapper.find('button').classes()).toContain(expected)
  })

  it('swaps rectangular padding for square padding when iconOnly is set', () => {
    const cls = mount(BaseButton, {
      props: { iconOnly: true },
      attrs: { 'aria-label': 'Eliminar' },
      slots: { default: '<svg />' },
    }).find('button').classes()
    expect(cls).toContain('p-2')
    expect(cls).not.toContain('px-4')
    expect(cls).not.toContain('py-2')
    expect(cls).toContain('base-button--icon')
  })

  it('renders link variant as bare text with no padding or radius', () => {
    const cls = mount(BaseButton, { props: { variant: 'link' }, slots: { default: 'Ver todos' } })
      .find('button').classes()
    expect(cls).toContain('hover:underline')
    expect(cls.some((c) => c.startsWith('px-') || c.startsWith('py-'))).toBe(false)
    expect(cls.some((c) => c.startsWith('rounded'))).toBe(false)
    expect(cls).toContain('base-button--link')
  })

  it('preserves bespoke visual classes in unstyled mode', () => {
    const classes = mount(BaseButton, {
      props: { iconOnly: true, unstyled: true },
      attrs: { 'aria-label': 'Compartir', class: 'custom-floating-control' },
    }).get('button').classes()

    expect(classes).toContain('custom-floating-control')
    expect(classes).toContain('base-button--icon')
    expect(classes).not.toContain('bg-primary')
    expect(classes).not.toContain('p-2')
  })

  describe('iconOnly accessibility warning', () => {
    let warn

    // Vue itself warns about NuxtLink being unresolvable in this environment,
    // so assert on our own message rather than on the call count.
    const a11yWarning = expect.stringContaining('aria-label')

    beforeEach(() => {
      warn = jest.spyOn(console, 'warn').mockImplementation(() => {})
    })

    afterEach(() => {
      warn.mockRestore()
    })

    it('warns when an iconOnly button has no accessible name', () => {
      mount(BaseButton, { props: { iconOnly: true }, slots: { default: '<svg />' } })
      expect(warn).toHaveBeenCalledWith(a11yWarning)
    })

    it('stays silent when an iconOnly button carries an aria-label', () => {
      mount(BaseButton, {
        props: { iconOnly: true },
        attrs: { 'aria-label': 'Eliminar' },
        slots: { default: '<svg />' },
      })
      expect(warn).not.toHaveBeenCalledWith(a11yWarning)
    })

    it('stays silent for a normal button with visible text', () => {
      mount(BaseButton, { slots: { default: 'Guardar' } })
      expect(warn).not.toHaveBeenCalledWith(a11yWarning)
    })
  })

  it('emits click when pressed', async () => {
    const wrapper = mount(BaseButton, { slots: { default: 'x' } })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
  })

  describe('icon activation feedback', () => {
    beforeEach(() => jest.useFakeTimers())
    afterEach(() => jest.useRealTimers())

    it('keeps an icon visibly active for a short interval after click', async () => {
      const wrapper = mount(BaseButton, {
        props: { iconOnly: true },
        attrs: { 'aria-label': 'Copiar' },
        slots: { default: '<svg />' },
      })

      await wrapper.get('button').trigger('click')
      expect(wrapper.get('button').attributes('data-activation-state')).toBe('active')

      jest.advanceTimersByTime(180)
      await wrapper.vm.$nextTick()
      expect(wrapper.get('button').attributes('data-activation-state')).toBe('idle')
    })

    it('does not add activation state to text buttons', async () => {
      const wrapper = mount(BaseButton, { slots: { default: 'Guardar' } })
      await wrapper.get('button').trigger('click')
      expect(wrapper.get('button').attributes('data-activation-state')).toBeUndefined()
    })

    it('does not activate a loading icon control', async () => {
      const wrapper = mount(BaseButton, {
        props: { iconOnly: true, loading: true },
        attrs: { 'aria-label': 'Actualizar' },
      })
      await wrapper.get('button').trigger('click')
      expect(wrapper.get('button').attributes('data-activation-state')).toBe('idle')
    })

    it('clears the activation timer on unmount', async () => {
      const wrapper = mount(BaseButton, {
        props: { iconOnly: true },
        attrs: { 'aria-label': 'Abrir' },
      })
      await wrapper.get('button').trigger('click')
      wrapper.unmount()
      expect(jest.getTimerCount()).toBe(0)
    })
  })

  it('disables the button when disabled prop is true', () => {
    const wrapper = mount(BaseButton, { props: { disabled: true }, slots: { default: 'x' } })
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })

  it('puts the semantic disabled reason on the native button', () => {
    const wrapper = mount(BaseButton, {
      props: {
        disabled: true,
        disabledReason: 'Selecciona un cliente antes de continuar.',
      },
      slots: { default: 'Continuar' },
    })

    expect(wrapper.get('button').attributes('title'))
      .toBe('Selecciona un cliente antes de continuar.')
  })

  it('preserves an explicit native hint by default', () => {
    const wrapper = mount(BaseButton, {
      attrs: { title: 'Ayuda contextual' },
      slots: { default: 'Continuar' },
    })

    expect(wrapper.get('button').attributes('title')).toBe('Ayuda contextual')
  })

  it('suppresses the native title for an owning tooltip primitive', () => {
    const wrapper = mount(BaseButton, {
      props: {
        disabled: true,
        disabledReason: 'Selecciona un cliente antes de continuar.',
        nativeTitle: false,
      },
      attrs: { title: 'Ayuda nativa duplicada' },
      slots: { default: 'Continuar' },
    })

    expect(wrapper.get('button').attributes('title')).toBeUndefined()
  })

  it('renders a spinner and disables the button when loading is true', () => {
    const wrapper = mount(BaseButton, { props: { loading: true }, slots: { default: 'Guardando' } })
    expect(wrapper.find('svg').exists()).toBe(true)
    expect(wrapper.find('svg').classes()).toContain('animate-spin')
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })

  it('renders the spinner only when loading is true', () => {
    const wrapper = mount(BaseButton, { slots: { default: 'x' } })
    expect(wrapper.find('svg').exists()).toBe(false)
  })

  it('respects type prop on button element', () => {
    const wrapper = mount(BaseButton, { props: { type: 'submit' }, slots: { default: 'x' } })
    expect(wrapper.find('button').attributes('type')).toBe('submit')
  })

  it('renders as a different element when "as" prop is used and omits type', () => {
    const wrapper = mount(BaseButton, {
      props: { as: 'a', type: 'submit' },
      slots: { default: 'x' },
    })
    expect(wrapper.element.tagName).toBe('A')
    expect(wrapper.attributes('type')).toBeUndefined()
  })

  it('always includes focus-ring token class', () => {
    const wrapper = mount(BaseButton, { slots: { default: 'x' } })
    const cls = wrapper.find('button').attributes('class') || ''
    expect(cls).toContain('focus:ring-focus-ring/40')
  })

  it('keeps icon and short text atomic by default', () => {
    const wrapper = mount(BaseButton, {
      slots: { default: '<svg data-testid="icon" /> Guardar cambios' },
    })

    expect(wrapper.get('button').classes()).toEqual(
      expect.arrayContaining(['flex-nowrap', 'whitespace-nowrap']),
    )
  })

  it('allows a sentence-like action to wrap explicitly', () => {
    const wrapper = mount(BaseButton, {
      props: { textPolicy: 'wrap' },
      slots: { default: 'Continuar aunque falten datos opcionales' },
    })

    expect(wrapper.get('button').classes()).toContain('whitespace-normal')
  })
})
