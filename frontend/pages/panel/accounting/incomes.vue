<template>
  <div>
    <AccountingSubnav active="incomes" />

    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Ingresos</h1>
        <p class="text-sm text-text-subtle mt-1">
          Ingresos esperados y líquidos del negocio, con su reparto entre socios.
        </p>
      </div>
      <BaseButton
        variant="primary"
        size="md"
        data-testid="incomes-new-button"
        @click="openCreateModal"
      >
        <PlusIcon class="w-4 h-4" />
        <span>Nuevo ingreso</span>
      </BaseButton>
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
        placeholder="Buscar por concepto o notas..."
        data-testid="incomes-search-input"
        class="w-full sm:max-w-xs"
        @input="onSearchInput"
      />
      <UiFilterToggleButton
        :open="isFilterPanelOpen"
        :count="activeFilterCount"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      />
    </div>

    <!-- Filter panel -->
    <AccountingFilterPanel
      :fields="filterFields"
      :model-value="currentFilters"
      :is-open="isFilterPanelOpen"
      @update:model-value="Object.assign(currentFilters, $event)"
      @reset="handleResetFilters"
    />

    <!-- Summary chips (filtered rows) -->
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <span
        class="text-xs px-2.5 py-1 rounded-full bg-surface-raised text-text-muted font-medium tabular-nums"
        data-testid="incomes-total-expected"
      >
        Total esperado: {{ formatMoney(totalExpected) }}
      </span>
      <span
        class="text-xs px-2.5 py-1 rounded-full bg-success-soft text-success-strong font-medium tabular-nums"
        data-testid="incomes-total-liquid"
      >
        Total líquido: {{ formatMoney(totalLiquid) }}
      </span>
    </div>

    <!-- Loading -->
    <div v-if="store.isLoading" class="text-center py-16 text-text-subtle text-sm">
      Cargando ingresos...
    </div>

    <!-- Empty -->
    <div
      v-else-if="filteredRecords.length === 0"
      class="text-center py-16 text-text-subtle text-sm"
    >
      {{ hasActiveFilters ? 'No se encontraron ingresos con ese criterio.' : 'No hay ingresos aún.' }}
    </div>

    <!-- Table -->
    <template v-else>
      <AccountingTable
        :columns="columns"
        :rows="pagedRecords"
        @edit="openEditModal"
        @delete="confirmDeleteRecord"
      >
        <template #cell-kind_label="{ row }">
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium"
            :class="row.kind === 'liquid'
              ? 'bg-success-soft text-success-strong'
              : 'bg-surface-raised text-text-muted'"
          >
            {{ row.kind_label }}
          </span>
        </template>
        <template #cell-destination_label="{ row }">
          {{ row.destination === 'pocket' ? row.destination_label : '—' }}
        </template>
      </AccountingTable>

      <BasePagination
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
    <IncomeFormModal
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
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { PlusIcon } from '@heroicons/vue/24/outline';
import ConfirmModal from '~/components/ConfirmModal.vue';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingFilterPanel from '~/components/accounting/AccountingFilterPanel.vue';
import IncomeFormModal from '~/components/accounting/IncomeFormModal.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { usePagination } from '~/composables/usePagination';
import {
  useAccountingFilters,
  matchDateRange,
  matchNumberRange,
  matchEquals,
} from '~/composables/useAccountingFilters';
import { useAccountingStore } from '~/stores/accounting';
import { formatMoney } from '~/utils/formatMoney';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useAccountingStore();
const notify = usePanelNotify();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } =
  useConfirmModal();

// -------------------------------------------------------------------
// Filters
// -------------------------------------------------------------------

const matchPartner = (record, value) => {
  if (!value) return true;
  if (value === 'gustavo') return Number(record.gustavo_amount) > 0;
  if (value === 'carlos') return Number(record.carlos_amount) > 0;
  if (value === 'projectapp') {
    return record.destination === 'pocket' || Number(record.company_amount) > 0;
  }
  return true;
};
matchPartner.keys = ['partner'];

const {
  currentFilters,
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
  viewName: 'accounting_income',
  defaults: {
    periodAfter: '',
    periodBefore: '',
    amountMin: '',
    amountMax: '',
    kind: '',
    partner: '',
  },
  matchers: {
    period: matchDateRange('period_date', 'periodAfter', 'periodBefore'),
    amount: matchNumberRange('total_amount', 'amountMin', 'amountMax'),
    kind: matchEquals('kind', 'kind'),
    partner: matchPartner,
  },
  searchFields: ['concept', 'notes'],
});

const filterFields = [
  { kind: 'daterange', label: 'Mes', minKey: 'periodAfter', maxKey: 'periodBefore' },
  { kind: 'range', label: 'Total', minKey: 'amountMin', maxKey: 'amountMax', type: 'number' },
  {
    kind: 'segmented',
    key: 'kind',
    label: 'Tipo',
    options: [
      { value: '', label: 'Todos' },
      { value: 'expected', label: 'Esperado' },
      { value: 'liquid', label: 'Líquido' },
    ],
  },
  {
    kind: 'segmented',
    key: 'partner',
    label: 'Socio',
    options: [
      { value: '', label: 'Todos' },
      { value: 'gustavo', label: 'Gustavo' },
      { value: 'carlos', label: 'Carlos' },
      { value: 'projectapp', label: 'ProjectApp' },
    ],
  },
];

// Debounced search (mirrors the clients page pattern).
const searchInput = ref(currentFilters.search);
let searchTimer = null;

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    currentFilters.search = searchInput.value;
  }, 250);
}

watch(
  () => currentFilters.search,
  (value) => {
    if (value !== searchInput.value) searchInput.value = value;
  },
);

function handleCreateFilterTab(name) {
  saveTab(name);
  isFilterPanelOpen.value = true;
}

function handleResetFilters() {
  resetFilters();
  isFilterPanelOpen.value = false;
}

// -------------------------------------------------------------------
// Data + pagination
// -------------------------------------------------------------------

const filteredRecords = computed(() => applyFilters(store.incomes));

const {
  currentPage,
  totalPages,
  totalItems,
  rangeFrom,
  rangeTo,
  paginatedItems: pagedRecords,
  goTo: goToPage,
  next: nextPage,
  prev: prevPage,
  reset: resetPage,
} = usePagination(filteredRecords, { pageSize: 15 });

watch(filteredRecords, () => resetPage(), { deep: false });

const totalExpected = computed(() =>
  filteredRecords.value
    .filter((r) => r.kind === 'expected')
    .reduce((sum, r) => sum + (Number(r.total_amount) || 0), 0),
);

const totalLiquid = computed(() =>
  filteredRecords.value
    .filter((r) => r.kind === 'liquid')
    .reduce((sum, r) => sum + (Number(r.total_amount) || 0), 0),
);

const columns = [
  { key: 'concept', label: 'Concepto' },
  { key: 'kind_label', label: 'Tipo' },
  { key: 'period_label', label: 'Mes' },
  { key: 'total_amount', label: 'Total', format: 'money' },
  { key: 'gustavo_amount', label: 'Gustavo', format: 'money' },
  { key: 'carlos_amount', label: 'Carlos', format: 'money' },
  { key: 'destination_label', label: 'Destino' },
];

async function loadRecords() {
  await store.fetchRecords('incomes');
}

onMounted(loadRecords);
usePanelRefresh(loadRecords);
onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer);
});

// -------------------------------------------------------------------
// Create / edit modal
// -------------------------------------------------------------------

const isModalOpen = ref(false);
const editingRecord = ref(null);

function openCreateModal() {
  editingRecord.value = null;
  isModalOpen.value = true;
}

function openEditModal(record) {
  editingRecord.value = record;
  isModalOpen.value = true;
}

function closeModal() {
  isModalOpen.value = false;
  editingRecord.value = null;
}

async function handleSubmit(payload) {
  const editing = editingRecord.value;
  const result = editing
    ? await store.updateRecord('incomes', editing.id, payload)
    : await store.createRecord('incomes', payload);

  if (result.success) {
    notify.success({ title: editing ? 'Ingreso actualizado' : 'Ingreso creado' });
    closeModal();
    // Keep the pocket ledger consistent when the income feeds the pocket.
    if (payload.destination === 'pocket' || editing?.pocket_movement) {
      store.fetchRecords('pocket');
    }
  } else {
    notify.error({ title: 'No se pudo guardar', detail: result.message || '' });
  }
}

// -------------------------------------------------------------------
// Delete
// -------------------------------------------------------------------

function confirmDeleteRecord(record) {
  requestConfirm({
    title: 'Eliminar ingreso',
    message: `Esto eliminará el ingreso "${record.concept}" de forma permanente. Esta acción no se puede deshacer.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    cancelText: 'Cancelar',
    onConfirm: async () => {
      const result = await store.deleteRecord('incomes', record.id);
      if (result.success) {
        notify.success('Ingreso eliminado');
        if (record.pocket_movement) store.fetchRecords('pocket');
      } else {
        notify.error({ title: 'No se pudo eliminar', detail: result.message || '' });
      }
    },
  });
}
</script>
