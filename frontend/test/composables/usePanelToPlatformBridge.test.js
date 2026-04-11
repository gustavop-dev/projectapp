const mockCreateRequest = jest.fn()
const mockWritePlatformSession = jest.fn()

describe('usePanelToPlatformBridge', () => {
  let openSpy

  beforeEach(() => {
    jest.resetModules()
    jest.doMock('../../stores/services/request_http', () => ({
      create_request: mockCreateRequest,
    }))
    jest.doMock('../../composables/usePlatformApi', () => ({
      writePlatformSession: mockWritePlatformSession,
    }))
    mockCreateRequest.mockReset()
    mockWritePlatformSession.mockReset()
    openSpy = jest.spyOn(window, 'open').mockImplementation(() => {})
  })

  afterEach(() => {
    openSpy.mockRestore()
  })

  function load() {
    return require('../../composables/usePanelToPlatformBridge')
  }

  it('returns false for isBridging initially', () => {
    const { usePanelToPlatformBridge } = load()
    const { isBridging } = usePanelToPlatformBridge()

    expect(isBridging.value).toBe(false)
  })

  it('ignores goToPlatform call when already bridging', async () => {
    let resolve
    mockCreateRequest.mockReturnValue(new Promise((r) => { resolve = r }))
    const { usePanelToPlatformBridge } = load()
    const { goToPlatform } = usePanelToPlatformBridge()

    const first = goToPlatform()
    const second = goToPlatform()
    resolve({ data: { tokens: { access: 'a', refresh: 'r' }, user: {} } })
    await first
    await second

    expect(mockCreateRequest).toHaveBeenCalledTimes(1)
  })

  it('calls create_request with accounts/session-token-bridge/ endpoint', async () => {
    mockCreateRequest.mockResolvedValueOnce({
      data: { tokens: { access: 'acc', refresh: 'ref' }, user: { id: 1 } },
    })
    const { usePanelToPlatformBridge } = load()
    const { goToPlatform } = usePanelToPlatformBridge()

    await goToPlatform()

    expect(mockCreateRequest).toHaveBeenCalledWith('accounts/session-token-bridge/')
  })

  it('calls writePlatformSession with tokens and user from response', async () => {
    const tokens = { access: 'access-tok', refresh: 'refresh-tok' }
    const user = { id: 42, email: 'a@b.com' }
    mockCreateRequest.mockResolvedValueOnce({ data: { tokens, user } })
    const { usePanelToPlatformBridge } = load()
    const { goToPlatform } = usePanelToPlatformBridge()

    await goToPlatform()

    expect(mockWritePlatformSession).toHaveBeenCalledWith({
      accessToken: tokens.access,
      refreshToken: tokens.refresh,
      user,
    })
  })

  it('opens target path in new tab on success and resets isBridging', async () => {
    mockCreateRequest.mockResolvedValueOnce({
      data: { tokens: { access: 'a', refresh: 'r' }, user: {} },
    })
    const { usePanelToPlatformBridge } = load()
    const { goToPlatform, isBridging } = usePanelToPlatformBridge()

    await goToPlatform('/platform/projects')

    expect(openSpy).toHaveBeenCalledWith('/platform/projects', '_blank')
    expect(isBridging.value).toBe(false)
  })

  it('uses /platform/dashboard as default target path', async () => {
    mockCreateRequest.mockResolvedValueOnce({
      data: { tokens: { access: 'a', refresh: 'r' }, user: {} },
    })
    const { usePanelToPlatformBridge } = load()
    const { goToPlatform } = usePanelToPlatformBridge()

    await goToPlatform()

    expect(openSpy).toHaveBeenCalledWith('/platform/dashboard', '_blank')
  })

  it('opens /platform/login in new tab when request throws and resets isBridging', async () => {
    mockCreateRequest.mockRejectedValueOnce(new Error('network error'))
    const { usePanelToPlatformBridge } = load()
    const { goToPlatform, isBridging } = usePanelToPlatformBridge()

    await goToPlatform('/platform/projects')

    expect(openSpy).toHaveBeenCalledWith('/platform/login', '_blank')
    expect(isBridging.value).toBe(false)
  })
})
