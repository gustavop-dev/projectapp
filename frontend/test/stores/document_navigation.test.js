import { createPinia, setActivePinia } from 'pinia';
import { useDocumentNavigationStore } from '../../stores/document_navigation';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  patch_request: jest.fn(),
}));

const { get_request, patch_request } = require('../../stores/services/request_http');

describe('useDocumentNavigationStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useDocumentNavigationStore();
    jest.clearAllMocks();
  });

  it('hydrates the account preference', async () => {
    get_request.mockResolvedValueOnce({ data: { navigation_mode: 'client' } });

    const result = await store.fetchPreference();

    expect(result.success).toBe(true);
    expect(store.mode).toBe('client');
    expect(store.persistedMode).toBe('client');
    expect(store.preferenceReady).toBe(true);
  });

  it('persists a mode selected in the UI', async () => {
    patch_request.mockResolvedValueOnce({ data: { navigation_mode: 'client' } });

    const result = await store.persistMode('client');

    expect(result.success).toBe(true);
    expect(patch_request).toHaveBeenCalledWith(
      'accounts/panel-preferences/documents/',
      { navigation_mode: 'client' },
    );
    expect(store.mode).toBe('client');
  });

  it('rolls the switch back when persistence fails', async () => {
    patch_request.mockRejectedValueOnce(new Error('offline'));

    const result = await store.persistMode('client');

    expect(result.success).toBe(false);
    expect(store.mode).toBe('project');
    expect(store.isSavingPreference).toBe(false);
  });

  it('keeps a facet failure separate from the folder store', async () => {
    get_request.mockRejectedValueOnce(new Error('offline'));

    const result = await store.fetchNavigation();

    expect(result.success).toBe(false);
    expect(store.error).toBe('No se pudieron cargar los proyectos y clientes.');
    expect(store.facets.projects).toEqual([]);
  });
});
