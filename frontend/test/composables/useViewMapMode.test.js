/**
 * Tests para useViewMapMode: toggle Lista/Mapa de /panel/views con
 * persistencia en localStorage y deep-linking via ?viewMode y ?module.
 */
import { nextTick } from 'vue';

const mockRoute = { query: {} };
const mockReplace = jest.fn();

jest.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => ({ replace: mockReplace }),
}));

import { useViewMapMode } from '../../composables/useViewMapMode';

const STORAGE_KEY = 'projectapp-view-map-mode';

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

  it('initializes from ?viewMode=map and ?module for deep-linking', () => {
    mockRoute.query = { viewMode: 'map', module: 'admin-panel' };

    const { viewMode, selectedModuleId } = useViewMapMode();

    expect(viewMode.value).toBe('map');
    expect(selectedModuleId.value).toBe('admin-panel');
  });

  it('prefers the query mode over the persisted mode', () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify('map'));
    mockRoute.query = { viewMode: 'list' };

    const { viewMode } = useViewMapMode();

    expect(viewMode.value).toBe('list');
  });

  it('restores the persisted mode when the query has none', () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify('map'));

    const { viewMode } = useViewMapMode();

    expect(viewMode.value).toBe('map');
  });

  it('persists the mode and syncs the query preserving other params', async () => {
    mockRoute.query = { viewTab: '3' };
    const { viewMode } = useViewMapMode();

    viewMode.value = 'map';
    await nextTick();

    expect(JSON.parse(window.localStorage.getItem(STORAGE_KEY))).toBe('map');
    expect(mockReplace).toHaveBeenCalledWith({ query: { viewTab: '3', viewMode: 'map' } });
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
