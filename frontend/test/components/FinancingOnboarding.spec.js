import { flushPromises, mount } from '@vue/test-utils'

import FinancingOnboarding from '../../components/Financing/Onboarding.vue'

global.useI18n = jest.fn(() => ({
  t: (key) => key,
}))

const STORAGE_KEY = 'projectapp-financing-guide-seen'

const BaseButtonStub = {
  inheritAttrs: false,
  props: ['type'],
  emits: ['click'],
  template: '<button v-bind="$attrs" :type="type || \'button\'" @click="$emit(\'click\', $event)"><slot /></button>',
}

let mountedWrappers = []

function addTargets({ explainer = true } = {}) {
  const nodes = [
    ['button', 'financing-explainer', null],
    ['article', null, 'financing-option-five-year'],
    ['nav', 'financing-conditions-nav', null],
    ['div', null, 'financing-calculator-input-output'],
    ['dl', null, 'financing-package-facts'],
    ['div', 'financing-terms', null],
    ['button', null, 'financing-download-pdf-floating'],
    ['button', 'financing-restart-guide', null],
  ]
  nodes.forEach(([tag, className, testId]) => {
    if (!explainer && className === 'financing-explainer') return
    const element = document.createElement(tag)
    if (className) element.className = className
    if (testId) element.setAttribute('data-testid', testId)
    document.body.appendChild(element)
  })
}

function mountOnboarding(props = {}) {
  const wrapper = mount(FinancingOnboarding, {
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

describe('FinancingOnboarding', () => {
  beforeEach(() => {
    mountedWrappers = []
    window.localStorage.clear()
    document.body.innerHTML = ''
  })

  afterEach(() => {
    mountedWrappers.forEach((wrapper) => wrapper.unmount())
    document.body.innerHTML = ''
  })

  it('starts with the explainer video and covers the eight financing controls', async () => {
    addTargets()
    const wrapper = mountOnboarding()

    await startGuide(wrapper)

    expect(wrapper.get('[data-testid="financing-guide-progress"]').text()).toBe('1/8')
    expect(wrapper.text()).toContain('financing.guideExplainerTitle')
    expect(wrapper.get('[data-testid="financing-guide-next"]').text()).toBe('financing.guideNext')
  })

  it('opens on the partnership options when the video is not rendered', async () => {
    addTargets({ explainer: false })
    const wrapper = mountOnboarding()

    await startGuide(wrapper)

    expect(wrapper.get('[data-testid="financing-guide-progress"]').text()).toBe('1/7')
    expect(wrapper.text()).toContain('financing.guideOptionsTitle')
  })

  it('advances through the steps and marks the guide as seen at the end', async () => {
    addTargets()
    const wrapper = mountOnboarding()
    await startGuide(wrapper)

    await wrapper.get('[data-testid="financing-guide-next"]').trigger('click')
    expect(wrapper.get('[data-testid="financing-guide-progress"]').text()).toBe('2/8')
    expect(wrapper.text()).toContain('financing.guideOptionsTitle')

    for (let step = 2; step < 8; step += 1) {
      await wrapper.get('[data-testid="financing-guide-next"]').trigger('click')
    }
    await wrapper.get('[data-testid="financing-guide-done"]').trigger('click')

    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('true')
    expect(wrapper.emitted('complete')).toHaveLength(1)
  })

  it('stays closed after being seen and reopens through forceStart', async () => {
    addTargets()
    window.localStorage.setItem(STORAGE_KEY, 'true')
    const wrapper = mountOnboarding()

    await startGuide(wrapper)
    expect(wrapper.find('[data-testid="financing-guide"]').exists()).toBe(false)

    wrapper.vm.forceStart()
    await flushPromises()

    expect(wrapper.find('[data-testid="financing-guide"]').exists()).toBe(true)
  })
})
