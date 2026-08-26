import { computed, ref } from 'vue';

export const COLLECTION_ACCOUNT_VIEW_MODES = ['grouped', 'classic'];
export const COLLECTION_ACCOUNT_GROUP_CRITERIA = ['client', 'project'];

const DEFAULT_PREFERENCES = {
  viewMode: 'grouped',
  groupBy: 'client',
};

function validOrDefault(value, validValues, fallback) {
  return validValues.includes(value) ? value : fallback;
}

/**
 * Server-backed view preferences for Cuentas de cobro.
 *
 * Changes are optimistic and always patch both values so a rapid sequence can
 * never leave the singleton with a view/criterion pair assembled from two
 * different interactions. The page disables its controls while that request
 * is in flight; a failure restores the last confirmed pair.
 */
export function useCollectionAccountsViewPreferences(store) {
  const viewMode = ref(DEFAULT_PREFERENCES.viewMode);
  const groupBy = ref(DEFAULT_PREFERENCES.groupBy);
  const isSaving = ref(false);
  const isGrouped = computed(() => viewMode.value === 'grouped');
  let confirmed = { ...DEFAULT_PREFERENCES };

  function hydrate(settings = {}) {
    viewMode.value = validOrDefault(
      settings.collection_accounts_view_mode,
      COLLECTION_ACCOUNT_VIEW_MODES,
      DEFAULT_PREFERENCES.viewMode,
    );
    groupBy.value = validOrDefault(
      settings.collection_accounts_group_by,
      COLLECTION_ACCOUNT_GROUP_CRITERIA,
      DEFAULT_PREFERENCES.groupBy,
    );
    confirmed = { viewMode: viewMode.value, groupBy: groupBy.value };
  }

  async function initFromSettings() {
    let result = { success: true, data: store.settings };
    if (!store.settings) result = await store.fetchSettings();
    hydrate(store.settings || result.data || {});
    return result;
  }

  async function persist(nextPreferences) {
    if (isSaving.value) return { success: false, busy: true };

    const next = {
      viewMode: validOrDefault(
        nextPreferences.viewMode,
        COLLECTION_ACCOUNT_VIEW_MODES,
        viewMode.value,
      ),
      groupBy: validOrDefault(
        nextPreferences.groupBy,
        COLLECTION_ACCOUNT_GROUP_CRITERIA,
        groupBy.value,
      ),
    };

    viewMode.value = next.viewMode;
    groupBy.value = next.groupBy;
    isSaving.value = true;
    const result = await store.updateSettings({
      collection_accounts_view_mode: next.viewMode,
      collection_accounts_group_by: next.groupBy,
    });
    isSaving.value = false;

    if (result.success) {
      hydrate(result.data || store.settings || {
        collection_accounts_view_mode: next.viewMode,
        collection_accounts_group_by: next.groupBy,
      });
    } else {
      viewMode.value = confirmed.viewMode;
      groupBy.value = confirmed.groupBy;
    }
    return result;
  }

  function setViewMode(mode) {
    return persist({ viewMode: mode, groupBy: groupBy.value });
  }

  function setGroupBy(criterion) {
    return persist({ viewMode: viewMode.value, groupBy: criterion });
  }

  return {
    viewMode,
    groupBy,
    isGrouped,
    isSaving,
    initFromSettings,
    setViewMode,
    setGroupBy,
  };
}
