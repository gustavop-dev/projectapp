import { nextTick } from 'vue'
import { useIncomeViewMode } from '../../composables/useIncomeViewMode'

describe('useIncomeViewMode', () => {
  afterEach(() => {
    window.localStorage.clear()
  })

  it('defaults to grouped before the settings arrive', () => {
    const { viewMode, isGrouped } = useIncomeViewMode({
      settings: null,
      fetchSettings: jest.fn(),
    })
    // Fails if the pre-init render stops matching the backend default.
    expect(viewMode.value).toBe('grouped')
    expect(isGrouped.value).toBe(true)
  })

  it('adopts the cached setting without refetching', async () => {
    const store = {
      settings: { income_default_view_mode: 'classic' },
      fetchSettings: jest.fn(),
    }
    const { viewMode, initFromSettings } = useIncomeViewMode(store)

    await initFromSettings()

    // Fails if the composable re-fetches settings the store already holds
    // (an extra request per visit) or ignores the configured landing mode.
    expect(viewMode.value).toBe('classic')
    expect(store.fetchSettings).not.toHaveBeenCalled()
  })

  it('fetches the settings when the store has none and applies the mode', async () => {
    const store = { settings: null }
    store.fetchSettings = jest.fn(async () => {
      store.settings = { income_default_view_mode: 'classic' }
      return { success: true, data: store.settings }
    })
    const { viewMode, initFromSettings } = useIncomeViewMode(store)

    await initFromSettings()

    expect(store.fetchSettings).toHaveBeenCalledTimes(1)
    expect(viewMode.value).toBe('classic')
  })

  it('keeps grouped when the fetch fails or brings an unknown mode', async () => {
    const failing = {
      settings: null,
      fetchSettings: jest.fn(async () => ({ success: false })),
    }
    const failed = useIncomeViewMode(failing)
    await failed.initFromSettings()
    // Fails if a broken settings endpoint takes the incomes list down with it.
    expect(failed.viewMode.value).toBe('grouped')

    const bogus = {
      settings: { income_default_view_mode: 'kanban' },
      fetchSettings: jest.fn(),
    }
    const stale = useIncomeViewMode(bogus)
    await stale.initFromSettings()
    expect(stale.viewMode.value).toBe('grouped')
  })

  it('treats the in-page toggle as session-only: nothing persists', async () => {
    const store = {
      settings: { income_default_view_mode: 'grouped' },
      fetchSettings: jest.fn(),
      updateSettings: jest.fn(),
    }
    const { viewMode, isGrouped, initFromSettings } = useIncomeViewMode(store)
    await initFromSettings()

    viewMode.value = 'classic'
    await nextTick()

    // The contract with Configuración: the setting owns the landing mode,
    // so the toggle must write neither the backend nor localStorage.
    expect(isGrouped.value).toBe(false)
    expect(store.updateSettings).not.toHaveBeenCalled()
    expect(window.localStorage.getItem('projectapp-income-view-mode')).toBeNull()
    expect(store.settings.income_default_view_mode).toBe('grouped')
  })
})
