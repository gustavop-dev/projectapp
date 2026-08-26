import { createPinia, setActivePinia } from 'pinia';
import { useDocumentStateStore } from '../../stores/document_states';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
}));

const { get_request, create_request, patch_request } = require('../../stores/services/request_http');

describe('useDocumentStateStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useDocumentStateStore();
    jest.clearAllMocks();
  });

  it('loads the grouped catalog', async () => {
    get_request
      .mockResolvedValueOnce({ data: [{ id: 2, name: 'Enviado', group: 1, is_active: true }] })
      .mockResolvedValueOnce({ data: [{ id: 1, name: 'Ciclo', selection_mode: 'exclusive' }] });

    const result = await store.fetchCatalog();

    expect(result.success).toBe(true);
    expect(store.statesByGroup[0].states[0].name).toBe('Enviado');
    expect(get_request).toHaveBeenNthCalledWith(1, 'document-states/');
    expect(get_request).toHaveBeenNthCalledWith(2, 'document-state-groups/');
  });

  it('surfaces similar states before creating a duplicate', async () => {
    create_request.mockRejectedValueOnce({
      response: {
        status: 409,
        data: { code: 'similar_states', detail: 'Parecido', suggestions: [{ id: 4 }] },
      },
    });

    const result = await store.createState({ name: 'Arreglar bug' });

    expect(result.needsConfirmation).toBe(true);
    expect(result.suggestions).toEqual([{ id: 4 }]);
  });

  it('opens an episode with its provenance', async () => {
    create_request.mockResolvedValueOnce({ data: { id: 30 } });

    const result = await store.openEpisode(8, 3, '2026-08-20T14:00:00.000Z', 'email');

    expect(result.success).toBe(true);
    expect(create_request).toHaveBeenCalledWith('documents/8/state-episodes/', {
      state_id: 3,
      opened_at: '2026-08-20T14:00:00.000Z',
      origin: 'email',
    });
  });

  it('preserves the removal outcome', async () => {
    create_request.mockResolvedValueOnce({ data: { id: 30, outcome: 'removed' } });

    await store.closeEpisode(8, 30, 'removed', 'No aplicaba');

    expect(create_request).toHaveBeenCalledWith(
      'documents/8/state-episodes/30/close/',
      { outcome: 'removed', note: 'No aplicaba' },
    );
  });

  it('loads the complete episode history', async () => {
    get_request.mockResolvedValueOnce({ data: [{ id: 9, closed_at: null }] });

    await store.fetchHistory(8);

    expect(store.history).toEqual([{ id: 9, closed_at: null }]);
    expect(get_request).toHaveBeenCalledWith('documents/8/state-history/');
  });

  it('creates a note that requests the needs-fix signal', async () => {
    create_request.mockResolvedValueOnce({ data: { id: 5, episode: 30 } });

    await store.createNote(8, { content: 'Corregir total', mark_needs_fix: true });

    expect(create_request).toHaveBeenCalledWith('documents/8/notes/', {
      content: 'Corregir total',
      mark_needs_fix: true,
    });
  });

  it('corrects an episode opening time', async () => {
    patch_request.mockResolvedValueOnce({ data: { id: 30 } });

    await store.correctEpisode(8, 30, '2026-08-18T10:00:00.000Z');

    expect(patch_request).toHaveBeenCalledWith(
      'documents/8/state-episodes/30/opened-at/',
      { opened_at: '2026-08-18T10:00:00.000Z' },
    );
  });
});
