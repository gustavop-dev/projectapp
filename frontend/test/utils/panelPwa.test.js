import { createPanelPwa } from '../../utils/panelPwa'

function createBrowser(overrides = {}) {
  const target = new EventTarget()
  return Object.assign(target, {
    isSecureContext: true,
    location: { pathname: '/es-co/panel' },
    navigator: {
      userAgent: 'Chrome',
      maxTouchPoints: 0,
      serviceWorker: { register: jest.fn().mockResolvedValue({}) },
    },
    matchMedia: () => ({ matches: false, addEventListener() {}, removeEventListener() {} }),
    sessionStorage: { getItem: () => null, setItem: jest.fn() },
  }, overrides)
}

function offerPrompt(browser, outcome = 'accepted', prompt = jest.fn().mockResolvedValue()) {
  const event = new Event('beforeinstallprompt', { cancelable: true })
  Object.assign(event, { prompt, userChoice: Promise.resolve({ outcome }) })
  browser.dispatchEvent(event)
  return event
}

describe('panel PWA installation', () => {
  let browser
  let controller
  beforeEach(() => {
    browser = createBrowser()
    controller = createPanelPwa(browser)
    controller.initialize()
  })
  afterEach(() => {
    controller.dispose()
    jest.restoreAllMocks()
  })

  it('invokes the browser prompt from an installation action', async () => {
    const event = offerPrompt(browser)
    await controller.install()
    expect(event.defaultPrevented).toBe(true)
    expect(event.prompt).toHaveBeenCalledTimes(1)
    expect(controller.canOffer.value).toBe(false)
  })

  it('keeps installation available after cancellation', async () => {
    offerPrompt(browser, 'dismissed')
    await controller.install()
    expect(controller.canOffer.value).toBe(true)
    await controller.install()
    expect(controller.instructionsOpen.value).toBe(true)
  })

  it('opens manual instructions when no native prompt is available', async () => {
    await controller.install()
    expect(controller.instructionsOpen.value).toBe(true)
    expect(controller.browserKind.value).toBe('chromium')
  })

  it('shows a recoverable error when the browser rejects installation', async () => {
    offerPrompt(browser, 'accepted', jest.fn().mockRejectedValue(new Error('unavailable')))
    await controller.install()
    expect(controller.installError.value).toBe(true)
    expect(controller.instructionsOpen.value).toBe(true)
    expect(controller.canOffer.value).toBe(true)
    expect(controller.isPrompting.value).toBe(false)
  })

  it('hides installation help after the appinstalled event', async () => {
    await controller.install()
    browser.dispatchEvent(new Event('appinstalled'))
    expect(controller.instructionsOpen.value).toBe(false)
    expect(controller.canOffer.value).toBe(false)
  })

  it('does not capture prompts belonging to public linktrees', () => {
    browser.location.pathname = '/es-co/lk/example'
    const event = offerPrompt(browser)
    expect(event.defaultPrevented).toBe(false)
  })

  it('does not offer installation when opened in standalone mode', () => {
    const standalone = createPanelPwa(createBrowser({ matchMedia: () => ({ matches: true }) }))
    standalone.initialize()
    standalone.showInvitationOnce()
    expect(standalone.canOffer.value).toBe(false)
    expect(standalone.invitationVisible.value).toBe(false)
    standalone.dispose()
  })

  it('shows the invitation only once when browser storage is blocked', () => {
    const denied = { getItem: () => { throw new Error('denied') }, setItem: () => { throw new Error('denied') } }
    const privateBrowser = createPanelPwa(createBrowser({ sessionStorage: denied }))
    privateBrowser.initialize()
    privateBrowser.showInvitationOnce()
    expect(privateBrowser.invitationVisible.value).toBe(true)
    privateBrowser.dismissInvitation()
    privateBrowser.showInvitationOnce()
    expect(privateBrowser.invitationVisible.value).toBe(false)
    privateBrowser.dispose()
  })

  it('preserves invitation dismissal after a reload', () => {
    const reopened = createPanelPwa(createBrowser({ sessionStorage: { getItem: () => 'seen' } }))
    reopened.initialize()
    reopened.showInvitationOnce()
    expect(reopened.invitationVisible.value).toBe(false)
    expect(reopened.canOffer.value).toBe(true)
    reopened.dispose()
  })

  it('supports initialization without browser globals for SSR', async () => {
    const server = createPanelPwa()
    server.initialize()
    await server.install()
    expect(server.canOffer.value).toBe(false)
    expect(server.instructionsOpen.value).toBe(false)
  })

  it('retries registration on the next panel visit after a network failure', async () => {
    browser.navigator.serviceWorker.register.mockRejectedValueOnce(new Error('offline'))
    await controller.registerWorker()
    await controller.registerWorker()
    expect(browser.navigator.serviceWorker.register).toHaveBeenCalledTimes(2)
    expect(browser.navigator.serviceWorker.register).toHaveBeenLastCalledWith('/sw.js', { scope: '/', updateViaCache: 'none' })
  })

  it('uses iOS instructions for an iPad with a desktop user agent', () => {
    browser.navigator.userAgent = 'Macintosh Safari'
    browser.navigator.maxTouchPoints = 5
    controller.dispose()
    controller = createPanelPwa(browser)
    controller.initialize()
    expect(controller.browserKind.value).toBe('ios')
  })
})
