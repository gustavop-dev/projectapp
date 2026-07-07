<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Bolsillo ProjectApp</h1>
        <p class="text-sm text-text-subtle mt-1">
          Libro de movimientos del bolsillo compartido, con saldo corrido.
        </p>
      </div>
      <BaseButton
        variant="primary"
        size="md"
        data-testid="pocket-new-button"
        @click="openCreateModal"
      >
        <PlusIcon class="w-4 h-4" />
        <span>Nuevo movimiento</span>
      </BaseButton>
    </div>

    <AccountingSubnav active="pocket" />

    <!-- Balance card -->
    <div class="bg-surface rounded-xl border border-border-muted shadow-sm p-5 sm:p-6 mb-6">
      <p class="text-xs text-text-muted uppercase tracking-wider mb-1">Saldo del bolsillo</p>
      <p
        class="text-3xl font-semibold tabular-nums"
        :class="pocketBalance >= 0 ? 'text-success-strong' : 'text-danger-strong'"
        data-testid="pocket-balance"
      >
        {{ formatMoney(pocketBalance) }}
      </p>
    </div>

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

    <!-- Search + Filter toggle -->
    <div class="flex items-center gap-2 mb-5">
      <BaseInput
        v-model="searchInput"
        type="text"
        placeholder="Buscar por concepto..."
        data-testid="pocket-search-input"
        class="w-full sm:max-w-xs"
      />
      <UiFilterToggleButton
        :open="isFilterPanelOpen"
        :count="activeFilterCount"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      />
      <AccountingExportButton section="pocket" :params="exportParams" />
    </div>

    <!-- Filter panel -->
    <AccountingFilterPanel
      :fields="filterFields"
      :model-value="currentFilters"
      :is-open="isFilterPanelOpen"
      :results-count="filteredMovements.length"
      :search-value="currentFilters.search"
      @update:model-value="Object.assign(currentFilters, $event)"
      @reset="handleResetFilters"
      @clear-search="searchInput = ''"
    />

    <!-- Error -->
    <AccountingErrorState
      v-if="store.error === 'fetch_failed'"
      title="No se pudieron cargar los movimientos"
      :retrying="store.isLoading"
      @retry="loadRecords"
    />

    <!-- Empty -->
    <BaseEmptyState
      v-else-if="!store.isLoading && filteredMovements.length === 0"
      :title="hasActiveFilters ? 'Sin resultados con esos filtros' : 'No hay movimientos aún'"
      :description="hasActiveFilters
        ? 'Ajusta o limpia los filtros para ver más registros.'
        : 'Registra el primer movimiento del Bolsillo ProjectApp.'"
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
          <span>Nuevo movimiento</span>
        </BaseButton>
      </template>
    </BaseEmptyState>

    <!-- Table -->
    <template v-else>
      <AccountingTable
        :loading="store.isLoading"
        :highlight-id="lastMutatedId"
        :columns="columns"
        :rows="pagedMovements"
        :highlight-query="currentFilters.search"
        :sort-key="sortKey"
        :sort-dir="sortDir"
        @edit="handleEdit"
        @delete="handleDelete"
        @sort="toggleSort"
      >
        <template #cell-concept="{ row }">
          <span class="inline-flex items-center gap-2">
            <span>{{ row.concept }}</span>
            <span
              v-if="row.is_auto_managed"
              class="text-[10px] px-1.5 py-0.5 rounded-full bg-surface-raised text-text-muted font-medium uppercase tracking-wide"
              title="Movimiento gestionado automáticamente desde el ingreso o gasto vinculado"
            >
              Auto
            </span>
          </span>
        </template>
        <template #cell-direction_label="{ row }">
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium"
            :class="row.direction === 'in'
              ? 'bg-success-soft text-success-strong'
              : 'bg-danger-soft text-danger-strong'"
          >
            {{ row.direction_label }}
          </span>
        </template>
        <template #cell-amount="{ row }">
          <span
            class="tabular-nums"
            :class="row.direction === 'out' ? 'text-danger-strong' : 'text-text-muted'"
          >
            {{ (row.direction === 'out' ? '-' : '') + formatMoney(row.amount) }}
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
    <PocketMovementFormModal
      :open="isModalOpen"
      :record="editingRecord"
      :saving="store.isUpdating"
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
import PocketMovementFormModal from '~/components/accounting/PocketMovementFormModal.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useAccountingCrudPage } from '~/composables/useAccountingCrudPage';
import {
  useAccountingFilters,
  matchDateRange,
  matchNumberRange,
  matchEquals,
} from '~/composables/useAccountingFilters';
import { useAccountingStore } from '~/stores/accounting';
import { buildExportParams } from '~/utils/accountingExportParams';
import { formatMoney } from '~/utils/formatMoney';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useAccountingStore();
const notify = usePanelNotify();

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
  viewName: 'accounting_pocket',
  defaults: {
    dateAfter: '',
    dateBefore: '',
    direction: '',
    amountMin: '',
    amountMax: '',
  },
  matchers: {
    date: matchDateRange('movement_date', 'dateAfter', 'dateBefore'),
    direction: matchEquals('direction', 'direction'),
    amount: matchNumberRange('amount', 'amountMin', 'amountMax'),
  },
  searchFields: ['concept'],
});

const filterFields = [
  { kind: 'daterange', label: 'Fecha', minKey: 'dateAfter', maxKey: 'dateBefore' },
  {
    kind: 'segmented',
    key: 'direction',
    label: 'Tipo',
    options: [
      { value: '', label: 'Todos' },
      { value: 'in', label: 'Ingreso' },
      { value: 'out', label: 'Egreso' },
    ],
  },
  { kind: 'range', label: 'Valor', minKey: 'amountMin', maxKey: 'amountMax', type: 'number' },
];

const EXPORT_MAPPING = {
  dateAfter: 'date_from',
  dateBefore: 'date_to',
  direction: 'direction',
  amountMin: 'amount_min',
  amountMax: 'amount_max',
  search: 'q',
};

const exportParams = computed(() =>
  buildExportParams(currentFilters, EXPORT_MAPPING),
);

// -------------------------------------------------------------------
// Data + CRUD controller (modal, delete confirm, pagination)
// -------------------------------------------------------------------

// Server meta is the single owner of the headline balance.
const pocketBalance = computed(() => Number(store.metaFor('pocket').balance ?? 0));

const filteredMovements = computed(() =>
  applyFilters(store.pocketWithRunningBalance),
);

function warnAutoManaged() {
  notify.warning({
    title: 'Movimiento automático',
    detail: 'Se gestiona desde el ingreso o gasto vinculado.',
  });
}

function guardAutoManaged(record) {
  if (record.is_auto_managed) {
    warnAutoManaged();
    return false;
  }
  return true;
}

const {
  isModalOpen,
  editingRecord,
  openCreateModal,
  lastMutatedId,
  openEditModal: handleEdit,
  closeModal,
  handleSubmit,
  confirmDeleteRecord: handleDelete,
  confirmState,
  handleConfirmed,
  handleCancelled,
  currentPage,
  totalPages,
  totalItems,
  rangeFrom,
  rangeTo,
  pagedRecords: pagedMovements,
  prevPage,
  nextPage,
  goToPage,
  handleCreateFilterTab,
  handleResetFilters,
  sortKey,
  sortDir,
  toggleSort,
} = useAccountingCrudPage({
  entity: 'pocket',
  store,
  filteredRecords: filteredMovements,
  labels: {
    created: 'Movimiento creado',
    updated: 'Movimiento actualizado',
    deleted: 'Movimiento eliminado',
    saveErrorTitle: 'No se pudo guardar',
    deleteErrorTitle: 'No se pudo eliminar',
    deleteTitle: 'Eliminar movimiento',
    deleteMessage: (record) =>
      `Esto eliminará el movimiento "${record.concept}" de forma permanente. ` +
      'Esta acción no se puede deshacer.',
  },
  beforeEdit: guardAutoManaged,
  beforeDelete: guardAutoManaged,
  saveTab,
  resetFilters,
  isFilterPanelOpen,
});

const columns = [
  { key: 'movement_date', label: 'Fecha', format: 'date', sortable: true },
  { key: 'concept', label: 'Concepto', sortable: true },
  { key: 'direction_label', label: 'Tipo' },
  { key: 'amount', label: 'Valor', format: 'money', sortable: true },
  { key: 'running_balance', label: 'Saldo', format: 'money' },
];

async function loadRecords() {
  await store.fetchRecords('pocket');
}

onMounted(loadRecords);
usePanelRefresh(loadRecords);
</script>
