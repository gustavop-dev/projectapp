<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Tarjetas</h1>
        <p class="text-sm text-text-subtle mt-1">
          Registros semanales de disponible y deuda de las tarjetas de crédito.
        </p>
      </div>
      <BaseButton
        variant="primary"
        size="md"
        data-testid="cards-new-button"
        @click="openCreateModal"
      >
        <PlusIcon class="w-4 h-4" />
        <span>Nuevo registro</span>
      </BaseButton>
    </div>

    <AccountingSubnav active="cards" />

    <!-- Saved filter tabs -->
    <ProposalFilterTabs
      :tabs="savedTabs"
      :active-tab-id="filterTabId"
      :is-tab-limit-reached="isTabLimitReached"
      @select="selectFilterTab"
      @create="handleCreateFilterTab"
      @rename="renameFilterTab"
      @delete="deleteFilterTab"
    />

    <!-- Search + Filter toggle + Export -->
    <div class="flex items-center gap-2 mb-5">
      <BaseInput
        v-model="searchInput"
        type="text"
        placeholder="Buscar por tarjeta o notas..."
        data-testid="cards-search-input"
        class="w-full sm:max-w-xs"
      />
      <UiFilterToggleButton
        :open="isFilterPanelOpen"
        :count="activeFilterCount"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      />
      <AccountingExportButton section="card_snapshot" :params="exportParams" />
    </div>

    <!-- Filter panel -->
    <AccountingFilterPanel
      :fields="filterFields"
      :model-value="currentFilters"
      :is-open="isFilterPanelOpen"
      :results-count="filteredRecords.length"
      :search-value="currentFilters.search"
      @update:model-value="Object.assign(currentFilters, $event)"
      @reset="handleResetFilters"
      @clear-search="searchInput = ''"
    />

    <!-- Summary chip (latest debt per card over filtered rows) -->
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <span
        class="text-xs px-2.5 py-1 rounded-full bg-danger-soft text-danger-strong font-medium tabular-nums"
        data-testid="cards-total-debt"
      >
        Deuda total (últimos por tarjeta): {{ formatMoney(latestDebtTotal) }}
      </span>
    </div>

    <!-- Error -->
    <AccountingErrorState
      v-if="store.error === 'fetch_failed'"
      title="No se pudieron cargar los registros de tarjetas"
      :retrying="store.isLoading"
      @retry="loadRecords"
    />

    <!-- Empty -->
    <BaseEmptyState
      v-else-if="!store.isLoading && filteredRecords.length === 0"
      :title="hasActiveFilters ? 'Sin resultados con esos filtros' : 'No hay registros de tarjetas aún'"
      :description="hasActiveFilters
        ? 'Ajusta o limpia los filtros para ver más registros.'
        : 'Registra el primer snapshot de disponible y deuda.'"
    >
      <template #actions>
        <BaseButton
          v-if="hasActiveFilters"
          variant="secondary"
          size="sm"
          @click="handleResetFilters"
        >
          Limpiar filtros
        </BaseButton>
        <BaseButton v-else variant="primary" size="sm" @click="openCreateModal">
          <PlusIcon class="w-4 h-4" />
          <span>Nuevo registro</span>
        </BaseButton>
      </template>
    </BaseEmptyState>

    <!-- Table -->
    <template v-else>
      <AccountingTable
        :loading="store.isLoading"
        :highlight-id="lastMutatedId"
        :columns="columns"
        :rows="pagedRecords"
        :highlight-query="currentFilters.search"
        :sort-key="sortKey"
        :sort-dir="sortDir"
        @edit="openEditModal"
        @delete="confirmDeleteRecord"
        @sort="toggleSort"
      >
        <template #cell-debt_amount="{ row }">
          <span class="tabular-nums text-danger-strong">
            {{ formatMoney(Number(row.debt_amount)) }}
          </span>
        </template>
      </AccountingTable>

      <BasePagination
        v-if="!store.isLoading"
        :current-page="currentPage"
        :total-pages="totalPages"
        :total-items="totalItems"
        :range-from="rangeFrom"
        :range-to="rangeTo"
        class="mt-4"
        @prev="prevPage"
        @next="nextPage"
        @go="goToPage"
      />
    </template>

    <!-- Create/edit modal -->
    <CardSnapshotFormModal
      :open="isModalOpen"
      :record="editingRecord"
      :saving="store.isUpdating"
      :known-cards="knownCards"
      @close="closeModal"
      @submit="handleSubmit"
    />

    <!-- Confirm modal for delete -->
    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      :require-type-text="confirmState.requireTypeText"
      :hide-cancel="confirmState.hideCancel"
      @confirm="handleConfirmed"
      @cancel="handleCancelled"
    />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { PlusIcon } from '@heroicons/vue/24/outline';
import ConfirmModal from '~/components/ConfirmModal.vue';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import AccountingFilterPanel from '~/components/accounting/AccountingFilterPanel.vue';
import AccountingExportButton from '~/components/accounting/AccountingExportButton.vue';
import CardSnapshotFormModal from '~/components/accounting/CardSnapshotFormModal.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useAccountingCrudPage } from '~/composables/useAccountingCrudPage';
import {
  useAccountingFilters,
  matchDateRange,
  matchNumberRange,
  matchIncludes,
} from '~/composables/useAccountingFilters';
import { useAccountingStore } from '~/stores/accounting';
import { buildExportParams } from '~/utils/accountingExportParams';
import { formatMoney } from '~/utils/formatMoney';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useAccountingStore();

// -------------------------------------------------------------------
// Filters
// -------------------------------------------------------------------

const {
  currentFilters,
  searchInput,
  savedTabs,
  activeTabId: filterTabId,
  isFilterPanelOpen,
  hasActiveFilters,
  activeFilterCount,
  isTabLimitReached,
  applyFilters,
  resetFilters,
  selectTab: selectFilterTab,
  saveTab,
  deleteTab: deleteFilterTab,
  renameTab: renameFilterTab,
} = useAccountingFilters({
  viewName: 'accounting_cards',
  defaults: {
    dateAfter: '',
    dateBefore: '',
    debtMin: '',
    debtMax: '',
    cardName: [],
  },
  matchers: {
    date: matchDateRange('snapshot_date', 'dateAfter', 'dateBefore'),
    debt: matchNumberRange('debt_amount', 'debtMin', 'debtMax'),
    cardName: matchIncludes('card_name', 'cardName'),
  },
  searchFields: ['card_name', 'notes'],
});

const knownCards = computed(() =>
  [...new Set(store.cardSnapshots.map((r) => r.card_name))].sort(),
);

const filterFields = computed(() => [
  { kind: 'daterange', label: 'Fecha', minKey: 'dateAfter', maxKey: 'dateBefore' },
  { kind: 'range', label: 'Deuda', minKey: 'debtMin', maxKey: 'debtMax', type: 'money' },
  {
    kind: 'multi',
    key: 'cardName',
    label: 'Tarjeta',
    options: knownCards.value.map((card) => ({ value: card, label: card })),
  },
]);

const EXPORT_MAPPING = {
  dateAfter: 'date_from',
  dateBefore: 'date_to',
  debtMin: 'amount_min',
  debtMax: 'amount_max',
  cardName: 'card_name',
  search: 'q',
};

const exportParams = computed(() =>
  buildExportParams(currentFilters, EXPORT_MAPPING),
);

// -------------------------------------------------------------------
// Data + CRUD controller (modal, delete confirm, pagination)
// -------------------------------------------------------------------

const filteredRecords = computed(() => applyFilters(store.cardSnapshots));

const {
  isModalOpen,
  editingRecord,
  openCreateModal,
  lastMutatedId,
  openEditModal,
  closeModal,
  handleSubmit,
  confirmDeleteRecord,
  confirmState,
  handleConfirmed,
  handleCancelled,
  currentPage,
  totalPages,
  totalItems,
  rangeFrom,
  rangeTo,
  pagedRecords,
  prevPage,
  nextPage,
  goToPage,
  handleCreateFilterTab,
  handleResetFilters,
  sortKey,
  sortDir,
  toggleSort,
} = useAccountingCrudPage({
  entity: 'cards',
  store,
  filteredRecords,
  saveTab,
  resetFilters,
  isFilterPanelOpen,
  labels: {
    entityName: 'registro de tarjeta',
    created: 'Registro de tarjeta creado',
    updated: 'Registro de tarjeta actualizado',
    deleted: 'Registro de tarjeta eliminado',
    saveErrorTitle: 'No se pudo guardar',
    deleteErrorTitle: 'No se pudo eliminar',
    deleteTitle: 'Eliminar registro de tarjeta',
    deleteMessage: (record) =>
      `Esto eliminará el registro de "${record.card_name}" del ${record.snapshot_date} de forma permanente. Esta acción no se puede deshacer.`,
  },
});

const latestDebtTotal = computed(() => {
  const latestByCard = new Map();
  for (const row of filteredRecords.value) {
    const current = latestByCard.get(row.card_name);
    if (!current || row.snapshot_date > current.snapshot_date) {
      latestByCard.set(row.card_name, row);
    }
  }
  return [...latestByCard.values()].reduce(
    (sum, row) => sum + (Number(row.debt_amount) || 0),
    0,
  );
});

const columns = [
  { key: 'card_name', label: 'Tarjeta', sortable: true },
  { key: 'snapshot_date', label: 'Fecha', sortable: true },
  { key: 'available_amount', label: 'Disponible', format: 'money', sortable: true },
  { key: 'debt_amount', label: 'Deuda', sortable: true },
  { key: 'notes', label: 'Notas' },
];

async function loadRecords() {
  await store.fetchRecords('cards');
}

onMounted(loadRecords);
usePanelRefresh(loadRecords);
</script>
