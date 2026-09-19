/** @jest-environment node */
import fs from 'node:fs'
import vm from 'node:vm'
import path from 'node:path'

// Execute the shipped worker in a worker-like context. Only the browser/network
// boundary is supplied; the routing and generated offline Response are real.
function loadWorker() {
  const handlers = new Map()
  const network = jest.fn()
  const scope = {
    addEventListener: (type, callback) => handlers.set(type, callback),
    location: { origin: 'https://projectapp.test' },
    clients: { claim: () => Promise.resolve() },
  }
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../../public/sw.js'), 'utf8'), {
    self: scope, URL, Response, fetch: network,
  })
  return {
    network,
    navigate(url, overrides = {}) {
      const response = jest.fn()
      handlers.get('fetch')({
        request: { url: new URL(url, scope.location.origin).href, method: 'GET', mode: 'navigate', ...overrides },
        respondWith: response,
      })
      return response
    },
  }
}

describe('panel service worker', () => {
  it.each([
    ['/es-co/panel', 'Sin conexión'],
    ['/en-us/panel/projects', 'You are offline'],
    ['/panel', 'Sin conexión'],
    ['/admin/login/?next=/en-us/panel', 'You are offline'],
  ])('offers a localized retry for an offline navigation to %s', async (url, title) => {
    const worker = loadWorker()
    worker.network.mockRejectedValue(new TypeError('network unavailable'))
    const reply = worker.navigate(url)
    const response = await reply.mock.calls[0][0]
    expect(response.status).toBe(503)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(await response.text()).toContain(title)
  })

  it.each([
    ['/api/auth/check/', {}],
    ['/es-co/proposal/private-id', {}],
    ['/es-co/platform/dashboard', {}],
    ['/es-co/lk/example', {}],
    ['/en-us/blog', {}],
    ['/admin/login/', { method: 'POST' }],
    ['/es-co/panel', { mode: 'cors' }],
    ['https://external.test/es-co/panel', {}],
  ])('leaves the excluded request %s to the browser', (url, overrides) => {
    const worker = loadWorker()
    const reply = worker.navigate(url, overrides)
    expect(reply).not.toHaveBeenCalled()
    expect(worker.network).not.toHaveBeenCalled()
  })

  it('preserves permission errors from the server', async () => {
    const worker = loadWorker()
    worker.network.mockResolvedValue(new Response('Permission denied', { status: 403 }))
    const response = await worker.navigate('/es-co/panel').mock.calls[0][0]
    expect(response.status).toBe(403)
    expect(await response.text()).toBe('Permission denied')
  })

  it('does not interpolate login query parameters into the offline HTML', async () => {
    const worker = loadWorker()
    worker.network.mockRejectedValue(new TypeError('offline'))
    const response = await worker.navigate('/admin/login/?next=%3Cscript%3Ealert(1)%3C/script%3E').mock.calls[0][0]
    const html = await response.text()
    expect(html).toContain('Sin conexión')
    expect(html).not.toContain('alert(1)')
  })
})
