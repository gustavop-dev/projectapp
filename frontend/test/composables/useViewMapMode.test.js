/**
 * Tests para useViewMapMode: toggle Lista/Mapa de /panel/views con
 * deep-linking via ?viewMode y ?module, y aplicación del modo por
 * defecto configurado en backend (applyDefaultMode).
 */
import { nextTick } from 'vue';

const mockRoute = { query: {} };
const mockReplace = jest.fn();

jest.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => ({ replace: mockReplace }),
}));

import { useViewMapMode } from '../../composables/useViewMapMode';

const LEGACY_STORAGE_KEY = 'projectapp-view-map-mode';

describe('useViewMapMode', () => {
  beforeEach(() => {
    mockRoute.query = {};
    mockReplace.mockClear();
    window.localStorage.clear();
  });

  it('defaults to list mode with no module selected', () => {
    const { viewMode, selectedModuleId } = useViewMapMode();

    expect(viewMode.value).toBe('list');
    expect(selectedModuleId.value).toBeNull();
  });

  it('initializes from ?viewMode=map and ?module query params', () => {
    mockRoute.query = { viewMode: 'map', module: 'admin-panel' };

    const { viewMode, selectedModuleId } = useViewMapMode();

    expect(viewMode.value).toBe('map');
    expect(selectedModuleId.value).toBe('admin-panel');
  });

  it('removes the legacy persisted-mode key and no longer reads it', () => {
    window.localStorage.setItem(LEGACY_STORAGE_KEY, JSON.stringify('map'));

    const { viewMode } = useViewMapMode();

    expect(viewMode.value).toBe('list');
    expect(window.localStorage.getItem(LEGACY_STORAGE_KEY)).toBeNull();
  });

  it('syncs the query preserving other params when the mode changes', async () => {
    mockRoute.query = { viewTab: '3' };
    const { viewMode } = useViewMapMode();

    viewMode.value = 'map';
    await nextTick();

    expect(mockReplace).toHaveBeenCalledWith({ query: { viewTab: '3', viewMode: 'map' } });
  });

  it('applyDefaultMode switches to the configured mode and syncs the query', async () => {
    const { viewMode, applyDefaultMode } = useViewMapMode();

    applyDefaultMode('map');
    await nextTick();

    expect(viewMode.value).toBe('map');
    expect(mockReplace).toHaveBeenCalledWith({ query: { viewMode: 'map' } });
  });

  it('applyDefaultMode is a no-op when the URL already sets ?viewMode', () => {
    mockRoute.query = { viewMode: 'list' };
    const { viewMode, applyDefaultMode } = useViewMapMode();

    applyDefaultMode('map');

    expect(viewMode.value).toBe('list');
  });

  it('applyDefaultMode does not override a mode the user already changed', async () => {
    const { viewMode, applyDefaultMode } = useViewMapMode();

    viewMode.value = 'map';
    await nextTick();
    applyDefaultMode('list');

    expect(viewMode.value).toBe('map');
  });

  it('applyDefaultMode ignores invalid modes', () => {
    const { viewMode, applyDefaultMode } = useViewMapMode();

    applyDefaultMode('grid');

    expect(viewMode.value).toBe('list');
  });

  it('selectModule adds ?module and clearModule removes it', async () => {
    mockRoute.query = { viewMode: 'map' };
    const { selectModule, clearModule } = useViewMapMode();

    selectModule('client-platform');
    await nextTick();
    expect(mockReplace).toHaveBeenCalledWith({
      query: { viewMode: 'map', module: 'client-platform' },
    });

    clearModule();
    await nextTick();
    expect(mockReplace).toHaveBeenCalledWith({ query: { viewMode: 'map' } });
  });

  it('switching back to list clears the selected module and query params', async () => {
    mockRoute.query = { viewMode: 'map', module: 'admin-panel' };
    const { viewMode, selectedModuleId } = useViewMapMode();

    viewMode.value = 'list';
    await nextTick();

    expect(selectedModuleId.value).toBeNull();
    expect(mockReplace).toHaveBeenCalledWith({ query: {} });
  });
});
