import { createProjectAccessApi } from '../../services/projectAccessApi'

function buildTransport() {
  const response = (data = { ok: true }) => Promise.resolve({ data })
  return {
    get: jest.fn(() => response()),
    post: jest.fn(() => response()),
    patch: jest.fn(() => response()),
    remove: jest.fn(() => response()),
  }
}

describe('createProjectAccessApi', () => {
  it('loads the normalized project detail path', async () => {
    const transport = buildTransport()
    const api = createProjectAccessApi(transport, 'projects/7/access')

    await expect(api.load()).resolves.toEqual({ ok: true })

    expect(transport.get).toHaveBeenCalledWith('projects/7/access/')
  })

  it('saves one field through PATCH', async () => {
    const transport = buildTransport()
    const api = createProjectAccessApi(transport, 'projects/7/access/')
    const payload = { environment: 'production', admin_username: 'operator' }

    await api.updateField(payload)

    expect(transport.patch).toHaveBeenCalledWith('projects/7/access/', payload)
  })

  it('uses the dedicated password reveal endpoint', async () => {
    const transport = buildTransport()
    const api = createProjectAccessApi(transport, 'projects/7/access/')

    await api.revealPassword('staging')

    expect(transport.post).toHaveBeenCalledWith(
      'projects/7/access/environments/staging/password/reveal/',
      {},
    )
  })

  it('uses the dedicated password delete endpoint', async () => {
    const transport = buildTransport()
    const api = createProjectAccessApi(transport, 'projects/7/access/')

    await api.deletePassword('production')

    expect(transport.remove).toHaveBeenCalledWith(
      'projects/7/access/environments/production/password/',
    )
  })

  it('creates a note through the project notes collection', async () => {
    const transport = buildTransport()
    const api = createProjectAccessApi(transport, 'projects/7/access/')
    const payload = { title: 'VPN', content: 'Use Tailscale', is_sensitive: false }

    await api.createNote(payload)

    expect(transport.post).toHaveBeenCalledWith('projects/7/access/notes/', payload)
  })

  it('reveals a note only through its secret endpoint', async () => {
    const transport = buildTransport()
    const api = createProjectAccessApi(transport, 'projects/7/access/')

    await api.revealNote(31)

    expect(transport.post).toHaveBeenCalledWith(
      'projects/7/access/notes/31/reveal/',
      {},
    )
  })

  it('classifies legacy credentials into an explicit environment', async () => {
    const transport = buildTransport()
    const api = createProjectAccessApi(transport, 'projects/7/access/')

    await api.classifyLegacy('production')

    expect(transport.post).toHaveBeenCalledWith(
      'projects/7/access/legacy/classify/',
      { environment: 'production' },
    )
  })
})
