import { useCollectionAccountsViewPreferences } from '../../composables/useCollectionAccountsViewPreferences';

function settings(overrides = {}) {
  return {
    collection_accounts_view_mode: 'grouped',
    collection_accounts_group_by: 'client',
    ...overrides,
  };
}

function makeStore(initialSettings = settings()) {
  return {
    settings: initialSettings,
    fetchSettings: jest.fn(),
    updateSettings: jest.fn(),
  };
}

describe('useCollectionAccountsViewPreferences', () => {
  it('defaults to grouped by client before initialization', () => {
    const preferences = useCollectionAccountsViewPreferences(makeStore(null));

    expect(preferences.viewMode.value).toBe('grouped');
    expect(preferences.groupBy.value).toBe('client');
    expect(preferences.isGrouped.value).toBe(true);
  });

  it('adopts cached server preferences without refetching', async () => {
    const store = makeStore(settings({
      collection_accounts_view_mode: 'classic',
      collection_accounts_group_by: 'project',
    }));
    const preferences = useCollectionAccountsViewPreferences(store);

    await preferences.initFromSettings();

    expect(preferences.viewMode.value).toBe('classic');
    expect(preferences.groupBy.value).toBe('project');
    expect(store.fetchSettings).not.toHaveBeenCalled();
  });

  it('fetches missing settings before hydrating', async () => {
    const store = makeStore(null);
    store.fetchSettings = jest.fn(async () => {
      store.settings = settings({ collection_accounts_group_by: 'project' });
      return { success: true, data: store.settings };
    });
    const preferences = useCollectionAccountsViewPreferences(store);

    await preferences.initFromSettings();

    expect(store.fetchSettings).toHaveBeenCalledTimes(1);
    expect(preferences.groupBy.value).toBe('project');
  });

  it('falls back when the server contains unknown values', async () => {
    const store = makeStore(settings({
      collection_accounts_view_mode: 'cards',
      collection_accounts_group_by: 'nested',
    }));
    const preferences = useCollectionAccountsViewPreferences(store);

    await preferences.initFromSettings();

    expect(preferences.viewMode.value).toBe('grouped');
    expect(preferences.groupBy.value).toBe('client');
  });

  it('persists both fields from an in-page change', async () => {
    const store = makeStore();
    store.updateSettings = jest.fn(async (payload) => ({
      success: true,
      data: { ...store.settings, ...payload },
    }));
    const preferences = useCollectionAccountsViewPreferences(store);
    await preferences.initFromSettings();

    await preferences.setGroupBy('project');

    expect(store.updateSettings).toHaveBeenCalledWith({
      collection_accounts_view_mode: 'grouped',
      collection_accounts_group_by: 'project',
    });
    expect(preferences.groupBy.value).toBe('project');
  });

  it('restores the last confirmed pair after a save failure', async () => {
    const store = makeStore();
    store.updateSettings = jest.fn(async () => ({
      success: false,
      message: 'Sin conexión',
    }));
    const preferences = useCollectionAccountsViewPreferences(store);
    await preferences.initFromSettings();

    const result = await preferences.setViewMode('classic');

    expect(result.success).toBe(false);
    expect(preferences.viewMode.value).toBe('grouped');
    expect(preferences.groupBy.value).toBe('client');
  });
});
