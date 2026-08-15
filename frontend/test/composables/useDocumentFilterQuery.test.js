/**
 * Tests for useDocumentFilterQuery (persistencia de carpeta/scope en la URL).
 */
import { reactive, ref, nextTick } from 'vue'

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

  beforeEach(() => {
    store = reactive({ activeFolderId: 'all', archiveScope: 'active' })
    mockRoute.query = {}
    mockReplace.mockClear()
    // Como el router real: replace deja el query visible en la ruta.
    mockReplace.mockImplementation(({ query }) => { mockRoute.query = query })
  })

  it('applies ?folder and ?scope from the query to the store', () => {
    mockRoute.query = { folder: '5', scope: 'archived' }

    const { applyQueryToStore } = useDocumentFilterQuery(store)
    applyQueryToStore()

    expect(store.activeFolderId).toBe(5)
    expect(store.archiveScope).toBe('archived')
  })

  it('keeps the pseudo folders as strings when applying the query', () => {
    mockRoute.query = { folder: 'none' }

    const { applyQueryToStore } = useDocumentFilterQuery(store)
    applyQueryToStore()

    expect(store.activeFolderId).toBe('none')
  })

  it('ignores garbage values in the query, and scrubs them from the url', () => {
    mockRoute.query = { folder: 'DROP TABLE', scope: 'bogus' }

    const { applyQueryToStore } = useDocumentFilterQuery(store)
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

    const { applyQueryToStore } = useDocumentFilterQuery(store)
    const changed = applyQueryToStore()

    expect(changed).toBe(true)
    expect(store.activeFolderId).toBe('all')
    expect(store.archiveScope).toBe('active')
  })

  it('drops a hand-typed default out of the url', () => {
    mockRoute.query = { scope: 'active' }

    const { applyQueryToStore } = useDocumentFilterQuery(store)
    applyQueryToStore()

    expect(mockReplace).toHaveBeenCalledWith({ query: {} })
  })

  it('follows the browser back and forward buttons', async () => {
    const onNavigate = jest.fn()
    useDocumentFilterQuery(store, { onNavigate })

    // Lo que hace un popstate: cambia la URL sin pasar por el store.
    mockRoute.query = { folder: '9', scope: 'archived' }
    await nextTick()

    expect(store.activeFolderId).toBe(9)
    expect(store.archiveScope).toBe('archived')
    expect(onNavigate).toHaveBeenCalledTimes(1)
  })

  it('does not refetch when the url change came from the store itself', async () => {
    const onNavigate = jest.fn()
    useDocumentFilterQuery(store, { onNavigate })

    store.activeFolderId = 3
    await nextTick()
    await nextTick()

    expect(mockRoute.query).toEqual({ folder: '3' })
    expect(onNavigate).not.toHaveBeenCalled()
  })

  it('leaves the view alone while a search is running', async () => {
    const onNavigate = jest.fn()
    useDocumentFilterQuery(store, { isSearching: ref(true), onNavigate })

    mockRoute.query = { folder: '9' }
    await nextTick()

    expect(store.activeFolderId).toBe('all')
    expect(onNavigate).not.toHaveBeenCalled()
  })

  it('writes state changes to the url with replace, omitting the defaults', async () => {
    useDocumentFilterQuery(store)

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

  it('does not persist the transient search scope', async () => {
    const isSearching = ref(true)
    useDocumentFilterQuery(store, { isSearching })

    // La búsqueda mueve el scope a 'all' por debajo; la URL no debe verlo.
    store.archiveScope = 'all'
    await nextTick()

    expect(mockReplace).not.toHaveBeenCalled()

    // Fuera de la búsqueda el mismo eje SÍ se escribe: la pausa era de la
    // búsqueda, no una pérdida del watcher.
    isSearching.value = false
    store.archiveScope = 'archived'
    await nextTick()

    expect(mockReplace).toHaveBeenCalledWith({ query: { scope: 'archived' } })
  })

  it('validateFolder falls back to all when the folder no longer exists', () => {
    store.activeFolderId = 99
    const { validateFolder } = useDocumentFilterQuery(store)

    const changed = validateFolder({ folderById: () => null })

    expect(changed).toBe(true)
    expect(store.activeFolderId).toBe('all')
  })

  it('validateFolder leaves an existing folder untouched', () => {
    store.activeFolderId = 4
    const { validateFolder } = useDocumentFilterQuery(store)

    const changed = validateFolder({ folderById: (id) => ({ id }) })

    expect(changed).toBe(false)
    expect(store.activeFolderId).toBe(4)
  })
})
