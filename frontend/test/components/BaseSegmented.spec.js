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

  it('accepts string options too', () => {
    const wrapper = mount(BaseSegmented, { props: { modelValue: 'a', options: ['a', 'b', 'c'] } })
    const buttons = wrapper.findAll('button')
    expect(buttons).toHaveLength(3)
    expect(buttons[2].text()).toBe('c')
  })
})
