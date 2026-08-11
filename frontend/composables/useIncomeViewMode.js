import { computed, ref } from 'vue';

export const INCOME_VIEW_MODES = ['grouped', 'classic'];

/**
 * Grouped/classic mode for /panel/accounting/incomes.
 *
 * Unlike useRecurringViewMode this persists NOTHING on the device: the
 * landing mode is the backend setting `income_default_view_mode`
 * (Configuración), so every visit — on any device — starts where the
 * operator configured it, and the in-page toggle only lasts the visit.
 */
export function useIncomeViewMode(store) {
  // Mirrors the backend default so the pre-init render already matches
  // what a fresh install would land on.
  const viewMode = ref('grouped');
  const isGrouped = computed(() => viewMode.value === 'grouped');

  /**
   * Adopt the configured landing mode. Reuses the settings already in the
   * store (updateSettings keeps them fresh) and falls back silently to
   * 'grouped' when the fetch fails or brings an unknown value: a broken
   * settings endpoint must not take the incomes list down with it.
   */
  async function initFromSettings() {
    if (!store.settings) await store.fetchSettings();
    const mode = store.settings?.income_default_view_mode;
    if (INCOME_VIEW_MODES.includes(mode)) viewMode.value = mode;
  }

  return { viewMode, isGrouped, initFromSettings };
}
