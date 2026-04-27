import { mount } from '@vue/test-utils'

// Approach A: Mock @headlessui/vue so we can render-test the Menu/MenuButton/
// MenuItems/MenuItem wiring without driving Headless UI's internal composables
// (which require focus management, provide/inject, etc. and are hard to exercise
// in jsdom). The toggle behavior is owned by Headless UI and out of scope here;
// we only verify how BaseDropdown shapes its slots, items, classes, and events.
jest.mock('@headlessui/vue', () => ({
  Menu: {
    name: 'Menu',
    props: ['as'],
    template: '<div class="hl-menu"><slot /></div>',
  },
  MenuButton: {
    name: 'MenuButton',
    props: ['as'],
    template: '<button class="hl-menu-button" type="button"><slot /></button>',
  },
  MenuItems: {
    name: 'MenuItems',
    template: '<div class="hl-menu-items"><slot /></div>',
  },
  MenuItem: {
    name: 'MenuItem',
    props: ['disabled'],
    // Expose `active=false` and `disabled=props.disabled` to the scoped slot,
    // mirroring Headless UI's signature so BaseDropdown's `v-slot="{ active, disabled }"`
    // continues to work as in production.
    template: '<div class="hl-menu-item"><slot :active="false" :disabled="disabled || false" /></div>',
  },
}))

import BaseDropdown from '../../components/base/BaseDropdown.vue'

const NuxtLink = {
  name: 'NuxtLink',
  props: ['to'],
  template: '<a class="nuxt-link" :href="typeof to === \'string\' ? to : \'#\'"><slot /></a>',
}

const FakeIcon = {
  name: 'FakeIcon',
  template: '<svg class="fake-icon" />',
}

function mountDropdown(props = {}, slots = {}) {
  return mount(BaseDropdown, {
    props,
    slots: { trigger: '<button class="t-btn">Open</button>', ...slots },
    global: { components: { NuxtLink } },
  })
}

describe('BaseDropdown', () => {
  it('renders the #trigger slot inside MenuButton', () => {
    const wrapper = mountDropdown({ items: [] })
    const button = wrapper.find('.hl-menu-button')
    expect(button.exists()).toBe(true)
    expect(button.find('.t-btn').exists()).toBe(true)
    expect(button.find('.t-btn').text()).toBe('Open')
  })

  it('renders one item per entry in items', () => {
    const items = [
      { label: 'One', onClick: () => {} },
      { label: 'Two', onClick: () => {} },
      { label: 'Three', onClick: () => {} },
    ]
    const wrapper = mountDropdown({ items })
    const menuItems = wrapper.findAll('.hl-menu-item')
    expect(menuItems).toHaveLength(3)
    expect(menuItems[0].text()).toContain('One')
    expect(menuItems[2].text()).toContain('Three')
  })

  it('renders divider items as a separator <div> instead of a MenuItem', () => {
    const items = [
      { label: 'A', onClick: () => {} },
      { divider: true },
      { label: 'B', onClick: () => {} },
    ]
    const wrapper = mountDropdown({ items })
    expect(wrapper.findAll('.hl-menu-item')).toHaveLength(2)
    const divider = wrapper.find('.hl-menu-items > div.border-t')
    expect(divider.exists()).toBe(true)
    expect(divider.classes()).toContain('border-border-muted')
  })

  it('applies danger token class to items flagged danger', () => {
    const items = [{ label: 'Eliminar', danger: true, onClick: () => {} }]
    const wrapper = mountDropdown({ items })
    const inner = wrapper.find('.hl-menu-item button')
    expect(inner.classes()).toContain('text-danger-strong')
  })

  it('applies disabled visual classes when MenuItem reports disabled', () => {
    const items = [{ label: 'Off', disabled: true, onClick: () => {} }]
    const wrapper = mountDropdown({ items })
    const inner = wrapper.find('.hl-menu-item button')
    expect(inner.classes()).toContain('opacity-50')
    expect(inner.classes()).toContain('cursor-not-allowed')
  })

  it('renders an item with `to` as NuxtLink and one without `to` as <button type="button">', () => {
    const items = [
      { label: 'Go', to: '/somewhere' },
      { label: 'Act', onClick: () => {} },
    ]
    const wrapper = mountDropdown({ items })
    // First item -> NuxtLink stub renders an <a>
    const link = wrapper.findComponent(NuxtLink)
    expect(link.exists()).toBe(true)
    expect(link.props('to')).toBe('/somewhere')
    // Second item -> native <button type="button">
    const buttons = wrapper.findAll('.hl-menu-item button')
    // The trigger button is outside .hl-menu-item, so this scope only catches
    // item buttons. Exactly one item-as-button is expected here.
    expect(buttons).toHaveLength(1)
    expect(buttons[0].attributes('type')).toBe('button')
    expect(buttons[0].text()).toContain('Act')
  })

  it('invokes onClick when an item is clicked', async () => {
    const onClick = jest.fn()
    const items = [{ label: 'Tap', onClick }]
    const wrapper = mountDropdown({ items })
    await wrapper.find('.hl-menu-item button').trigger('click')
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('renders the icon component when item.icon is provided', () => {
    const items = [{ label: 'With icon', icon: FakeIcon, onClick: () => {} }]
    const wrapper = mountDropdown({ items })
    expect(wrapper.findComponent(FakeIcon).exists()).toBe(true)
    expect(wrapper.find('.fake-icon').exists()).toBe(true)
  })

  it('aligns to the right by default with right-0 origin-top-right', () => {
    const wrapper = mountDropdown({ items: [{ label: 'A', onClick: () => {} }] })
    const items = wrapper.find('.hl-menu-items')
    const cls = items.attributes('class') || ''
    expect(cls).toContain('right-0')
    expect(cls).toContain('origin-top-right')
    expect(cls).not.toContain('left-0')
  })

  it('aligns to the left when align="left" with left-0 origin-top-left', () => {
    const wrapper = mountDropdown({
      items: [{ label: 'A', onClick: () => {} }],
      align: 'left',
    })
    const cls = wrapper.find('.hl-menu-items').attributes('class') || ''
    expect(cls).toContain('left-0')
    expect(cls).toContain('origin-top-left')
    expect(cls).not.toContain('right-0')
  })

  it('passes the width prop through as a class on MenuItems', () => {
    const wrapper = mountDropdown({
      items: [{ label: 'A', onClick: () => {} }],
      width: 'w-72',
    })
    const cls = wrapper.find('.hl-menu-items').attributes('class') || ''
    expect(cls).toContain('w-72')
  })
})
