/**
 * Tests for useDocumentFilterQuery (persistencia de carpeta/scope en la URL).
 */
import {
  effectScope, reactive, ref, nextTick,
} from 'vue'

// Reactiva a propósito: el composable observa la ruta en los dos sentidos, y
// con un objeto plano el watcher de atrás/adelante no llegaría a dispararse.
const mockRoute = reactive({ query: {} })
const mockReplace = jest.fn()

jest.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => ({ replace: mockReplace }),
}))

const { useDocumentFilterQuery } = require('../../composables/useDocumentFilterQuery')

describe('useDocumentFilterQuery', () => {
  let store
  let scope

  function setupFilterQuery(options) {
    return scope.run(() => useDocumentFilterQuery(store, options))
  }

  beforeEach(() => {
    scope = effectScope()
    store = reactive({
      activeFolderId: 'all', archiveScope: 'active',
      activeTagIds: [], archivedOrder: 'recent',
      activeClientId: null, activeProjectId: null,
    })
    mockRoute.query = {}
    mockReplace.mockClear()
    // Como el router real: replace deja el query visible en la ruta.
    mockReplace.mockImplementation(({ query }) => { mockRoute.query = query })
  })

  afterEach(() => scope.stop())

  it('applies ?folder and ?scope from the query to the store', () => {
    mockRoute.query = { folder: '5', scope: 'archived' }

    const { applyQueryToStore } = setupFilterQuery()
    applyQueryToStore()

    expect(store.activeFolderId).toBe(5)
    expect(store.archiveScope).toBe('archived')
  })

  it('keeps the pseudo folders as strings when applying the query', () => {
    mockRoute.query = { folder: 'none' }

    const { applyQueryToStore } = setupFilterQuery()
    applyQueryToStore()

    expect(store.activeFolderId).toBe('none')
  })

  it('ignores garbage values in the query, and scrubs them from the url', () => {
    mockRoute.query = { folder: 'DROP TABLE', scope: 'bogus' }

    const { applyQueryToStore } = setupFilterQuery()
    applyQueryToStore()

    expect(store.activeFolderId).toBe('all')
    expect(store.archiveScope).toBe('active')
    // La URL reproduce la vista: si el valor no se aplicó, no puede quedarse.
    expect(mockReplace).toHaveBeenCalledWith({ query: {} })
  })

  it('resets a stale store when the url is clean', () => {
    // El store sobrevive a salir del módulo: volver por el menú (URL sin query)
    // dejaba la carpeta de la visita anterior seleccionada bajo un «Todos».
    store.activeFolderId = 7
    store.archiveScope = 'archived'
    mockRoute.query = {}

    const { applyQueryToStore } = setupFilterQuery()
    const summary = applyQueryToStore()

    expect(summary.changed).toBe(true)
    expect(store.activeFolderId).toBe('all')
    expect(store.archiveScope).toBe('active')
  })

  it('drops a hand-typed default out of the url', () => {
    mockRoute.query = { scope: 'active' }

    const { applyQueryToStore } = setupFilterQuery()
    applyQueryToStore()

    expect(mockReplace).toHaveBeenCalledWith({ query: {} })
  })

  it('follows the browser back and forward buttons', async () => {
    const onNavigate = jest.fn()
    setupFilterQuery({ onNavigate })

    // Lo que hace un popstate: cambia la URL sin pasar por el store.
    mockRoute.query = { folder: '9', scope: 'archived' }
    await nextTick()

    expect(store.activeFolderId).toBe(9)
    expect(store.archiveScope).toBe('archived')
    expect(onNavigate).toHaveBeenCalledTimes(1)
  })

  it('does not refetch when the url change came from the store itself', async () => {
    const onNavigate = jest.fn()
    setupFilterQuery({ onNavigate })

    store.activeFolderId = 3
    await nextTick()
    await nextTick()

    expect(mockRoute.query).toEqual({ folder: '3' })
    expect(onNavigate).not.toHaveBeenCalled()
  })

  it('applies filtering and search state from the query', () => {
    const searchQuery = ref('')
    mockRoute.query = {
      folder: '9', scope: 'archived', tags: '8,3,8', client: '4',
      project: 'none', q: '  factura  ', order: 'oldest',
    }

    const { applyQueryToStore } = setupFilterQuery({ searchQuery })
    applyQueryToStore()

    expect(store.activeFolderId).toBe(9)
    expect(store.archiveScope).toBe('archived')
    expect(store.activeTagIds).toEqual([3, 8])
    expect(store.activeClientId).toBe(4)
    expect(store.activeProjectId).toBe('none')
    expect(store.archivedOrder).toBe('oldest')
    expect(searchQuery.value).toBe('factura')
  })

  it('applies presentation and focus state from the query', () => {
    const viewMode = ref('list')
    const currentPage = ref(1)
    const focusedDocumentId = ref(null)
    mockRoute.query = { view: 'grid', page: '3', focus: '42' }

    const { applyQueryToStore } = setupFilterQuery({
      viewMode, currentPage, focusedDocumentId,
    })
    applyQueryToStore()

    expect(viewMode.value).toBe('grid')
    expect(currentPage.value).toBe(3)
    expect(focusedDocumentId.value).toBe(42)
  })

  it('follows browser history for the complete list state', async () => {
    const onNavigate = jest.fn()
    const searchQuery = ref('')
    const currentPage = ref(1)
    const focusedDocumentId = ref(null)
    setupFilterQuery({
      searchQuery, currentPage, focusedDocumentId, onNavigate,
    })

    mockRoute.query = { q: 'Acme', page: '2', focus: '17' }
    await nextTick()

    expect(searchQuery.value).toBe('Acme')
    expect(currentPage.value).toBe(2)
    expect(focusedDocumentId.value).toBe(17)
    expect(onNavigate).toHaveBeenCalledWith(expect.objectContaining({
      searchChanged: true, pageChanged: true, focusChanged: true,
    }))
  })

  it('writes state changes to the url with replace, omitting the defaults', async () => {
    setupFilterQuery()

    store.activeFolderId = 7
    store.archiveScope = 'archived'
    await nextTick()

    expect(mockReplace).toHaveBeenCalledWith({ query: { folder: '7', scope: 'archived' } })

    // Volver al reposo limpia la URL en vez de dejar defaults colgando.
    store.activeFolderId = 'all'
    store.archiveScope = 'active'
    await nextTick()

    expect(mockReplace).toHaveBeenLastCalledWith({ query: {} })
  })

  it('writes search state without changing its origin scope', async () => {
    const searchQuery = ref('')
    setupFilterQuery({ searchQuery })

    store.archiveScope = 'archived'
    searchQuery.value = 'contrato'
    await nextTick()

    expect(mockRoute.query).toEqual({ scope: 'archived', q: 'contrato' })
    expect(store.archiveScope).toBe('archived')
  })

  it('writes presentation state while omitting defaults', async () => {
    const viewMode = ref('list')
    const currentPage = ref(1)
    const focusedDocumentId = ref(null)
    setupFilterQuery({ viewMode, currentPage, focusedDocumentId })

    viewMode.value = 'grid'
    currentPage.value = 4
    focusedDocumentId.value = 23
    await nextTick()

    expect(mockRoute.query).toEqual({ view: 'grid', page: '4', focus: '23' })

    viewMode.value = 'list'
    currentPage.value = 1
    focusedDocumentId.value = null
    await nextTick()

    expect(mockRoute.query).toEqual({})
  })

  it('canonicalizes tag ids in the url', async () => {
    setupFilterQuery()

    store.activeTagIds = [8, 3, 8]
    await nextTick()

    expect(mockRoute.query).toEqual({ tags: '3,8' })
  })

  it('validateFolder falls back to all when the folder no longer exists', () => {
    store.activeFolderId = 99
    const { validateFolder } = setupFilterQuery()

    const changed = validateFolder({ folderById: () => null })

    expect(changed).toBe(true)
    expect(store.activeFolderId).toBe('all')
  })

  it('validateFolder leaves an existing folder untouched', () => {
    store.activeFolderId = 4
    const { validateFolder } = setupFilterQuery()

    const changed = validateFolder({ folderById: (id) => ({ id }) })

    expect(changed).toBe(false)
    expect(store.activeFolderId).toBe(4)
  })

  it('applies the ?client and ?project association axes from the query', () => {
    mockRoute.query = { client: '4', project: 'none' }

    const { applyQueryToStore } = setupFilterQuery()
    applyQueryToStore()

    expect(store.activeClientId).toBe(4)
    expect(store.activeProjectId).toBe('none')
  })

  it('scrubs garbage association values from the url', () => {
    mockRoute.query = { client: 'abc' }

    const { applyQueryToStore } = setupFilterQuery()
    applyQueryToStore()

    expect(store.activeClientId).toBeNull()
    expect(mockReplace).toHaveBeenCalledWith({ query: {} })
  })

  it('writes the association axes to the url and clears them when off', async () => {
    setupFilterQuery()

    store.activeClientId = 'none'
    await nextTick()
    expect(mockRoute.query).toEqual({ client: 'none' })

    store.activeClientId = null
    await nextTick()
    expect(mockRoute.query).toEqual({})
  })

  it('back and forward with an association param reach the store', async () => {
    const onNavigate = jest.fn()
    setupFilterQuery({ onNavigate })

    mockRoute.query = { client: '7' }
    await nextTick()

    expect(store.activeClientId).toBe(7)
    expect(onNavigate).toHaveBeenCalledTimes(1)
  })
})
