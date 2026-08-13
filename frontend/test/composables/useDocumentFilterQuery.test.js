/**
 * Tests for useDocumentFilterQuery (persistencia de carpeta/scope en la URL).
 */
import { reactive, ref, nextTick } from 'vue'

const mockRoute = { query: {} }
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

  it('ignores garbage values in the query', () => {
    mockRoute.query = { folder: 'DROP TABLE', scope: 'bogus' }

    const { applyQueryToStore } = useDocumentFilterQuery(store)
    applyQueryToStore()

    expect(store.activeFolderId).toBe('all')
    expect(store.archiveScope).toBe('active')
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
