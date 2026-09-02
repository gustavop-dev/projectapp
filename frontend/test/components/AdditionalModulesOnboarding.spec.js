import { flushPromises, mount } from '@vue/test-utils'

import AdditionalModulesOnboarding from '../../components/AdditionalModules/Onboarding.vue'

global.useI18n = jest.fn(() => ({
  t: (key) => key,
}))

const STORAGE_KEY = 'projectapp-additional-modules-guide-seen'
const ALL_TARGETS = [
  'additional-modules-theme-toggle',
  'additional-modules-controls',
  'additional-modules-category-nav',
  'additional-module-entry',
  'additional-modules-share-btn',
  'additional-modules-pdf-fab',
  'additional-modules-restart-guide',
]

const BaseButtonStub = {
  inheritAttrs: false,
  props: ['type'],
  emits: ['click'],
  template: '<button v-bind="$attrs" :type="type || \'button\'" @click="$emit(\'click\', $event)"><slot /></button>',
}

let mountedWrappers = []

function addTargets(targets = ALL_TARGETS) {
  targets.forEach((className) => {
    const element = document.createElement('button')
    element.className = className
    document.body.appendChild(element)
  })
}

function mountOnboarding(props = {}) {
  const wrapper = mount(AdditionalModulesOnboarding, {
    props,
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

async function startGuide(wrapper) {
  wrapper.vm.start()
  await flushPromises()
  await wrapper.vm.$nextTick()
}

describe('AdditionalModulesOnboarding', () => {
  beforeEach(() => {
    mountedWrappers = []
    window.localStorage.clear()
    document.body.innerHTML = ''
  })

  afterEach(() => {
    mountedWrappers.forEach((wrapper) => wrapper.unmount())
    document.body.innerHTML = ''
  })

  it('starts with the catalog-specific theme explanation', async () => {
    addTargets()
    const wrapper = mountOnboarding()

    await startGuide(wrapper)

    expect(wrapper.get('[data-testid="additional-modules-guide-progress"]').text()).toBe('1/7')
    expect(wrapper.text()).toContain('additionalModules.guideThemeTitle')
  })

  it('does not repeat automatically after the guide was seen', async () => {
    addTargets()
    window.localStorage.setItem(STORAGE_KEY, 'true')
    const wrapper = mountOnboarding()

    await startGuide(wrapper)

    expect(wrapper.find('[data-testid="additional-modules-guide"]').exists()).toBe(false)
  })

  it('restarts on demand even after the guide was seen', async () => {
    addTargets()
    window.localStorage.setItem(STORAGE_KEY, 'true')
    const wrapper = mountOnboarding()

    wrapper.vm.forceStart()
    await flushPromises()

    expect(wrapper.find('[data-testid="additional-modules-guide"]').exists()).toBe(true)
    expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull()
  })

  it('advances and returns through the available steps', async () => {
    addTargets()
    const wrapper = mountOnboarding()
    await startGuide(wrapper)

    await wrapper.get('[data-testid="additional-modules-guide-next"]').trigger('click')
    expect(wrapper.get('[data-testid="additional-modules-guide-progress"]').text()).toBe('2/7')

    const backButton = wrapper.findAll('button')
      .find((button) => button.text() === 'additionalModules.guideBack')
    await backButton.trigger('click')

    expect(wrapper.get('[data-testid="additional-modules-guide-progress"]').text()).toBe('1/7')
  })

  it('uses only controls that exist in the current catalog view', async () => {
    addTargets(['additional-modules-theme-toggle', 'additional-modules-restart-guide'])
    const wrapper = mountOnboarding()

    await startGuide(wrapper)

    expect(wrapper.get('[data-testid="additional-modules-guide-progress"]').text()).toBe('1/2')
  })

  it('marks the guide as seen after completing its last available step', async () => {
    addTargets(['additional-modules-theme-toggle', 'additional-modules-restart-guide'])
    const wrapper = mountOnboarding()
    await startGuide(wrapper)

    await wrapper.get('[data-testid="additional-modules-guide-next"]').trigger('click')
    await wrapper.get('[data-testid="additional-modules-guide-done"]').trigger('click')

    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('true')
    expect(wrapper.find('[data-testid="additional-modules-guide"]').exists()).toBe(false)
    expect(wrapper.emitted('complete')).toHaveLength(1)
  })

  it('inherits dark mode inside the teleported guide', async () => {
    addTargets()
    const wrapper = mountOnboarding({ isDark: true })

    await startGuide(wrapper)

    expect(wrapper.get('[data-testid="additional-modules-guide"]').attributes('data-theme')).toBe('dark')
  })

  it('dismisses with Escape and remembers that choice', async () => {
    addTargets()
    const wrapper = mountOnboarding()
    await startGuide(wrapper)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-testid="additional-modules-guide"]').exists()).toBe(false)
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('true')
  })
})
