<template>
  <div>
    <AccountingSubnav active="expenses" />

    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Gastos</h1>
        <p class="text-sm text-text-subtle mt-1">
          Gastos del negocio y personales, con su reparto entre socios.
        </p>
      </div>
      <BaseButton
        variant="primary"
        size="md"
        data-testid="expenses-new-button"
        @click="openCreateModal"
      >
        <PlusIcon class="w-4 h-4" />
        <span>Nuevo gasto</span>
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
        data-testid="expenses-search-input"
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

    <!-- Summary chip (filtered rows) -->
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <span
        class="text-xs px-2.5 py-1 rounded-full bg-danger-soft text-danger-strong font-medium tabular-nums"
        data-testid="expenses-total-filtered"
      >
        Total gastos: {{ formatMoney(totalFiltered) }}
      </span>
    </div>

    <!-- Loading -->
    <div v-if="store.isLoading" class="text-center py-16 text-text-subtle text-sm">
      Cargando gastos...
    </div>

    <!-- Empty -->
    <div
      v-else-if="filteredRecords.length === 0"
      class="text-center py-16 text-text-subtle text-sm"
    >
      {{ hasActiveFilters ? 'No se encontraron gastos con ese criterio.' : 'No hay gastos aún.' }}
    </div>

    <!-- Table -->
    <template v-else>
      <AccountingTable
        :columns="columns"
        :rows="pagedRecords"
        @edit="openEditModal"
        @delete="confirmDeleteRecord"
      >
        <template #cell-category_label="{ row }">
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium"
            :class="row.category === 'personal'
              ? 'bg-warning-soft text-warning-strong'
              : 'bg-surface-raised text-text-muted'"
          >
            {{ row.category_label }}
          </span>
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
    <ExpenseFormModal
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
import ExpenseFormModal from '~/components/accounting/ExpenseFormModal.vue';
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
  matchIncludes,
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
  viewName: 'accounting_expense',
  defaults: {
    periodAfter: '',
    periodBefore: '',
    amountMin: '',
    amountMax: '',
    categories: [],
    paidFrom: [],
  },
  matchers: {
    period: matchDateRange('period_date', 'periodAfter', 'periodBefore'),
    amount: matchNumberRange('total_amount', 'amountMin', 'amountMax'),
    categories: matchIncludes('category', 'categories'),
    paidFrom: matchIncludes('paid_from', 'paidFrom'),
  },
  searchFields: ['concept', 'notes'],
});

const filterFields = [
  { kind: 'daterange', label: 'Mes', minKey: 'periodAfter', maxKey: 'periodBefore' },
  { kind: 'range', label: 'Total', minKey: 'amountMin', maxKey: 'amountMax', type: 'number' },
  {
    kind: 'multi',
    key: 'categories',
    label: 'Categoría',
    options: [
      { value: 'business', label: 'Negocio' },
      { value: 'personal', label: 'Personal' },
    ],
  },
  {
    kind: 'multi',
    key: 'paidFrom',
    label: 'Pagado desde',
    options: [
      { value: 'partners', label: 'Socios' },
      { value: 'pocket', label: 'Bolsillo ProjectApp' },
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

const filteredRecords = computed(() => applyFilters(store.expenses));

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

const totalFiltered = computed(() =>
  filteredRecords.value.reduce((sum, r) => sum + (Number(r.total_amount) || 0), 0),
);

const columns = [
  { key: 'concept', label: 'Concepto' },
  { key: 'period_label', label: 'Mes' },
  { key: 'category_label', label: 'Categoría' },
  { key: 'paid_from_label', label: 'Pagado desde' },
  { key: 'total_amount', label: 'Total', format: 'money' },
  { key: 'gustavo_amount', label: 'Gustavo', format: 'money' },
  { key: 'carlos_amount', label: 'Carlos', format: 'money' },
];

async function loadRecords() {
  await store.fetchRecords('expenses');
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
    ? await store.updateRecord('expenses', editing.id, payload)
    : await store.createRecord('expenses', payload);

  if (result.success) {
    notify.success({ title: editing ? 'Gasto actualizado' : 'Gasto creado' });
    closeModal();
    // Keep the pocket ledger consistent when the expense touches the pocket.
    if (payload.paid_from === 'pocket' || editing?.paid_from === 'pocket') {
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
    title: 'Eliminar gasto',
    message: `Esto eliminará el gasto "${record.concept}" de forma permanente. Esta acción no se puede deshacer.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    cancelText: 'Cancelar',
    onConfirm: async () => {
      const result = await store.deleteRecord('expenses', record.id);
      if (result.success) {
        notify.success('Gasto eliminado');
        if (record.paid_from === 'pocket') store.fetchRecords('pocket');
      } else {
        notify.error({ title: 'No se pudo eliminar', detail: result.message || '' });
      }
    },
  });
}
</script>
