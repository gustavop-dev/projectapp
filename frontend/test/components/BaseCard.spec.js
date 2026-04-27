import { mount } from '@vue/test-utils'
import BaseCard from '../../components/base/BaseCard.vue'

describe('BaseCard', () => {
  it('renders default slot inside a div with surface tokens', () => {
    const wrapper = mount(BaseCard, { slots: { default: '<p>hola</p>' } })
    expect(wrapper.element.tagName).toBe('DIV')
    expect(wrapper.html()).toContain('<p>hola</p>')
    const cls = wrapper.classes()
    expect(cls).toContain('bg-surface')
    expect(cls).toContain('border-border-muted')
    expect(cls).toContain('rounded-xl')
  })

  it.each([
    ['none', ''],
    ['sm', 'p-3'],
    ['md', 'p-5'],
    ['lg', 'p-7'],
  ])('applies padding=%s', (padding, expected) => {
    const wrapper = mount(BaseCard, { props: { padding }, slots: { default: 'x' } })
    if (!expected) {
      expect(wrapper.classes().some((c) => /^p-\d+$/.test(c))).toBe(false)
    } else {
      expect(wrapper.classes()).toContain(expected)
    }
  })

  it('respects "as" prop to render a different tag', () => {
    const wrapper = mount(BaseCard, { props: { as: 'section' }, slots: { default: 'x' } })
    expect(wrapper.element.tagName).toBe('SECTION')
  })
})
