import { nextTick } from 'vue'
import { useDocumentViewMode } from '../../composables/useDocumentViewMode'

const STORAGE_KEY = 'projectapp-documents-view-mode'

describe('useDocumentViewMode', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('defaults to list on a clean profile', () => {
    const { viewMode } = useDocumentViewMode()
    expect(viewMode.value).toBe('list')
  })

  it('restores a persisted grid mode', () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify('grid'))
    const { viewMode } = useDocumentViewMode()
    expect(viewMode.value).toBe('grid')
  })

  it('falls back to list when the stored value is invalid', () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify('kanban'))
    const { viewMode } = useDocumentViewMode()
    expect(viewMode.value).toBe('list')
  })

  it('persists mode changes to localStorage', async () => {
    const { viewMode } = useDocumentViewMode()
    viewMode.value = 'grid'
    await nextTick()
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe(JSON.stringify('grid'))
  })
})
