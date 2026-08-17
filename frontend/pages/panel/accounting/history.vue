<template>
  <div :class="PAGE_MAX_WIDTH">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-light text-text-default">Historial</h1>
      <p class="text-sm text-text-subtle mt-1">
        Qué se cambió en el módulo contable y a quién le salió cada correo automático.
        Solo lectura.
      </p>
    </div>

    <AccountingSubnav active="history" />

    <BaseSegmented
      v-model="tab"
      :options="TAB_OPTIONS"
      class="mb-5"
      data-testid="history-tab"
    />

    <!-- Search + filter toggle -->
    <div class="flex items-center gap-2 mb-3">
      <BaseInput
        v-model="searchInput"
        type="text"
        :placeholder="isChanges ? 'Buscar por registro...' : 'Buscar por asunto...'"
        data-testid="history-search"
        class="w-full sm:max-w-xs"
      />
      <UiFilterToggleButton
        :open="isFilterPanelOpen"
        :count="activeFilterCount"
        data-testid="history-filter-toggle"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      />
      <AccountingExportButton
        class="ml-auto"
        :section="isChanges ? 'change_log' : 'email_log'"
        :params="activeParams()"
      />
    </div>

    <!-- Filter row -->
    <AccountingFilterPanel
      :fields="filterFields"
      :model-value="currentFilters"
      :is-open="isFilterPanelOpen"
      :results-count="totalCount"
      :search-value="currentFilters.search"
      @update:model-value="onFiltersUpdate"
      @reset="onResetFilters"
      @clear-search="onClearSearch"
    />

    <!-- Predefined tabs, under the filter row -->
    <ProposalFilterTabs
      :tabs="displayTabs"
      :active-tab-id="activeTabId"
      :counts="activeCounts"
      :count-title="isChanges ? 'Cambios que cumplen este filtro' : 'Envíos que cumplen este filtro'"
      :is-tab-limit-reached="isTabLimitReached"
      @select="onSelectTab"
      @create="onCreateTab"
      @rename="onRenameTab"
      @delete="onDeleteTab"
      @restore="onRestoreTab"
      @rebase="onRebaseTab"
    />

    <!-- Error -->
    <AccountingErrorState
      v-if="store.error === errorKey"
      :title="isChanges ? 'No se pudo cargar el historial' : 'No se pudo cargar el registro de envíos'"
      :retrying="store.isLoading"
      @retry="load(currentPage)"
    />

    <!-- Loading -->
    <div v-else-if="store.isLoading" class="text-center py-16 text-text-subtle text-sm">
      {{ isChanges ? 'Cargando historial...' : 'Cargando envíos...' }}
    </div>

    <template v-else>
      <ChangelogTable v-if="isChanges" :entries="store.changelog.results" />
      <EmailLogTable
        v-else
        :entries="store.emailLog.results"
        :retrying-id="retryingId"
        @view-body="openBody"
        @retry="retrySend"
      />

      <!-- Server-side pagination -->
      <div
        v-if="totalCount > 0"
        class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mt-4"
      >
        <p class="text-xs text-text-muted text-center sm:text-left" data-testid="history-page-info">
          Página {{ currentPage }} de {{ totalPages }} —
          {{ totalCount }} {{ countLabel }}
        </p>
        <BasePagination
          :current-page="currentPage"
          :total-pages="totalPages"
          @prev="goToPage(currentPage - 1)"
          @next="goToPage(currentPage + 1)"
          @go="goToPage"
        />
      </div>
    </template>

    <EmailBodyModal
      :open="bodyModalOpen"
      :entry="bodyEntry"
      @close="bodyModalOpen = false"
    />
  </div>
</template>

<script setup>
import { PAGE_MAX_WIDTH } from '~/utils/tableLayout';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import AccountingExportButton from '~/components/accounting/AccountingExportButton.vue';
import AccountingFilterPanel from '~/components/accounting/AccountingFilterPanel.vue';
import ChangelogTable from '~/components/accounting/ChangelogTable.vue';
import EmailBodyModal from '~/components/accounting/EmailBodyModal.vue';
import EmailLogTable from '~/components/accounting/EmailLogTable.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import BaseInput from '~/components/base/BaseInput.vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import UiFilterToggleButton from '~/components/ui/FilterToggleButton.vue';
import { useAccountingFilters } from '~/composables/useAccountingFilters';
import { sameFilters } from '~/composables/useSavedFilterTabs';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useAccountingStore } from '~/stores/accounting';
import { usePanelProjectsStore } from '~/stores/panel_projects';
import { useProposalClientsStore } from '~/stores/proposal_clients';
import { buildExportParams } from '~/utils/accountingExportParams';
import {
  CHANGES_DEFAULTS,
  CHANGES_FILTERS_CONFIG,
  CHANGES_PARAM_MAPPING,
  SENDS_DEFAULTS,
  SENDS_FILTERS_CONFIG,
  SENDS_PARAM_MAPPING,
  changesFilterFields,
  sendsFilterFields,
} from '~/constants/historyFilters';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useAccountingStore();
const clientsStore = useProposalClientsStore();
const projectsStore = usePanelProjectsStore();
const notify = usePanelNotify();
const route = useRoute();
const router = useRouter();

const TAB_OPTIONS = [
  { value: 'changes', label: 'Cambios', testId: 'history-tab-changes' },
  { value: 'sends', label: 'Envíos', testId: 'history-tab-sends' },
];

// Both subtabs write the same query string, so whichever is on screen clears
// the whole union before writing its own — otherwise switching would leave
// the other's filters stranded in the URL.
const URL_FILTER_KEYS = [...new Set([
  'search',
  ...Object.keys(SENDS_DEFAULTS),
  ...Object.keys(CHANGES_DEFAULTS),
])];

// Read before the filter factories are built: each one seeds itself from the
// URL only while it is the visible subtab.
const tab = ref(route.query.tab === 'sends' ? 'sends' : 'changes');
const isChanges = computed(() => tab.value === 'changes');

const sends = useAccountingFilters({
  ...SENDS_FILTERS_CONFIG,
  isUrlOwner: () => tab.value === 'sends',
  urlFilterKeys: URL_FILTER_KEYS,
});
const changes = useAccountingFilters({
  ...CHANGES_FILTERS_CONFIG,
  isUrlOwner: () => tab.value === 'changes',
  urlFilterKeys: URL_FILTER_KEYS,
});

const active = computed(() => (isChanges.value ? changes : sends));

// The factory hands back refs inside a plain object, which the template will
// not unwrap on its own; each one is surfaced explicitly.
const currentFilters = computed(() => active.value.currentFilters);
const displayTabs = computed(() => active.value.displayTabs.value);
const activeTabId = computed(() => String(active.value.activeTabId.value));
const activeFilterCount = computed(() => active.value.activeFilterCount.value);
const isTabLimitReached = computed(() => active.value.isTabLimitReached.value);

const searchInput = computed({
  get: () => active.value.searchInput.value,
  set: (value) => { active.value.searchInput.value = value; },
});
const isFilterPanelOpen = computed({
  get: () => active.value.isFilterPanelOpen.value,
  set: (value) => { active.value.isFilterPanelOpen.value = value; },
});

const clientOptions = computed(() =>
  (clientsStore.clients || [])
    .map((client) => ({ value: String(client.id), label: client.name }))
    .sort((a, b) => a.label.localeCompare(b.label)),
);
const projectOptions = computed(() =>
  (projectsStore.records || [])
    .map((project) => ({ value: String(project.id), label: project.name }))
    .sort((a, b) => a.label.localeCompare(b.label)),
);

const filterFields = computed(() => (
  isChanges.value
    ? changesFilterFields({
      clients: clientOptions.value,
      projects: projectOptions.value,
    })
    : sendsFilterFields({
      clients: clientOptions.value,
      projects: projectOptions.value,
    })
));

const currentPage = computed(() =>
  isChanges.value ? store.changelog.page : store.emailLog.page,
);
const totalPages = computed(() =>
  isChanges.value ? store.changelog.numPages : store.emailLog.numPages,
);
const totalCount = computed(() =>
  isChanges.value ? store.changelog.count : store.emailLog.count,
);
const errorKey = computed(() => (isChanges.value ? 'changelog_failed' : 'email_log_failed'));
const countLabel = computed(() => {
  const plural = totalCount.value === 1 ? '' : 's';
  return isChanges.value ? `cambio${plural}` : `envío${plural}`;
});

// ---------------------------------------------------------------------------
// Loading
// ---------------------------------------------------------------------------

function activeParams() {
  const mapping = isChanges.value ? CHANGES_PARAM_MAPPING : SENDS_PARAM_MAPPING;
  return buildExportParams(currentFilters.value, mapping);
}

async function load(page = 1) {
  const params = { page, ...activeParams() };
  const result = isChanges.value
    ? await store.fetchChangelog(params)
    : await store.fetchEmailLog(params);
  if (!result.success) {
    notify.error({
      title: isChanges.value
        ? 'No se pudo cargar el historial'
        : 'No se pudo cargar el registro de envíos',
      detail: result.message,
    });
  }
}

// One debounce for every filter change, not just the free-text ones: the
// panel's text fields emit per keystroke, and a select landing 250ms later
// is imperceptible next to the round-trip it saves.
let loadTimer = null;
function scheduleLoad() {
  if (loadTimer) clearTimeout(loadTimer);
  loadTimer = setTimeout(() => load(1), 250);
}

function goToPage(page) {
  const target = Math.min(Math.max(1, page), totalPages.value || 1);
  if (target === currentPage.value) return;
  load(target);
}

// ---------------------------------------------------------------------------
// Tab counts
// ---------------------------------------------------------------------------

const counts = ref({ sends: {}, changes: {} });
const activeCounts = computed(() => counts.value[tab.value] || {});

/**
 * Ask the server what each tab is worth.
 *
 * Deliberately not tied to the filter watcher: a tab's count is a property of
 * its own definition, so it only moves when the tabs or the data do — not
 * every time somebody types into the search box.
 */
async function refreshCounts() {
  const scope = tab.value;
  const specs = [
    { id: 'all', filters: {} },
    ...displayTabs.value.map((entry) => ({
      id: entry.id,
      filters: entry.filters || {},
    })),
  ];
  const result = await store.fetchHistoryTabCounts(scope, specs);
  if (result.success) {
    counts.value = { ...counts.value, [scope]: result.counts };
  }
}

// ---------------------------------------------------------------------------
// Tab ↔ filters ↔ chips
// ---------------------------------------------------------------------------

const builtinById = computed(() => new Map(
  displayTabs.value.filter((entry) => entry.builtin).map((entry) => [String(entry.id), entry]),
));

/** True while every key the tab pins still holds the tab's value. */
function stillMatches(entry) {
  return Object.entries(entry.filters || {}).every(([key, value]) =>
    sameFilters({ [key]: currentFilters.value[key] }, { [key]: value }),
  );
}

function onSelectTab(tabId) {
  // Re-clicking the tab that is already on clears it, the way a toggle reads.
  if (builtinById.value.has(String(tabId)) && String(tabId) === activeTabId.value) {
    active.value.selectTab('all');
    return;
  }
  active.value.selectTab(tabId);
}

function onFiltersUpdate(next) {
  Object.assign(currentFilters.value, next);
  // Editing a builtin's filters out from under it must un-light the tab; the
  // saved ones instead absorb the edit (that is what the • marker reports).
  const entry = builtinById.value.get(activeTabId.value);
  if (entry && !stillMatches(entry)) {
    active.value.activeTabId.value = 'all';
  }
}

function onClearSearch() {
  active.value.searchInput.value = '';
  currentFilters.value.search = '';
}

function onResetFilters() {
  active.value.resetFilters();
}

async function onCreateTab(name) {
  const created = await active.value.saveTab(name);
  if (!created) {
    notify.error({ title: 'No se pudo guardar la pestaña' });
    return;
  }
  refreshCounts();
}

async function onRenameTab(tabId, name) {
  await active.value.renameTab(tabId, name);
}

async function onDeleteTab(tabId) {
  await active.value.deleteTab(tabId);
  refreshCounts();
}

async function onRestoreTab(tabId) {
  await active.value.restoreTab(tabId);
  refreshCounts();
}

async function onRebaseTab(tabId) {
  await active.value.rebaseTab(tabId);
}

// ---------------------------------------------------------------------------
// Diagnosis: what was sent, and sending it again
// ---------------------------------------------------------------------------

const bodyModalOpen = ref(false);
const bodyEntry = ref(null);
const retryingId = ref(null);

function openBody(entry) {
  bodyEntry.value = entry;
  bodyModalOpen.value = true;
}

async function retrySend(entry) {
  retryingId.value = entry.id;
  const result = await store.retryEmailLog(entry.id);
  retryingId.value = null;
  if (!result.success) {
    notify.error({
      title: 'No se pudo reintentar el envío',
      detail: result.message,
    });
    return;
  }
  notify.success({
    title: 'Reenviado',
    detail: `Salió de nuevo a ${entry.recipient}.`,
  });
  // The retry is a new row, and it lands first: reload rather than patch, so
  // the list and its counts tell the same story.
  load(1);
  refreshCounts();
}

// ---------------------------------------------------------------------------
// Wiring
// ---------------------------------------------------------------------------

watch(() => [sends.currentFilters, changes.currentFilters], scheduleLoad, { deep: true });

// The saved tabs arrive after mount, and a tab's definition can change under
// the auto-save, so the badges follow the tab set rather than being asked for
// once — otherwise every saved tab would sit there without a count.
watch(
  () => displayTabs.value.map(
    (entry) => `${entry.id}:${JSON.stringify(entry.filters || {})}`,
  ).join('|'),
  refreshCounts,
);

watch(tab, async (value) => {
  const query = { ...route.query, tab: value };
  // Hand the query string over: the outgoing subtab's filters go, then the
  // incoming one writes its own. Awaiting the replace keeps the second write
  // from reading a stale route.
  for (const key of URL_FILTER_KEYS) delete query[key];
  await router.replace({ query });
  active.value.syncUrl();
  load(1);
  refreshCounts();
});

onMounted(async () => {
  load(1);
  // Options for the client and project filters. Failures are silent on
  // purpose: an empty dropdown is a smaller problem than a blocked page.
  Promise.all([
    clientsStore.fetchClients({ limit: 500, silent: true }),
    projectsStore.fetchProjects(),
  ]).catch(() => {});
  refreshCounts();
});

usePanelRefresh(() => {
  load(currentPage.value);
  refreshCounts();
});

onBeforeUnmount(() => {
  if (loadTimer) clearTimeout(loadTimer);
});
</script>
