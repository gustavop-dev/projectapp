const { reactive, ref, nextTick } = require('vue')

const routerReplace = jest.fn()
let routeQuery = {}
const originalGlobals = {
  definePageMeta: global.definePageMeta,
  useI18n: global.useI18n,
  useRoute: global.useRoute,
  useRouter: global.useRouter,
}
const mockStore = reactive({
  resources: [],
  sources: [],
  records: [],
  count: 0,
  pageSize: 25,
  detail: null,
  loading: false,
  saving: false,
  error: '',
  requestId: 0,
  list: jest.fn(),
  catalog: jest.fn(),
  close: jest.fn(),
  open: jest.fn(),
  note: jest.fn(),
  transition: jest.fn(),
})

global.definePageMeta = jest.fn()
global.useI18n = () => ({ t: key => key, locale: ref('es-CO') })
global.useRoute = () => ({ query: routeQuery })
global.useRouter = () => ({ replace: routerReplace })

jest.mock('../../stores/monitoring', () => ({
  useMonitoringStore: () => mockStore,
}))

const { mount, flushPromises } = require('@vue/test-utils')
const PanelMonitoringIndex = require('../../pages/panel/monitoring/index.vue').default

const BaseSelectStub = {
  props: ['id', 'options'],
  template: '<output :data-testid="`${id}-options`">{{ options.map(option => `${option.value}:${option.label}`).join("|") }}</output>',
}

const BaseButtonStub = {
  emits: ['click'],
  template: '<button role="button" type="button" @click="$emit(\'click\', $event)"><slot /></button>',
}

function defaultStubs() {
  return {
    BaseButton: BaseButtonStub,
    BaseFormField: { template: '<div><slot /></div>' },
    BaseInput: { template: '<input />' },
    BaseModal: { template: '<div><slot /></div>' },
    BaseModalActions: { template: '<div><slot /></div>' },
    BaseSelect: BaseSelectStub,
    BaseTextarea: { template: '<textarea />' },
  }
}

function mountPage() {
  return mount(PanelMonitoringIndex, { global: { stubs: defaultStubs() } })
}

function resource(id, name, kind) {
  return { id, name, kind }
}

function source(id, resourceId, resourceName, name, lastSeenAt = '2026-09-24T10:00:00Z') {
  return {
    id,
    resource: resourceId,
    resource_name: resourceName,
    name,
    health: 'current',
    last_seen_at: lastSeenAt,
    last_error: '',
  }
}

function buttonWithLabel(wrapper, label) {
  return wrapper.findAll('[role="button"]').find(button => button.text() === label)
}

describe('panel/monitoring index page', () => {
  let wrapper

  beforeEach(() => {
    routeQuery = {}
    routerReplace.mockReset().mockResolvedValue(undefined)
    mockStore.resources = []
    mockStore.sources = []
    mockStore.records = []
    mockStore.count = 0
    mockStore.pageSize = 25
    mockStore.detail = null
    mockStore.loading = false
    mockStore.saving = false
    mockStore.error = ''
    mockStore.requestId = 0
    mockStore.list.mockReset().mockResolvedValue(undefined)
    mockStore.catalog.mockReset().mockResolvedValue(undefined)
    mockStore.close.mockReset()
    mockStore.open.mockReset().mockResolvedValue(undefined)
    mockStore.note.mockReset().mockResolvedValue(undefined)
    mockStore.transition.mockReset().mockResolvedValue(undefined)
    jest.useFakeTimers()
  })

  afterEach(() => {
    wrapper?.unmount()
    jest.useRealTimers()
  })

  afterAll(() => {
    Object.entries(originalGlobals).forEach(([key, value]) => {
      if (value === undefined) delete global[key]
      else global[key] = value
    })
  })

  it('keeps the project source when a query resource id has the other primitive type', async () => {
    // Falla si el filtro de recurso deja de comparar sus ids como texto o si el tab acepta una fuente de otro tipo.
    routeQuery = { resource: '1' }
    mockStore.resources = [
      resource(1, 'Proyecto Uno', 'project'),
      resource(1, 'Servidor duplicado', 'server'),
      resource('1', 'Servidor Uno', 'server'),
    ]
    mockStore.sources = [
      source(11, 1, 'Proyecto Uno', 'Inspector'),
      source(12, '1', 'Servidor Uno', 'Healthcheck'),
      source(13, 99, 'Huérfano', 'Archivo'),
    ]
    wrapper = mountPage()
    await flushPromises()

    expect(wrapper.get('[data-testid="monitor-resource-options"]').text()).toBe(':monitoring.any|1:Proyecto Uno')
    expect(wrapper.get('[data-testid="monitor-source-options"]').text()).toBe(':monitoring.any|11:Proyecto Uno · Inspector')
  })

  it('updates project options after a catalog resource changes kind', async () => {
    // Falla si el índice de recursos queda en caché después de que el catálogo cambia de tipo.
    mockStore.resources = [
      resource(1, 'Proyecto Uno', 'project'),
      resource(2, 'Servidor Uno', 'server'),
    ]
    mockStore.sources = [
      source(11, 1, 'Proyecto Uno', 'Inspector'),
      source(12, 2, 'Servidor Uno', 'Healthcheck'),
    ]
    wrapper = mountPage()
    await flushPromises()
    mockStore.resources[0].kind = 'server'
    await nextTick()

    expect(wrapper.get('[data-testid="monitor-resource-options"]').text()).toBe(':monitoring.any')
    expect(wrapper.get('[data-testid="monitor-source-options"]').text()).toBe(':monitoring.any')
  })

  it('lists project, server, and orphan sources in reports', async () => {
    // Falla si Reports conserva la partición del tab Project y oculta fuentes que deben revisarse juntas.
    mockStore.resources = [
      resource(1, 'Proyecto Uno', 'project'),
      resource(2, 'Servidor Uno', 'server'),
    ]
    mockStore.sources = [
      source(11, 1, 'Proyecto Uno', 'Inspector'),
      source(12, 2, 'Servidor Uno', 'Healthcheck'),
      source(13, 99, 'Huérfano', 'Archivo'),
    ]
    wrapper = mountPage()
    await flushPromises()
    await buttonWithLabel(wrapper, 'monitoring.reports').trigger('click')
    await flushPromises()

    expect(wrapper.get('[data-testid="monitor-resource-options"]').text()).toBe(':monitoring.any|1:Proyecto Uno|2:Servidor Uno')
    expect(wrapper.get('[data-testid="monitor-source-options"]').text()).toBe(':monitoring.any|11:Proyecto Uno · Inspector|12:Servidor Uno · Healthcheck|13:Huérfano · Archivo')
  })

  it('does not reread resource ids when sources grow from one to ten thousand', async () => {
    // Falla si filtrar fuentes vuelve a recorrer ids de recursos para cada una de las diez mil entradas.
    const idReads = jest.fn()
    mockStore.resources = Array.from({ length: 50 }, (_, index) => {
      const item = { name: `Recurso ${index + 1}`, kind: 'project' }
      Object.defineProperty(item, 'id', {
        enumerable: true,
        get: () => {
          idReads()
          return index + 1
        },
      })
      return item
    })
    mockStore.sources = [source(51, 1, 'Recurso 1', 'Inspector')]
    wrapper = mountPage()
    await flushPromises()
    expect(wrapper.get('[data-testid="monitor-source-options"]').text()).toBe(':monitoring.any|51:Recurso 1 · Inspector')
    const baselineReads = idReads.mock.calls.length
    expect(baselineReads).toBeLessThanOrEqual(100)
    mockStore.sources = [
      source(51, 1, 'Recurso 1', 'Inspector'),
      ...Array.from({ length: 9999 }, (_, index) => source(index + 52, -1, 'Fuera del catálogo', `Archivo ${index + 1}`, null)),
    ]
    await nextTick()

    expect(wrapper.get('[data-testid="monitor-source-options"]').text()).toBe(':monitoring.any|51:Recurso 1 · Inspector')
    expect(idReads).toHaveBeenCalledTimes(baselineReads)
  })
})
