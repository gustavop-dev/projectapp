import { createPinia, setActivePinia } from 'pinia';
import { useDocumentThreadStore } from '../../stores/document_threads';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const {
  get_request,
  create_request,
  patch_request,
  delete_request,
} = require('../../stores/services/request_http');

describe('useDocumentThreadStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useDocumentThreadStore();
    jest.clearAllMocks();
  });

  it('keeps a standalone document as a null thread', async () => {
    get_request.mockResolvedValueOnce({ data: null });

    const result = await store.fetchThread(14);

    expect(result.success).toBe(true);
    expect(store.currentThread).toBeNull();
    expect(get_request).toHaveBeenCalledWith('documents/14/thread/');
  });

  it('ignores a stale thread response after another document opens', async () => {
    let resolveFirst;
    get_request
      .mockImplementationOnce(() => new Promise((resolve) => { resolveFirst = resolve; }))
      .mockResolvedValueOnce({ data: { id: 22, title: 'Hilo vigente' } });

    const first = store.fetchThread(14);
    await store.fetchThread(22);
    resolveFirst({ data: { id: 14, title: 'Hilo anterior' } });
    await first;

    expect(store.currentThread).toEqual({ id: 22, title: 'Hilo vigente' });
  });

  it('loads the thread index with its order and search', async () => {
    get_request.mockResolvedValueOnce({
      data: { count: 2, results: [{ id: 7, title: 'Entrega' }] },
    });

    await store.fetchThreads({ search: '  acta ', order: 'title', page: 3 });

    const url = get_request.mock.calls[0][0];
    expect(url).toContain('document-threads/?');
    expect(url).toContain('order=title');
    expect(url).toContain('search=acta');
    expect(url).toContain('page=3');
    expect(store.threads).toEqual([{ id: 7, title: 'Entrega' }]);
    expect(store.threadCount).toBe(2);
  });

  it('omits a blank search from the thread index query', async () => {
    get_request.mockResolvedValueOnce({ data: { count: 0, results: [] } });

    await store.fetchThreads({ search: '   ' });

    const url = get_request.mock.calls[0][0];
    expect(url).toContain('order=recent');
    expect(url).not.toContain('search=');
  });

  it('ignores a stale thread index response', async () => {
    let resolveFirst;
    get_request.mockReturnValueOnce(new Promise((resolve) => { resolveFirst = resolve; }));
    get_request.mockResolvedValueOnce({
      data: { count: 1, results: [{ id: 2, title: 'Vigente' }] },
    });

    const first = store.fetchThreads({ search: 'a' });
    await store.fetchThreads({ search: 'ab' });
    resolveFirst({ data: { count: 9, results: [{ id: 1, title: 'Obsoleto' }] } });

    await first;

    // Falla si una respuesta que llega tarde pisa la búsqueda vigente.
    expect(store.threads).toEqual([{ id: 2, title: 'Vigente' }]);
    expect(store.threadCount).toBe(1);
    expect(store.isLoadingThreads).toBe(false);
  });

  it('loads paginated candidates with the selected scope', async () => {
    get_request.mockResolvedValueOnce({
      data: { count: 1, next: null, previous: null, results: [{ id: 3 }] },
    });

    await store.fetchCandidates({
      documentId: 14,
      threadId: 9,
      search: ' acta ',
      includeArchived: true,
      page: 2,
    });

    const url = get_request.mock.calls[0][0];
    expect(url).toContain('document_id=14');
    expect(url).toContain('thread_id=9');
    expect(url).toContain('scope=all');
    expect(url).toContain('search=acta');
    expect(url).toContain('page=2');
    expect(store.candidates).toEqual([{ id: 3 }]);
  });

  it('ignores an obsolete candidate failure after a newer search succeeds', async () => {
    let rejectFirst;
    get_request
      .mockImplementationOnce(() => new Promise((resolve, reject) => { rejectFirst = reject; }))
      .mockResolvedValueOnce({
        data: { count: 1, next: null, previous: null, results: [{ id: 22 }] },
      });

    const first = store.fetchCandidates({ documentId: 14, search: 'anterior' });
    await store.fetchCandidates({ documentId: 14, search: 'vigente' });
    rejectFirst(new Error('respuesta anterior fallida'));
    const staleResult = await first;

    expect(staleResult.stale).toBe(true);
    expect(store.candidates).toEqual([{ id: 22 }]);
    expect(store.error).toBeNull();
  });

  it('caches document detail outside the document editor store', async () => {
    get_request.mockResolvedValueOnce({ data: { id: 14, title: 'Acta' } });

    await store.fetchDocumentDetail(14);
    await store.fetchDocumentDetail(14);

    expect(get_request).toHaveBeenCalledTimes(1);
    expect(store.detailCache[14].title).toBe('Acta');
  });

  it('creates a thread and keeps the server response', async () => {
    const payload = { title: 'Entrega', items: [{ document_id: 1 }, { document_id: 2 }] };
    create_request.mockResolvedValueOnce({ data: { id: 8, ...payload } });

    const result = await store.createThread(payload);

    expect(result.success).toBe(true);
    expect(create_request).toHaveBeenCalledWith('document-threads/', payload);
    expect(store.currentThread.id).toBe(8);
  });

  it('clears the current thread when an update dissolves it', async () => {
    store.currentThread = { id: 8 };
    patch_request.mockResolvedValueOnce({ data: { thread: null, dissolved: true } });

    const result = await store.updateThread(8, { items: [{ document_id: 1 }] });

    expect(result.success).toBe(true);
    expect(patch_request).toHaveBeenCalledWith(
      'document-threads/8/',
      { items: [{ document_id: 1 }] },
    );
    expect(store.currentThread).toBeNull();
  });

  it('dissolves the thread through the delete endpoint', async () => {
    store.currentThread = { id: 8 };
    delete_request.mockResolvedValueOnce({});

    const result = await store.dissolveThread(8);

    expect(result.success).toBe(true);
    expect(delete_request).toHaveBeenCalledWith('document-threads/8/');
    expect(store.currentThread).toBeNull();
  });

  it('surfaces the backend conflict without mutating the current thread', async () => {
    store.currentThread = { id: 8, title: 'Original' };
    patch_request.mockRejectedValueOnce({
      response: {
        status: 409,
        data: { code: 'document_already_threaded', error: 'Ya pertenece a otro hilo.' },
      },
    });

    const result = await store.updateThread(8, { title: 'Nuevo' });

    expect(result.success).toBe(false);
    expect(result.code).toBe('document_already_threaded');
    expect(store.currentThread.title).toBe('Original');
  });
});
