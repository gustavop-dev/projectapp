import { flushPromises, mount } from '@vue/test-utils'

import PublicGuidedTour from '../../components/PublicGuidedTour.vue'

const STORAGE_KEY = 'projectapp-tour-spec-seen'
const STEPS = [
  { target: '.tour-video', title: 'Video', description: 'Empieza por el video.', prefer: 'bottom' },
  { target: '.tour-options', title: 'Opciones', description: 'Compara las opciones.', prefer: 'bottom' },
  { target: '.tour-restart', title: 'Reinicio', description: 'Vuelve a abrir la guía.', prefer: 'right' },
]
const LABELS = { skip: 'Omitir', back: 'Atrás', next: 'Siguiente', done: 'Entendido' }

const BaseButtonStub = {
  inheritAttrs: false,
  props: ['type'],
  emits: ['click'],
  template: '<button v-bind="$attrs" :type="type || \'button\'" @click="$emit(\'click\', $event)"><slot /></button>',
}

let mountedWrappers = []

function addTargets(classes = STEPS.map((step) => step.target.slice(1))) {
  classes.forEach((className) => {
    const element = document.createElement('button')
    element.className = className
    document.body.appendChild(element)
  })
}

function mountTour(props = {}) {
  const wrapper = mount(PublicGuidedTour, {
    props: {
      steps: STEPS,
      labels: LABELS,
      storageKey: STORAGE_KEY,
      testIdPrefix: 'spec-guide',
      ...props,
    },
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

async function startTour(wrapper) {
  wrapper.vm.start()
  await flushPromises()
  await wrapper.vm.$nextTick()
}

describe('PublicGuidedTour', () => {
  beforeEach(() => {
    mountedWrappers = []
    window.localStorage.clear()
    document.body.innerHTML = ''
  })

  afterEach(() => {
    mountedWrappers.forEach((wrapper) => wrapper.unmount())
    document.body.innerHTML = ''
  })

  it('shows the first step with the owning view copy and test ids', async () => {
    addTargets()
    const wrapper = mountTour()

    await startTour(wrapper)

    const dialog = wrapper.get('[data-testid="spec-guide"]')
    expect(dialog.attributes('aria-labelledby')).toBe('spec-guide-title-0')
    expect(dialog.text()).toContain('Empieza por el video.')
    expect(wrapper.get('[data-testid="spec-guide-progress"]').text()).toBe('1/3')
    expect(wrapper.get('[data-testid="spec-guide-next"]').text()).toBe('Siguiente')
  })

  it('skips steps whose target is missing from the page', async () => {
    addTargets(['tour-options', 'tour-restart'])
    const wrapper = mountTour()

    await startTour(wrapper)

    expect(wrapper.get('[data-testid="spec-guide-progress"]').text()).toBe('1/2')
    expect(wrapper.text()).toContain('Opciones')
  })

  it('walks forward and back and finishes with the done label', async () => {
    addTargets()
    const wrapper = mountTour()
    await startTour(wrapper)

    await wrapper.get('[data-testid="spec-guide-next"]').trigger('click')
    expect(wrapper.get('[data-testid="spec-guide-progress"]').text()).toBe('2/3')

    const back = wrapper.findAll('button').find((button) => button.text() === 'Atrás')
    await back.trigger('click')
    expect(wrapper.get('[data-testid="spec-guide-progress"]').text()).toBe('1/3')

    await wrapper.get('[data-testid="spec-guide-next"]').trigger('click')
    await wrapper.get('[data-testid="spec-guide-next"]').trigger('click')
    await wrapper.get('[data-testid="spec-guide-done"]').trigger('click')

    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('true')
    expect(wrapper.emitted('complete')).toHaveLength(1)
    expect(wrapper.find('[data-testid="spec-guide"]').exists()).toBe(false)
  })

  it('does not auto-start once the storage key is set but restarts on demand', async () => {
    addTargets()
    window.localStorage.setItem(STORAGE_KEY, 'true')
    const wrapper = mountTour()

    await startTour(wrapper)
    expect(wrapper.find('[data-testid="spec-guide"]').exists()).toBe(false)

    wrapper.vm.forceStart()
    await flushPromises()

    expect(wrapper.find('[data-testid="spec-guide"]').exists()).toBe(true)
    expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull()
  })

  it('closes with Escape, remembers it and applies the dark theme', async () => {
    addTargets()
    const wrapper = mountTour({ isDark: true })
    await startTour(wrapper)
    expect(wrapper.get('[data-testid="spec-guide"]').attributes('data-theme')).toBe('dark')

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-testid="spec-guide"]').exists()).toBe(false)
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('true')
  })
})
