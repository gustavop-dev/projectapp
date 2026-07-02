import { setActivePinia, createPinia } from 'pinia'
import { useMcpsStore } from '../../stores/mcps'

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
}))

const { get_request, create_request, patch_request } = require('../../stores/services/request_http')

const CONNECTOR = {
  slug: 'blog',
  name: 'Blog Publisher',
  description: 'Publica blogs desde Claude.',
  is_active: false,
  has_token: false,
  token_prefix: '',
  last_used_at: null,
  tools: [{ name: 'create_blog_post', description: 'Crea un post.' }],
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
})
