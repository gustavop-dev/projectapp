global.defineNuxtRouteMiddleware = (fn) => fn
global.navigateTo = jest.fn((to) => to)

const middleware = require('../../middleware/legacy-partnership-route').default

describe('legacy partnership routes', () => {
  afterEach(() => jest.clearAllMocks())

  it.each([
    ['/es-co/panel/financing', '/es-co/panel/partnership-program'],
    ['/en-us/panel/financing/new', '/en-us/panel/partnership-program/new'],
    ['/es-co/panel/financing/42', '/es-co/panel/partnership-program/42'],
    ['/panel/financing', '/es-co/panel/partnership-program'],
  ])('redirects %s to its canonical destination', (path, destination) => {
    const result = middleware({ path, query: { tab: 'agreements' }, hash: '#history' })

    expect(result).toEqual({ path: destination, query: { tab: 'agreements' }, hash: '#history' })
    expect(global.navigateTo).toHaveBeenCalledWith(result, { replace: true, redirectCode: 301 })
  })

  it.each(['/panel/financing-guide', '/es-co/panel/partnership-program'])('leaves %s untouched', (path) => {
    middleware({ path, query: {}, hash: '' })

    expect(global.navigateTo).not.toHaveBeenCalled()
  })
})
