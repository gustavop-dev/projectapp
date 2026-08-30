import { nextTick } from 'vue'
import { useAdditionalModulesViewMode } from '../../composables/useAdditionalModulesViewMode'

describe('useAdditionalModulesViewMode', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('defaults to cards for a clean profile', () => {
    const { viewMode } = useAdditionalModulesViewMode('public')

    expect(viewMode.value).toBe('cards')
  })

  it('restores the view independently for each surface', () => {
    window.localStorage.setItem(
      'projectapp-additional-modules-view-mode-public',
      JSON.stringify('accordion'),
    )
    window.localStorage.setItem(
      'projectapp-additional-modules-view-mode-panel',
      JSON.stringify('list'),
    )

    expect(useAdditionalModulesViewMode('public').viewMode.value).toBe('accordion')
    expect(useAdditionalModulesViewMode('panel').viewMode.value).toBe('list')
  })

  it('falls back to cards for an invalid stored mode', () => {
    window.localStorage.setItem(
      'projectapp-additional-modules-view-mode-public',
      JSON.stringify('table'),
    )

    expect(useAdditionalModulesViewMode('public').viewMode.value).toBe('cards')
  })

  it('persists a supported view change', async () => {
    const { viewMode } = useAdditionalModulesViewMode('panel')

    viewMode.value = 'list'
    await nextTick()

    expect(window.localStorage.getItem('projectapp-additional-modules-view-mode-panel'))
      .toBe(JSON.stringify('list'))
  })
})
