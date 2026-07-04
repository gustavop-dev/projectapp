import { setActivePinia, createPinia } from 'pinia'
import { usePlatformScopeItemsStore } from '../../stores/platform-scope-items'

jest.mock('../../composables/usePlatformApi', () => {
  const mockGet = jest.fn()
  return {
    usePlatformApi: () => ({ get: mockGet }),
    __mockGet: mockGet,
  }
})

const { __mockGet: mockGet } = require('../../composables/usePlatformApi')

describe('usePlatformScopeItemsStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = usePlatformScopeItemsStore()
    jest.clearAllMocks()
  })

  // -- getters ---------------------------------------------------------------

  it('itemCount reflects the number of items', () => {
    store.items = [{ id: 1 }, { id: 2 }]
    expect(store.itemCount).toBe(2)
  })

  it('groups buckets items by group_id preserving titles and icons', () => {
    store.items = [
      { id: 1, group_id: 'views', group_title: 'Vistas', group_icon: '🖥️', name: 'Login' },
      { id: 2, group_id: 'views', group_title: 'Vistas', group_icon: '🖥️', name: 'Home' },
      { id: 3, group_id: 'components', group_title: 'Componentes', group_icon: '🧩', name: 'Navbar' },
    ]
    const groups = store.groups
    expect(groups).toHaveLength(2)
    expect(groups[0]).toMatchObject({ group_id: 'views', group_title: 'Vistas', group_icon: '🖥️' })
    expect(groups[0].items.map((i) => i.name)).toEqual(['Login', 'Home'])
    expect(groups[1].group_id).toBe('components')
  })

  it('groups falls back to "otros" when group_id is missing', () => {
    store.items = [{ id: 1, name: 'Suelto' }]
    expect(store.groups[0].group_id).toBe('otros')
  })

  // -- fetchScopeItems -------------------------------------------------------

  it('fetchScopeItems loads items and stores projectId', async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: 1, name: 'Login' }] })
    const result = await store.fetchScopeItems(7)
    expect(result).toEqual({ success: true })
    expect(store.items).toEqual([{ id: 1, name: 'Login' }])
    expect(store.projectId).toBe(7)
    expect(mockGet).toHaveBeenCalledWith('projects/7/scope-items/')
  })

  it('fetchScopeItems appends phase_id query when given', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchScopeItems(7, 42)
    expect(mockGet).toHaveBeenCalledWith('projects/7/scope-items/?phase_id=42')
  })

  it('fetchScopeItems coerces a non-array payload to an empty array', async () => {
    // The E2E mock (and any unexpected backend response) can return {} — the
    // store must keep items iterable so board getters never throw.
    mockGet.mockResolvedValueOnce({ data: {} })
    await store.fetchScopeItems(7)
    expect(store.items).toEqual([])
    expect(store.groups).toEqual([])
  })

  it('fetchScopeItems returns a message on error', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'boom' } } })
    const result = await store.fetchScopeItems(7)
    expect(result.success).toBe(false)
    expect(result.message).toBe('boom')
    expect(store.error).toBe('boom')
  })
})
