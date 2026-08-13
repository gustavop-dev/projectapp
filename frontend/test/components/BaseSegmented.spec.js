import { mount } from '@vue/test-utils'
import BaseSegmented from '../../components/base/BaseSegmented.vue'

const opts = [
  { value: 'editor', label: 'Editor', testId: 'sg-editor' },
  { value: 'json', label: 'JSON', testId: 'sg-json' },
]

describe('BaseSegmented', () => {
  it('renders one button per option with the given label and testId', () => {
    const wrapper = mount(BaseSegmented, { props: { modelValue: 'editor', options: opts } })
    const buttons = wrapper.findAll('button')
    expect(buttons).toHaveLength(2)
    expect(buttons[0].text()).toBe('Editor')
    expect(buttons[0].attributes('data-testid')).toBe('sg-editor')
    expect(buttons[1].attributes('data-testid')).toBe('sg-json')
  })

  it('marks the active option with aria-selected and surface styling', () => {
    const wrapper = mount(BaseSegmented, { props: { modelValue: 'json', options: opts } })
    const [editor, json] = wrapper.findAll('button')
    expect(editor.attributes('aria-selected')).toBe('false')
    expect(json.attributes('aria-selected')).toBe('true')
    expect(json.classes()).toContain('bg-surface')
    expect(editor.classes()).toContain('text-text-muted')
  })

  it('emits update:modelValue with the option value when clicked', async () => {
    const wrapper = mount(BaseSegmented, { props: { modelValue: 'editor', options: opts } })
    await wrapper.findAll('button')[1].trigger('click')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['json'])
  })

  it('lets multi-word labels wrap by default', () => {
    const wrapper = mount(BaseSegmented, {
      props: { modelValue: 'COL', options: [{ value: 'COL', label: 'Colombia (COP)' }] },
    })
    expect(wrapper.findAll('button')[0].classes()).not.toContain('whitespace-nowrap')
    expect(wrapper.find('[role="tablist"]').classes()).not.toContain('overflow-x-auto')
  })

  it('keeps labels on a single line when nowrap is set, scrolling instead of breaking', () => {
    const wrapper = mount(BaseSegmented, {
      props: { modelValue: 'COL', options: [{ value: 'COL', label: 'Colombia (COP)' }], nowrap: true },
    })
    expect(wrapper.findAll('button')[0].classes()).toContain('whitespace-nowrap')
    // The container absorbs the extra width so the page never gains a scrollbar.
    expect(wrapper.find('[role="tablist"]').classes()).toEqual(
      expect.arrayContaining(['max-w-full', 'overflow-x-auto']),
    )
  })

  it('locks a single option without touching the others', async () => {
    const wrapper = mount(BaseSegmented, {
      props: {
        modelValue: 'json',
        options: [{ ...opts[0], disabled: true }, opts[1]],
      },
    })
    const [editor, json] = wrapper.findAll('button')

    expect(editor.element.disabled).toBe(true)
    expect(editor.classes()).toContain('cursor-not-allowed')
    await editor.trigger('click')
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()

    // The rest of the control stays live — that is the whole point of the flag.
    expect(json.element.disabled).toBe(false)
    await json.trigger('click')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['json'])
  })

  it('still disables every option when the control itself is disabled', async () => {
    const wrapper = mount(BaseSegmented, {
      props: { modelValue: 'editor', options: opts, disabled: true },
    })
    const buttons = wrapper.findAll('button')
    expect(buttons.map((b) => b.element.disabled)).toEqual([true, true])
    await buttons[1].trigger('click')
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })

  it('accepts string options too', () => {
    const wrapper = mount(BaseSegmented, { props: { modelValue: 'a', options: ['a', 'b', 'c'] } })
    const buttons = wrapper.findAll('button')
    expect(buttons).toHaveLength(3)
    expect(buttons[2].text()).toBe('c')
  })
})
