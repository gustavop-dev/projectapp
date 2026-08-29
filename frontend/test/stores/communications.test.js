jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

import { createPinia, setActivePinia } from 'pinia';
import { useCommunicationsStore } from '../../stores/communications';
import { useDocumentStore } from '../../stores/documents';
import {
  create_request,
  delete_request,
  get_request,
  patch_request,
} from '../../stores/services/request_http';


const thread = (overrides = {}) => ({
  id: 3,
  title: 'Aprobación de alcance',
  status: 'open',
  messages: [],
  ...overrides,
});


describe('communications store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    jest.clearAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => jest.restoreAllMocks());

  it('loads a filtered page of threads', async () => {
    get_request.mockResolvedValueOnce({
      data: {
        results: [thread()], count: 1, page: 1, num_pages: 1,
        facets: { total: 1, projects: [{ id: 19, count: 1 }] },
      },
    });
    const store = useCommunicationsStore();

    const result = await store.fetchThreads({ client: 8, status: 'open' });

    expect(get_request).toHaveBeenCalledWith(
      'communications/threads/?client=8&status=open',
    );
    expect(result.success).toBe(true);
    expect(store.threads).toHaveLength(1);
    expect(store.facets.projects).toEqual([{ id: 19, count: 1 }]);
  });

  it('serializes multi-value filters as comma-separated query values', async () => {
    get_request.mockResolvedValueOnce({
      data: { results: [], count: 0, page: 1, num_pages: 1 },
    });
    const store = useCommunicationsStore();

    await store.fetchThreads({ status: ['open', 'closed'], channel: ['email'] });

    expect(get_request).toHaveBeenCalledWith(
      'communications/threads/?status=open%2Cclosed&channel=email',
    );
  });

  it('keeps the newest result when saved-view requests overlap', async () => {
    let resolveFirst;
    get_request
      .mockImplementationOnce(() => new Promise((resolve) => { resolveFirst = resolve; }))
      .mockResolvedValueOnce({
        data: {
          results: [thread({ id: 8, title: 'Vista guardada' })],
          count: 1,
          page: 1,
          num_pages: 1,
        },
      });
    const store = useCommunicationsStore();

    const initialRequest = store.fetchThreads({});
    await store.fetchThreads({ client: 17 });
    resolveFirst({
      data: {
        results: [thread({ id: 3, title: 'Todos' })],
        count: 1,
        page: 1,
        num_pages: 1,
      },
    });
    await initialRequest;

    expect(store.threads).toEqual([expect.objectContaining({ id: 8 })]);
    expect(store.isLoading).toBe(false);
  });

  it('creates a thread as the current conversation', async () => {
    create_request.mockResolvedValueOnce({ data: thread() });
    const store = useCommunicationsStore();

    const result = await store.createThread({ client: 8, title: 'Aprobación de alcance' });

    expect(create_request).toHaveBeenCalledWith('communications/threads/', {
      client: 8,
      title: 'Aprobación de alcance',
    });
    expect(result.success).toBe(true);
    expect(store.currentThread.id).toBe(3);
  });

  it('fetches the ordered messages of one thread', async () => {
    get_request.mockResolvedValueOnce({ data: thread({ messages: [{ id: 11 }] }) });
    const store = useCommunicationsStore();

    await store.fetchThread(3);

    expect(get_request).toHaveBeenCalledWith('communications/threads/3/');
    expect(store.currentThread.messages).toEqual([{ id: 11 }]);
  });

  it('registers a message through its owning thread', async () => {
    create_request.mockResolvedValueOnce({ data: { id: 11, thread_id: 3 } });
    get_request.mockResolvedValueOnce({ data: thread({ messages: [{ id: 11 }] }) });
    const store = useCommunicationsStore();
    const payload = { channel: 'whatsapp', direction: 'outgoing', content: 'Hola' };

    const result = await store.createMessage(3, payload);

    expect(create_request).toHaveBeenCalledWith(
      'communications/threads/3/messages/', payload,
    );
    expect(result.success).toBe(true);
    expect(store.currentThread.messages).toHaveLength(1);
  });

  it('marks a draft as sent with the supplied date', async () => {
    const occurredAt = '2026-08-25T12:00:00.000Z';
    create_request.mockResolvedValueOnce({ data: { id: 11, thread_id: 3 } });
    get_request.mockResolvedValueOnce({ data: thread() });
    const store = useCommunicationsStore();

    await store.markSent(11, occurredAt);

    expect(create_request).toHaveBeenCalledWith(
      'communications/messages/11/mark-sent/',
      { occurred_at: occurredAt },
    );
  });

  it('updates only a draft through the message endpoint', async () => {
    patch_request.mockResolvedValueOnce({ data: { id: 11, thread_id: 3 } });
    get_request.mockResolvedValueOnce({ data: thread() });
    const store = useCommunicationsStore();

    const result = await store.updateDraft(11, { content: 'Texto final' });

    expect(patch_request).toHaveBeenCalledWith(
      'communications/messages/11/', { content: 'Texto final' },
    );
    expect(result.success).toBe(true);
  });

  it('deletes a draft through the message endpoint', async () => {
    delete_request.mockResolvedValueOnce({});
    get_request.mockResolvedValueOnce({ data: thread() });
    const store = useCommunicationsStore();

    const result = await store.deleteDraft({ id: 11, thread_id: 3 });

    expect(delete_request).toHaveBeenCalledWith('communications/messages/11/');
    expect(result.success).toBe(true);
  });

  it('keeps a thread-load error separate from the list state', async () => {
    get_request.mockRejectedValueOnce({
      response: { status: 400, data: { detail: 'El hilo está cerrado.' } },
    });
    const store = useCommunicationsStore();

    const result = await store.fetchThread(3);

    expect(result.success).toBe(false);
    expect(result.message).toBe('El hilo está cerrado.');
    expect(store.threadError).toBe('El hilo está cerrado.');
    expect(store.error).toBeNull();
  });

  it('loads the reverse communication usage of a document', async () => {
    get_request.mockResolvedValueOnce({
      data: { count: 1, results: [{ thread: { id: 3, title: 'Aprobación' } }] },
    });
    const store = useDocumentStore();

    const result = await store.fetchDocumentCommunications(73);

    expect(get_request).toHaveBeenCalledWith('documents/73/communications/');
    expect(result.data.count).toBe(1);
  });

  it('normalizes a failed reverse document lookup', async () => {
    get_request.mockRejectedValueOnce({ response: { status: 503, data: {} } });
    const store = useDocumentStore();

    const result = await store.fetchDocumentCommunications(73);

    expect(result.success).toBe(false);
    expect(result.message).toBe('No se pudieron cargar las comunicaciones del documento.');
  });
});
