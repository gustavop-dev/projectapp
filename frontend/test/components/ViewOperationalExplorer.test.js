import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ViewOperationalExplorer from '../../components/views/ViewOperationalExplorer.vue'

const BaseButtonStub = {
  emits: ['click'],
  template: '<button type="button" @click="$emit(\'click\', $event)"><slot /></button>',
}

const BaseActionButtonStub = {
  props: ['action', 'label'],
  emits: ['click'],
  template: '<button type="button" :data-action="action" @click="$emit(\'click\', $event)">{{ label }}</button>',
}

const BaseBadgeStub = { template: '<span><slot /></span>' }

function mountExplorer(props = {}) {
  return mount(ViewOperationalExplorer, {
    props: {
      selectedNodeId: null,
      showRelations: true,
      ...props,
    },
    global: {
      stubs: {
        BaseButton: BaseButtonStub,
        BaseActionButton: BaseActionButtonStub,
        BaseBadge: BaseBadgeStub,
        BaseActionIcon: true,
      },
    },
  })
}

describe('ViewOperationalExplorer', () => {
  beforeEach(() => {
    window.requestAnimationFrame = jest.fn(() => 1)
    window.cancelAnimationFrame = jest.fn()
    window.matchMedia = jest.fn(() => ({
      matches: false,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    }))
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('renders every high-level business domain', () => {
    const wrapper = mountExplorer()

    expect(wrapper.findAll('[data-testid^="view-explorer-node-"]')).toHaveLength(7)
    expect(wrapper.text()).toContain('Presencia digital')
    expect(wrapper.text()).toContain('Plataforma de clientes')
    expect(wrapper.text()).toContain('104 vistas relacionadas')
  })

  it('selects a domain from the orbit', async () => {
    const wrapper = mountExplorer()

    await wrapper.get('[data-testid="view-explorer-node-client-platform"]').trigger('click')

    expect(wrapper.emitted('select')).toEqual([['client-platform']])
  })

  it('renders the Platform capability ring', () => {
    const wrapper = mountExplorer({ selectedNodeId: 'client-platform' })

    expect(wrapper.findAll('[data-testid^="view-explorer-node-"]')).toHaveLength(8)
    expect(wrapper.text()).toContain('Seguimiento del trabajo')
  })

  it('draws the curated Platform relationships', () => {
    const wrapper = mountExplorer({ selectedNodeId: 'client-platform' })

    expect(wrapper.findAll('[data-testid="view-explorer-relation"]')).toHaveLength(9)
  })

  it('toggles the relationship layer', async () => {
    const wrapper = mountExplorer({ selectedNodeId: 'client-platform' })

    await wrapper.get('[data-testid="view-explorer-relations-toggle"]').trigger('click')

    expect(wrapper.emitted('update:showRelations')).toEqual([[false]])
  })

  it('finds a capability by its commercial benefit', async () => {
    const wrapper = mountExplorer()

    await wrapper.get('#view-explorer-search').setValue('aprobación trazable')

    expect(wrapper.get('[data-testid="view-explorer-search-results"]').text())
      .toContain('Documentos y aprobaciones')
  })

  it('opens a capability from search results', async () => {
    const wrapper = mountExplorer()
    await wrapper.get('#view-explorer-search').setValue('aprobación trazable')

    await wrapper.get('[data-testid="view-explorer-search-results"] button').trigger('click')

    expect(wrapper.emitted('select')).toEqual([['platform-documents']])
  })

  it('shows the technical reference below a feature', () => {
    const wrapper = mountExplorer({ selectedNodeId: 'platform-document-portal' })

    expect(wrapper.get('[data-testid="view-explorer-detail"]').text()).toContain('Qué permite hacer')
    expect(wrapper.get('[data-testid="view-explorer-detail"]').text()).toContain('/platform/documents')
  })

  it('opens a shallow domain in Map mode', async () => {
    const wrapper = mountExplorer({ selectedNodeId: 'public-site' })

    await wrapper.get('[data-testid="view-explorer-detail"] button').trigger('click')

    expect(wrapper.emitted('open-map')).toEqual([['public-site']])
  })

  it('explains when reduced motion disables automatic rotation', async () => {
    window.matchMedia = jest.fn(() => ({
      matches: true,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    }))

    const wrapper = mountExplorer()
    await nextTick()

    expect(wrapper.text()).toContain('desactivado por tu preferencia de movimiento reducido')
  })

  it('clears an unknown node from URL state', () => {
    const wrapper = mountExplorer({ selectedNodeId: 'unknown-capability' })

    expect(wrapper.emitted('select')).toEqual([[null]])
  })
})
