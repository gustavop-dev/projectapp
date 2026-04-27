import { mount } from '@vue/test-utils'
import BaseTabs from '../../components/base/BaseTabs.vue'

jest.mock('~/utils/selectArrowStyle', () => ({ SELECT_ARROW_STYLE: '' }), { virtual: true })

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'details', label: 'Details', badge: 3 },
  { id: 'history', label: 'History', disabled: true },
]

describe('BaseTabs', () => {
  it('renders one button per tab and one option per tab', () => {
    const wrapper = mount(BaseTabs, { props: { modelValue: 'overview', tabs } })
    expect(wrapper.findAll('button')).toHaveLength(3)
    expect(wrapper.findAll('option')).toHaveLength(3)
  })

  it('marks the active tab with aria-selected and brand classes (underline)', () => {
    const wrapper = mount(BaseTabs, { props: { modelValue: 'details', tabs } })
    const buttons = wrapper.findAll('button')
    expect(buttons[0].attributes('aria-selected')).toBe('false')
    expect(buttons[1].attributes('aria-selected')).toBe('true')
    expect(buttons[1].classes()).toContain('border-text-brand')
    expect(buttons[1].classes()).toContain('text-text-brand')
  })

  it('uses pill styling when variant=pill', () => {
    const wrapper = mount(BaseTabs, { props: { modelValue: 'overview', tabs, variant: 'pill' } })
    const tablist = wrapper.find('[role="tablist"]')
    expect(tablist.classes()).toContain('bg-surface-raised')
    const active = wrapper.findAll('button')[0]
    expect(active.classes()).toContain('bg-surface')
  })

  it('emits update:modelValue when a tab is clicked', async () => {
    const wrapper = mount(BaseTabs, { props: { modelValue: 'overview', tabs } })
    await wrapper.findAll('button')[1].trigger('click')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['details'])
  })

  it('does not emit when a disabled tab is clicked', async () => {
    const wrapper = mount(BaseTabs, { props: { modelValue: 'overview', tabs } })
    await wrapper.findAll('button')[2].trigger('click')
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })

  it('renders badge content when present', () => {
    const wrapper = mount(BaseTabs, { props: { modelValue: 'overview', tabs } })
    expect(wrapper.findAll('button')[1].text()).toContain('3')
  })

  it('emits via the mobile select on change', async () => {
    const wrapper = mount(BaseTabs, { props: { modelValue: 'overview', tabs } })
    await wrapper.find('select').setValue('details')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['details'])
  })
})
