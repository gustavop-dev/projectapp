import { flushPromises, mount } from '@vue/test-utils'

import AdditionalModulesShareButton from '../../components/AdditionalModules/ShareButton.vue'

global.useI18n = jest.fn(() => ({
  t: (key) => key,
}))

const BaseButtonStub = {
  inheritAttrs: false,
  props: ['type'],
  emits: ['click'],
  template: '<button v-bind="$attrs" :type="type || \'button\'" @click="$emit(\'click\', $event)"><slot /></button>',
}

let mountedWrappers = []

function mountShareButton(props = {}) {
  const wrapper = mount(AdditionalModulesShareButton, {
    props,
    attachTo: document.body,
    global: {
      stubs: {
        BaseButton: BaseButtonStub,
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  })
  mountedWrappers.push(wrapper)
  return wrapper
}

describe('AdditionalModulesShareButton', () => {
  beforeEach(() => {
    mountedWrappers = []
    window.history.replaceState({}, '', '/es-co/additional-modules/share/current-token')
    Object.defineProperty(window.navigator, 'clipboard', {
      configurable: true,
      value: { writeText: jest.fn().mockResolvedValue(undefined) },
    })
    Object.defineProperty(window.navigator, 'share', {
      configurable: true,
      value: undefined,
    })
  })

  afterEach(() => {
    mountedWrappers.forEach((wrapper) => wrapper.unmount())
    document.body.innerHTML = ''
  })

  it('opens a dark-themed dialog with the current selection URL', async () => {
    const wrapper = mountShareButton({ isDark: true })

    await wrapper.get('[data-testid="additional-modules-share-floating"]').trigger('click')

    expect(wrapper.get('[data-testid="additional-modules-share-dialog"]').attributes('data-theme')).toBe('dark')
    expect(wrapper.get('[data-testid="additional-modules-share-url"]').text())
      .toBe('http://localhost/es-co/additional-modules/share/current-token')
  })

  it('copies the unchanged current URL and confirms success', async () => {
    const wrapper = mountShareButton()
    await wrapper.get('[data-testid="additional-modules-share-floating"]').trigger('click')

    await wrapper.get('[data-testid="additional-modules-copy-link"]').trigger('click')
    await flushPromises()

    expect(window.navigator.clipboard.writeText)
      .toHaveBeenCalledWith('http://localhost/es-co/additional-modules/share/current-token')
    expect(wrapper.get('[data-testid="additional-modules-share-feedback"]').attributes('role')).toBe('status')
  })

  it('moves focus into the dialog and returns it to the floating action', async () => {
    const wrapper = mountShareButton()
    const trigger = wrapper.get('[data-testid="additional-modules-share-floating"]')
    trigger.element.focus()

    await trigger.trigger('click')
    await flushPromises()

    expect(document.activeElement).toBe(wrapper.get('[data-testid="additional-modules-copy-link"]').element)
    await wrapper.get('[aria-label="additionalModules.close"]').trigger('click')
    await flushPromises()
    expect(document.activeElement).toBe(trigger.element)
  })

  it('shows an explicit error when clipboard access fails', async () => {
    window.navigator.clipboard.writeText.mockRejectedValue(new Error('denied'))
    const wrapper = mountShareButton()
    await wrapper.get('[data-testid="additional-modules-share-floating"]').trigger('click')

    await wrapper.get('[data-testid="additional-modules-copy-link"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('[data-testid="additional-modules-share-feedback"]').attributes('role')).toBe('alert')
    expect(wrapper.get('[data-testid="additional-modules-share-feedback"]').text())
      .toBe('additionalModules.copyFailed')
  })

  it('passes the current URL to the native share sheet', async () => {
    const nativeShare = jest.fn().mockResolvedValue(undefined)
    Object.defineProperty(window.navigator, 'share', {
      configurable: true,
      value: nativeShare,
    })
    const wrapper = mountShareButton()
    await wrapper.get('[data-testid="additional-modules-share-floating"]').trigger('click')

    await wrapper.get('[data-testid="additional-modules-native-share"]').trigger('click')

    expect(nativeShare).toHaveBeenCalledWith(expect.objectContaining({
      url: 'http://localhost/es-co/additional-modules/share/current-token',
    }))
  })

  it('closes the dialog with Escape', async () => {
    const wrapper = mountShareButton()
    await wrapper.get('[data-testid="additional-modules-share-floating"]').trigger('click')

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-testid="additional-modules-share-dialog"]').exists()).toBe(false)
  })
})
