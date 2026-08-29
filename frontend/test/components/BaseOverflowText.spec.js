import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'

import BaseOverflowText from '../../components/base/BaseOverflowText.vue'

const NuxtLinkStub = {
  template: '<a :href="to" v-bind="$attrs"><slot /></a>',
  props: ['to'],
}

const originalFontsDescriptor = Object.getOwnPropertyDescriptor(document, 'fonts')

function restoreDocumentFonts() {
  if (originalFontsDescriptor) {
    Object.defineProperty(document, 'fonts', originalFontsDescriptor)
    return
  }
  delete document.fonts
}

function mountText(props = {}) {
  return mount(BaseOverflowText, {
    props: {
      text: 'Contrato de servicios para Cliente Atlas con destinatario final',
      to: '/panel/documents/1/edit',
      lines: 2,
      testId: 'document-title',
      ...props,
    },
    global: { stubs: { NuxtLink: NuxtLinkStub } },
  })
}

async function setOverflow(wrapper, overflowing) {
  const el = wrapper.get('[data-testid="document-title"]').element
  Object.defineProperties(el, {
    clientWidth: { configurable: true, value: 240 },
    scrollWidth: { configurable: true, value: 240 },
    clientHeight: { configurable: true, value: 40 },
    scrollHeight: { configurable: true, value: overflowing ? 80 : 40 },
  })
  window.dispatchEvent(new Event('resize'))
  await nextTick()
  await nextTick()
}

describe('BaseOverflowText', () => {
  afterEach(restoreDocumentFonts)

  it('constrains an unbroken real document name to the available width', () => {
    const wrapper = mountText({ text: 'Levantamiento_Fase_4_Multi-Tenant_24082026' })
    const content = wrapper.get('[data-testid="document-title"]')

    expect(content.classes()).toEqual(expect.arrayContaining([
      'w-full', 'min-w-0', 'max-w-full', '[overflow-wrap:anywhere]',
    ]))
    expect(content.classes()).not.toContain('break-words')
  })

  it('keeps the full hover hint without adding disclosure for a complete title', async () => {
    const wrapper = mountText()
    await setOverflow(wrapper, false)

    expect(wrapper.get('[data-testid="document-title"]').attributes('title'))
      .toBe('Contrato de servicios para Cliente Atlas con destinatario final')
    expect(wrapper.find('[data-testid="document-title-toggle"]').exists()).toBe(false)
  })

  it('adds the full title only after clipping', async () => {
    const wrapper = mountText()
    await setOverflow(wrapper, true)

    expect(wrapper.get('[data-testid="document-title"]').attributes('title'))
      .toBe('Contrato de servicios para Cliente Atlas con destinatario final')
    expect(wrapper.get('[data-testid="document-title-toggle"]').text()).toContain('Ver completo')
  })

  it('reveals the complete title in place', async () => {
    const wrapper = mountText()
    await setOverflow(wrapper, true)

    await wrapper.get('[data-testid="document-title-toggle"]').trigger('click')

    expect(wrapper.get('[data-testid="document-title-toggle"]').attributes('aria-expanded')).toBe('true')
    expect(wrapper.get('[data-testid="document-title-toggle"]').text()).toContain('Contraer')
    expect(wrapper.get('[data-testid="document-title"]').attributes('title')).toBeUndefined()
  })

  it('remeasures clipping after document fonts finish loading', async () => {
    let resolveFonts
    const ready = new Promise((resolve) => { resolveFonts = resolve })
    Object.defineProperty(document, 'fonts', {
      configurable: true,
      value: { ready },
    })
    const wrapper = mountText()
    await nextTick()
    await nextTick()

    const el = wrapper.get('[data-testid="document-title"]').element
    Object.defineProperties(el, {
      clientWidth: { configurable: true, value: 240 },
      scrollWidth: { configurable: true, value: 420 },
      clientHeight: { configurable: true, value: 40 },
      scrollHeight: { configurable: true, value: 40 },
    })

    resolveFonts()
    await flushPromises()
    await nextTick()

    expect(wrapper.get('[data-testid="document-title-toggle"]').text()).toContain('Ver completo')
  })

  it('publishes the document link while clipped', async () => {
    const wrapper = mountText()
    await setOverflow(wrapper, true)

    expect(wrapper.get('[data-testid="document-title"]').attributes('href'))
      .toBe('/panel/documents/1/edit')
  })
})
