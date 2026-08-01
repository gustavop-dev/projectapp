import { nextTick } from 'vue'
import { useRecurringViewMode } from '../../composables/useRecurringViewMode'

const STORAGE_KEY = 'projectapp-recurring-view-mode'

describe('useRecurringViewMode', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  afterEach(() => {
    window.localStorage.clear()
  })

  it('defaults to grouped on a clean profile', () => {
    const { viewMode } = useRecurringViewMode()
    // Fails if the default view for /panel/accounting/recurring silently changes.
    expect(viewMode.value).toBe('grouped')
  })

  it('restores a persisted table mode', () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify('table'))
    const { viewMode } = useRecurringViewMode()
    // Fails if a valid persisted choice stops being honored on load.
    expect(viewMode.value).toBe('table')
  })

  it('falls back to grouped when the stored value is an invalid/stale mode', () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify('bogus'))
    const { viewMode } = useRecurringViewMode()
    // Fails if a corrupted or removed-mode localStorage value stops being
    // rejected, leaving the user on a mode the UI can't render.
    expect(viewMode.value).toBe('grouped')
  })

  it('persists a mode change back to localStorage', async () => {
    const { viewMode } = useRecurringViewMode()
    viewMode.value = 'table'
    await nextTick()
    // Fails if the write-mirror watch (useRecurringViewMode.js:21-23) stops
    // persisting a valid mode change, silently losing the user's toggle on reload.
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe(JSON.stringify('table'))
  })
})
