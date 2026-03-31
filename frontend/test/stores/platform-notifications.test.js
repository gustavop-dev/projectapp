import { setActivePinia, createPinia } from 'pinia'
import { usePlatformNotificationsStore } from '../../stores/platform-notifications'

jest.mock('../../composables/usePlatformApi', () => {
  const mockGet = jest.fn()
  const mockPost = jest.fn()
  return {
    usePlatformApi: () => ({ get: mockGet, post: mockPost }),
    readPlatformSession: jest.fn(() => ({
      accessToken: '',
      refreshToken: '',
      user: null,
      verificationToken: '',
      pendingEmail: '',
    })),
    writePlatformSession: jest.fn(),
    clearPlatformSession: jest.fn(),
    __mockGet: mockGet,
    __mockPost: mockPost,
  }
})

const { __mockGet: mockGet, __mockPost: mockPost } = require('../../composables/usePlatformApi')

describe('usePlatformNotificationsStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = usePlatformNotificationsStore()
    jest.clearAllMocks()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
    store.stopPolling()
  })

  it('unreadNotifications filters not read', () => {
    store.notifications = [
      { id: 1, is_read: false },
      { id: 2, is_read: true },
    ]
    expect(store.unreadNotifications).toHaveLength(1)
  })

  it('readNotifications filters read only', () => {
    store.notifications = [
      { id: 1, is_read: true },
      { id: 2, is_read: false },
    ]
    expect(store.readNotifications).toHaveLength(1)
  })

  it('fetchNotifications appends is_read true query', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchNotifications(true)
    expect(mockGet).toHaveBeenCalledWith('notifications/?is_read=true')
  })

  it('fetchNotifications appends is_read false query', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchNotifications(false)
    expect(mockGet).toHaveBeenCalledWith('notifications/?is_read=false')
  })

  it('fetchNotifications uses base URL when isRead null', async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: 1 }] })
    await store.fetchNotifications(null)
    expect(mockGet).toHaveBeenCalledWith('notifications/')
    expect(store.notifications).toEqual([{ id: 1 }])
  })

  it('fetchNotifications sets error on failure', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'x' } } })
    const result = await store.fetchNotifications()
    expect(result.success).toBe(false)
    expect(store.error).toBe('x')
  })

  it('fetchUnreadCount updates count', async () => {
    mockGet.mockResolvedValueOnce({ data: { count: 3 } })
    const result = await store.fetchUnreadCount()
    expect(result.success).toBe(true)
    expect(store.unreadCount).toBe(3)
  })

  it('fetchUnreadCount returns failure on catch', async () => {
    mockGet.mockRejectedValueOnce(new Error('net'))
    const result = await store.fetchUnreadCount()
    expect(result.success).toBe(false)
  })

  it('markRead updates row and decrements count', async () => {
    store.notifications = [{ id: 5, is_read: false }]
    store.unreadCount = 2
    mockPost.mockResolvedValueOnce({ data: { id: 5, is_read: true } })
    const result = await store.markRead(5)
    expect(result.success).toBe(true)
    expect(store.notifications[0].is_read).toBe(true)
    expect(store.unreadCount).toBe(1)
  })

  it('markRead does not decrement when count already zero', async () => {
    store.notifications = [{ id: 5, is_read: false }]
    store.unreadCount = 0
    mockPost.mockResolvedValueOnce({ data: { id: 5, is_read: true } })
    await store.markRead(5)
    expect(store.unreadCount).toBe(0)
  })

  it('markRead returns failure when post rejects', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'bad' } } })
    const result = await store.markRead(9)
    expect(result.success).toBe(false)
    expect(result.message).toBe('bad')
  })

  it('markAllRead marks every notification read', async () => {
    store.notifications = [
      { id: 1, is_read: false },
      { id: 2, is_read: false },
    ]
    store.unreadCount = 5
    mockPost.mockResolvedValueOnce({ data: { marked_read: 2 } })
    const result = await store.markAllRead()
    expect(result.success).toBe(true)
    expect(store.notifications.every((n) => n.is_read)).toBe(true)
    expect(store.unreadCount).toBe(0)
  })

  it('markAllRead returns failure when post rejects', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'err' } } })
    const result = await store.markAllRead()
    expect(result.success).toBe(false)
    expect(result.message).toBe('err')
  })

  it('startPolling calls fetchUnreadCount on interval', async () => {
    mockGet.mockResolvedValue({ data: { count: 0 } })
    store.startPolling(1000)
    expect(mockGet).toHaveBeenCalled()
    jest.advanceTimersByTime(1000)
    expect(mockGet.mock.calls.length).toBeGreaterThanOrEqual(2)
  })

  it('stopPolling clears interval', () => {
    mockGet.mockResolvedValue({ data: { count: 0 } })
    store.startPolling(500)
    store.stopPolling()
    const callsAfterStop = mockGet.mock.calls.length
    jest.advanceTimersByTime(2000)
    expect(mockGet.mock.calls.length).toBe(callsAfterStop)
  })
})
