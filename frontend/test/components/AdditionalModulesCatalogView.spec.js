import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import AdditionalModulesCatalogView from '../../components/AdditionalModules/CatalogView.vue'

global.useI18n = jest.fn(() => ({
  t: (key, params = {}) => `${key}${params.name ? `:${params.name}` : ''}`,
}))

const moduleItem = {
  slug: 'electronic-invoicing',
  icon: '🧾',
  name: 'Facturación electrónica',
  summary: 'Emite documentos fiscales desde la plataforma.',
  what_is: 'Una integración fiscal.',
  purpose: 'Automatizar la emisión.',
  problems_solved: ['Evita digitación doble'],
  integrations: ['Proveedor autorizado'],
  implementation_requirements: ['Credenciales del proveedor'],
}

const categories = [{
  slug: 'commerce',
  name: 'Comercio y transacciones',
  modules: [moduleItem],
}]

const ModalStub = {
  props: ['modelValue'],
  template: '<div v-if="modelValue" data-testid="modal-stub"><slot /></div>',
}

function mountCatalog(props = {}) {
  document.body.innerHTML = ''
  return mount(AdditionalModulesCatalogView, {
    props: {
      categories,
      totalModules: 1,
      downloadUrl: '/api/catalog.pdf',
      ...props,
    },
    global: {
      stubs: {
        BaseAlert: { template: '<div role="alert"><slot /></div>' },
        BaseModal: ModalStub,
        BaseCard: { template: '<article><slot /></article>' },
        NuxtLink: { template: '<a><slot /></a>' },
      },
    },
    attachTo: document.body,
  })
}

describe('AdditionalModulesCatalogView', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('renders the one-screen category index without prices', () => {
    const wrapper = mountCatalog()

    expect(wrapper.text()).toContain('Comercio y transacciones')
    expect(wrapper.text()).toContain('Facturación electrónica')
    expect(wrapper.text()).toContain('Emite documentos fiscales')
    expect(wrapper.text()).not.toMatch(/\$|COP|USD/)
    expect(wrapper.get('[data-testid="additional-modules-download-pdf"]').element.tagName)
      .toBe('BUTTON')
  })

  it('opens all five content blocks in a modal', async () => {
    const wrapper = mountCatalog()

    await wrapper.get('[data-testid="additional-module-card-electronic-invoicing"]').trigger('click')

    const modal = wrapper.get('[data-testid="additional-module-detail-modal"]')
    expect(modal.text()).toContain('Una integración fiscal.')
    expect(modal.text()).toContain('Automatizar la emisión.')
    expect(modal.text()).toContain('Evita digitación doble')
    expect(modal.text()).toContain('Proveedor autorizado')
    expect(modal.text()).toContain('Credenciales del proveedor')
  })

  it('returns focus to the selected card after closing the modal', async () => {
    const wrapper = mountCatalog({ downloadUrl: '' })
    const card = wrapper.get('[data-testid="additional-module-card-electronic-invoicing"]')
    card.element.focus()
    await card.trigger('click')

    const closeButton = wrapper.get('[aria-label="additionalModules.close"]')
    await closeButton.trigger('click')
    await nextTick()

    expect(document.activeElement).toBe(card.element)
  })

  it('shows an explicit empty state when no active modules remain', () => {
    const wrapper = mountCatalog({ categories: [], totalModules: 0 })

    expect(wrapper.text()).toContain('additionalModules.emptyTitle')
    expect(wrapper.find('[data-testid^="additional-module-card-"]').exists()).toBe(false)
  })

  it('shows compact rows after selecting list view', async () => {
    const wrapper = mountCatalog()

    await wrapper.get('[data-testid="additional-view-list"]').trigger('click')

    expect(wrapper.get('[data-testid="additional-module-list-electronic-invoicing"]').text())
      .toContain('Facturación electrónica')
    expect(wrapper.find('[data-testid="additional-module-card-electronic-invoicing"]').exists())
      .toBe(false)
  })

  it('reveals module content from the accordion trigger', async () => {
    const wrapper = mountCatalog()
    await wrapper.get('[data-testid="additional-view-accordion"]').trigger('click')
    const trigger = wrapper.get('[data-testid="additional-module-accordion-trigger-electronic-invoicing"]')

    await trigger.trigger('click')

    expect(trigger.attributes('aria-expanded')).toBe('true')
    expect(wrapper.get('[data-testid="additional-module-accordion-electronic-invoicing"]').text())
      .toContain('Credenciales del proveedor')
  })

  it('requests the selected catalog language', async () => {
    const wrapper = mountCatalog({ language: 'es' })

    await wrapper.get('[data-testid="additional-language-en"]').trigger('click')

    expect(wrapper.emitted('change-language')).toEqual([['en']])
  })
})
