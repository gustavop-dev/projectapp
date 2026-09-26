/**
 * Tests for the secure_links store.
 * Covers: list filters/counters, create merge without URL, revealed content is
 * never kept in state, public token calls and error normalization.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useSecureLinksStore } from '../../stores/secure_links';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const { get_request, create_request, delete_request } = require('../../stores/services/request_http');

const row = { id: 7, title: 'Admin', status: 'active' };

describe('useSecureLinksStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useSecureLinksStore();
    jest.clearAllMocks();
  });

  it('requests only the active filters and stores counters and the public page URL', async () => {
    get_request.mockResolvedValue({ data: {
      results: [row], count: 1, page: 2, page_size: 25,
      counts: { active: 1 }, unopened_received: 3, public_create_url: 'https://x/es-co/secure-link',
    } });

    await store.fetchLinks({ status: 'active', received: '', search: '', page: 2 });

    expect(get_request).toHaveBeenCalledWith('secure-links/?status=active&page=2');
    expect(store.links).toEqual([row]);
    expect(store.unopenedReceived).toBe(3);
    expect(store.publicCreateUrl).toBe('https://x/es-co/secure-link');
  });

  it('adds a created link to the list without keeping its one-time URL', async () => {
    create_request.mockResolvedValue({ data: { ...row, url: 'https://x#token' } });

    const result = await store.createLink({ title: 'Admin' });

    expect(result.data.url).toBe('https://x#token');
    expect(store.links).toEqual([row]);
    expect(JSON.stringify(store.$state)).not.toContain('token');
  });

  it('returns revealed panel content without storing it', async () => {
    create_request.mockResolvedValue({ data: { fields: [{ key: 'password', value: 'S3cr3t' }] } });

    const result = await store.viewContent(7);

    expect(create_request).toHaveBeenCalledWith('secure-links/7/content/', {});
    expect(result.data.fields[0].value).toBe('S3cr3t');
    expect(JSON.stringify(store.$state)).not.toContain('S3cr3t');
  });

  it('sends the public token in the request body, never in the path', async () => {
    create_request.mockResolvedValue({ data: { status: 'active' } });

    await store.publicStatus('abc123');
    await store.publicReveal('abc123');

    expect(create_request).toHaveBeenNthCalledWith(1, 'secure-links/public/status/', { token: 'abc123' });
    expect(create_request).toHaveBeenNthCalledWith(2, 'secure-links/public/reveal/', { token: 'abc123' });
  });

  it('normalizes the backend error code for a consumed link', async () => {
    create_request.mockRejectedValue({ response: { status: 410, data: { error: 'Este enlace ya fue utilizado.', code: 'link_consumed' } } });

    const result = await store.publicReveal('abc123');

    expect(result.success).toBe(false);
    expect(result.error.code).toBe('link_consumed');
    expect(result.error.message).toBe('Este enlace ya fue utilizado.');
  });

  it('removes a deleted link from the list', async () => {
    store.links = [row];
    store.count = 1;
    delete_request.mockResolvedValue({});

    await store.deleteLink(7);

    expect(store.links).toEqual([]);
    expect(store.count).toBe(0);
  });
});
