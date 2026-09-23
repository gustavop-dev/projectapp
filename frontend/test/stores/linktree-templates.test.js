import { createPinia, setActivePinia } from 'pinia';
import { useLinktreeTemplatesStore } from '../../stores/linktree-templates';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  delete_request: jest.fn(),
}));

const { get_request, create_request } = require('../../stores/services/request_http');

const library = (versionId, activeVersionId = versionId) => ({
  templates: [],
  versions: [{ id: versionId, name: `Versión ${versionId}`, status: 'valid' }],
  active_version_id: activeVersionId,
  can_share: false,
  next_offset: null,
});

describe('useLinktreeTemplatesStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useLinktreeTemplatesStore();
    jest.clearAllMocks();
  });

  it('keeps the second Linktree library when an older request resolves last', async () => {
    // Falla si una respuesta tardía vuelve a mostrar el historial de otra tarjeta.
    let resolveFirst;
    const firstRequest = new Promise((resolve) => { resolveFirst = resolve; });
    get_request
      .mockReturnValueOnce(firstRequest)
      .mockResolvedValueOnce({ data: library('version-bravo') });

    const firstLoad = store.load('tree-alpha');
    const secondLoad = store.load('tree-bravo');
    await secondLoad;
    resolveFirst({ data: library('version-alpha') });
    await firstLoad;

    expect(get_request).toHaveBeenNthCalledWith(1, 'linktrees/admin/tree-alpha/templates/?offset=0');
    expect(get_request).toHaveBeenNthCalledWith(2, 'linktrees/admin/tree-bravo/templates/?offset=0');
    expect(store.treeId).toBe('tree-bravo');
    expect(store.versions).toEqual([{ id: 'version-bravo', name: 'Versión version-bravo', status: 'valid' }]);
    expect(store.activeVersionId).toBe('version-bravo');
  });

  it('publishes the selected version and refreshes the active library version', async () => {
    // Falla si publicar apunta a otra versión o deja el editor con estado desactualizado.
    store.treeId = 'tree-bravo';
    create_request.mockResolvedValueOnce({ data: { id: 'version-two', status: 'valid' } });
    get_request.mockResolvedValueOnce({ data: library('version-three', 'version-three') });

    await store.mutate('tree-bravo', 'version-two/publish/', {});

    expect(create_request).toHaveBeenCalledWith('linktrees/admin/tree-bravo/templates/version-two/publish/', {});
    expect(store.versions).toEqual([{ id: 'version-three', name: 'Versión version-three', status: 'valid' }]);
    expect(store.activeVersionId).toBe('version-three');
  });
});
