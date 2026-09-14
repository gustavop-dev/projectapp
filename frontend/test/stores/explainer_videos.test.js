/**
 * Tests for the explainer_videos store: the panel switches that show or hide
 * each module's explainer video in the client-facing views.
 */
import { setActivePinia, createPinia } from 'pinia'
import { useExplainerVideosStore } from '../../stores/explainer_videos'

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  patch_request: jest.fn(),
}))

const { get_request, patch_request } = require('../../stores/services/request_http')

const settings = {
  show_additional_modules_video: true,
  show_financing_video: true,
  updated_at: '2026-09-14T10:00:00Z',
}

describe('useExplainerVideosStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useExplainerVideosStore()
    jest.clearAllMocks()
  })

  it('treats both videos as visible until the settings say otherwise', () => {
    expect(store.settings).toBeNull()
    expect(store.isVisible('additional-modules')).toBe(true)
    expect(store.isVisible('financing')).toBe(true)
  })

  it('loads the switches from the panel endpoint', async () => {
    get_request.mockResolvedValue({ data: { ...settings, show_financing_video: false } })

    const result = await store.fetchSettings()

    expect(get_request).toHaveBeenCalledWith('explainer-videos/admin/settings/')
    expect(result.success).toBe(true)
    expect(store.isVisible('financing')).toBe(false)
    expect(store.isVisible('additional-modules')).toBe(true)
  })

  it('reports a failed load without inventing settings', async () => {
    get_request.mockRejectedValue(new Error('offline'))

    const result = await store.fetchSettings()

    expect(result.success).toBe(false)
    expect(store.settings).toBeNull()
    expect(store.isLoading).toBe(false)
  })

  it('patches only the switch of the requested module', async () => {
    store.settings = { ...settings }
    patch_request.mockResolvedValue({ data: { ...settings, show_additional_modules_video: false } })

    const result = await store.setVisibility('additional-modules', false)

    expect(patch_request).toHaveBeenCalledWith(
      'explainer-videos/admin/settings/update/',
      { show_additional_modules_video: false },
    )
    expect(result.success).toBe(true)
    expect(store.isVisible('additional-modules')).toBe(false)
    expect(store.isUpdating).toBe(false)
  })

  it('shows the new state while saving and reverts it when the save fails', async () => {
    store.settings = { ...settings }
    let rejectPatch
    patch_request.mockImplementation(() => new Promise((_resolve, reject) => { rejectPatch = reject }))

    const pending = store.setVisibility('financing', false)
    expect(store.isVisible('financing')).toBe(false)
    expect(store.isUpdating).toBe(true)
    const error = new Error('bad request')
    error.response = { data: { show_financing_video: ['Valor inválido.'] } }
    rejectPatch(error)
    const result = await pending

    expect(result).toEqual({ success: false, errors: { show_financing_video: ['Valor inválido.'] } })
    expect(store.isVisible('financing')).toBe(true)
  })
})
