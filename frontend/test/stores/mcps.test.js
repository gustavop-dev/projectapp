import { setActivePinia, createPinia } from 'pinia'
import { useMcpsStore } from '../../stores/mcps'

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

const CONNECTOR = {
  slug: 'blog',
  name: 'Blog Publisher',
  description: 'Publica blogs desde Claude.',
  is_active: false,
  has_token: false,
  token_prefix: '',
  last_used_at: null,
  tools: [{ name: 'create_blog_post', description: 'Crea un post.' }],
  credentials: [],
}

describe('useMcpsStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useMcpsStore()
    jest.clearAllMocks()
  })

  it('fetchConnectors loads the list', async () => {
    get_request.mockResolvedValue({ data: [CONNECTOR] })
    const result = await store.fetchConnectors()
    expect(result.success).toBe(true)
    expect(store.connectors).toHaveLength(1)
    expect(get_request).toHaveBeenCalledWith('mcp-connectors/')
  })

  it('fetchConnectors stores a readable error on failure', async () => {
    get_request.mockRejectedValue({ response: { data: { detail: 'nope' } } })
    const result = await store.fetchConnectors()
    expect(result.success).toBe(false)
    expect(store.error).toBe('nope')
  })

  it('generateToken returns the one-time connector URL', async () => {
    create_request.mockResolvedValue({
      data: { connector_url: 'https://projectapp.co/api/mcp/blog/abc123def/', token_prefix: 'abc123de' },
    })
    get_request.mockResolvedValue({ data: [{ ...CONNECTOR, has_token: true, token_prefix: 'abc123de' }] })
    const result = await store.generateToken('blog')
    expect(result.success).toBe(true)
    expect(result.data.connector_url).toContain('/api/mcp/blog/')
    expect(create_request).toHaveBeenCalledWith('mcp-connectors/blog/generate-token/', {})
  })

  it('toggleConnector patches is_active and updates local state', async () => {
    store.connectors = [{ ...CONNECTOR }]
    patch_request.mockResolvedValue({ data: { ...CONNECTOR, is_active: true } })
    const result = await store.toggleConnector('blog', true)
    expect(result.success).toBe(true)
    expect(store.connectors[0].is_active).toBe(true)
    expect(patch_request).toHaveBeenCalledWith('mcp-connectors/blog/', { is_active: true })
  })

  it('createCredential returns its one-time URL and refreshes the catalog', async () => {
    create_request.mockResolvedValue({
      data: { id: 7, connector_url: 'https://projectapp.co/api/mcp/blog/scoped-token/' },
    })
    get_request.mockResolvedValue({ data: [CONNECTOR] })
    const payload = { label: 'Lectura', allowed_tools: ['get_blog_template'] }

    const result = await store.createCredential('blog', payload)

    expect(result.data.connector_url).toContain('/api/mcp/blog/')
    expect(create_request).toHaveBeenCalledWith('mcp-connectors/blog/credentials/', payload)
    expect(get_request).toHaveBeenCalledWith('mcp-connectors/')
  })

  it('updateCredential replaces the connector payload in local state', async () => {
    store.connectors = [{ ...CONNECTOR }]
    const updated = { ...CONNECTOR, credentials: [{ id: 7, label: 'Lectura' }] }
    patch_request.mockResolvedValue({ data: updated })

    const result = await store.updateCredential('blog', 7, { expires_at: null })

    expect(result.success).toBe(true)
    expect(store.connectors[0].credentials).toHaveLength(1)
    expect(patch_request).toHaveBeenCalledWith(
      'mcp-connectors/blog/credentials/7/',
      { expires_at: null },
    )
  })

  it('rotateCredential returns the replacement secret once', async () => {
    create_request.mockResolvedValue({
      data: { id: 7, connector_url: 'https://projectapp.co/api/mcp/blog/replacement/' },
    })
    get_request.mockResolvedValue({ data: [CONNECTOR] })

    const result = await store.rotateCredential('blog', 7)

    expect(result.success).toBe(true)
    expect(create_request).toHaveBeenCalledWith(
      'mcp-connectors/blog/credentials/7/rotate/',
      {},
    )
  })

  it('revokeCredential deletes only the selected credential', async () => {
    delete_request.mockResolvedValue({ status: 204 })
    get_request.mockResolvedValue({ data: [CONNECTOR] })

    const result = await store.revokeCredential('blog', 7)

    expect(result.success).toBe(true)
    expect(delete_request).toHaveBeenCalledWith('mcp-connectors/blog/credentials/7/')
  })
})
