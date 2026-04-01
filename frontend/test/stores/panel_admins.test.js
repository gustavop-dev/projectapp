import { setActivePinia, createPinia } from 'pinia'
import { usePanelAdminsStore } from '../../stores/panel_admins'

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}))

const {
  get_request,
  create_request,
  patch_request,
  delete_request,
} = require('../../stores/services/request_http')

const ADMIN = {
  user_id: 10,
  email: 'a@b.com',
  is_active: true,
  is_onboarded: false,
}

describe('usePanelAdminsStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = usePanelAdminsStore()
    jest.clearAllMocks()
  })

  it('starts with empty admins', () => {
    expect(store.admins).toEqual([])
    expect(store.loading).toBe(false)
  })

  it('activeAdmins filters by is_active', () => {
    store.admins = [
      { user_id: 1, is_active: true },
      { user_id: 2, is_active: false },
    ]
    expect(store.activeAdmins).toHaveLength(1)
  })

  it('pendingAdmins filters active not onboarded', () => {
    store.admins = [
      { user_id: 1, is_active: true, is_onboarded: false },
      { user_id: 2, is_active: true, is_onboarded: true },
    ]
    expect(store.pendingAdmins).toHaveLength(1)
  })

  it('inactiveAdmins filters not active', () => {
    store.admins = [
      { user_id: 1, is_active: false },
      { user_id: 2, is_active: true },
    ]
    expect(store.inactiveAdmins).toHaveLength(1)
  })

  it('fetchAdmins uses filter query when not all', async () => {
    get_request.mockResolvedValueOnce({ data: [] })
    await store.fetchAdmins('pending')
    expect(get_request).toHaveBeenCalledWith('accounts/admins/?filter=pending')
  })

  it('fetchAdmins omits query for all', async () => {
    get_request.mockResolvedValueOnce({ data: [ADMIN] })
    const result = await store.fetchAdmins('all')
    expect(get_request).toHaveBeenCalledWith('accounts/admins/')
    expect(result.success).toBe(true)
    expect(store.admins).toEqual([ADMIN])
  })

  it('fetchAdmins sets error message on failure', async () => {
    get_request.mockRejectedValueOnce({ response: { data: { detail: 'fail' } } })
    const result = await store.fetchAdmins()
    expect(result.success).toBe(false)
    expect(store.error).toBe('fail')
  })

  it('createAdmin prepends new admin', async () => {
    create_request.mockResolvedValueOnce({ data: ADMIN })
    const result = await store.createAdmin({ email: 'a@b.com' })
    expect(result.success).toBe(true)
    expect(store.admins[0]).toEqual(ADMIN)
  })

  it('createAdmin uses email field from validation error', async () => {
    create_request.mockRejectedValueOnce({
      response: { data: { email: ['taken'] } },
    })
    const result = await store.createAdmin({})
    expect(result.success).toBe(false)
    expect(result.error).toBe('taken')
  })

  it('updateAdmin replaces row by user_id', async () => {
    store.admins = [{ user_id: 10, name: 'old' }]
    patch_request.mockResolvedValueOnce({ data: { user_id: 10, name: 'new' } })
    const result = await store.updateAdmin(10, { name: 'new' })
    expect(result.success).toBe(true)
    expect(store.admins[0].name).toBe('new')
  })

  it('deactivateAdmin sets is_active false', async () => {
    store.admins = [{ user_id: 5, is_active: true }]
    delete_request.mockResolvedValueOnce({})
    const result = await store.deactivateAdmin(5)
    expect(result.success).toBe(true)
    expect(store.admins[0].is_active).toBe(false)
  })

  it('reactivateAdmin patches is_active true', async () => {
    store.admins = [{ user_id: 3, is_active: false }]
    patch_request.mockResolvedValueOnce({ data: { user_id: 3, is_active: true } })
    const result = await store.reactivateAdmin(3)
    expect(result.success).toBe(true)
    expect(store.admins[0].is_active).toBe(true)
  })

  it('resendInvite posts and succeeds', async () => {
    create_request.mockResolvedValueOnce({})
    const result = await store.resendInvite(7)
    expect(create_request).toHaveBeenCalledWith('accounts/admins/7/resend-invite/', {})
    expect(result.success).toBe(true)
  })

  it('fetchAdmins uses default message when detail missing', async () => {
    get_request.mockRejectedValueOnce({ response: {} })
    const result = await store.fetchAdmins()
    expect(result.success).toBe(false)
    expect(store.error).toContain('administradores')
  })

  it('createAdmin uses default message when detail missing', async () => {
    create_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.createAdmin({})
    expect(result.success).toBe(false)
  })

  it('updateAdmin returns error detail on failure', async () => {
    patch_request.mockRejectedValueOnce({ response: { data: { detail: 'u' } } })
    const result = await store.updateAdmin(1, {})
    expect(result.success).toBe(false)
    expect(result.error).toBe('u')
  })

  it('deactivateAdmin returns error detail on failure', async () => {
    delete_request.mockRejectedValueOnce({ response: { data: { detail: 'd' } } })
    const result = await store.deactivateAdmin(1)
    expect(result.success).toBe(false)
  })

  it('reactivateAdmin returns error detail on failure', async () => {
    patch_request.mockRejectedValueOnce({ response: { data: { detail: 'r' } } })
    const result = await store.reactivateAdmin(1)
    expect(result.success).toBe(false)
  })

  it('resendInvite returns error detail on failure', async () => {
    create_request.mockRejectedValueOnce({ response: { data: { detail: 're' } } })
    const result = await store.resendInvite(1)
    expect(result.success).toBe(false)
  })
})
