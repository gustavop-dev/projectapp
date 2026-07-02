<template>
  <div>
    <AccountingSubnav active="pocket" />

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

    <!-- Loading -->
    <div v-if="store.isLoading" class="text-center py-16 text-text-subtle text-sm">
      Cargando movimientos...
    </div>

    <!-- Empty -->
    <div
      v-else-if="filteredMovements.length === 0"
      class="text-center py-16 text-text-subtle text-sm"
    >
      {{ hasActiveFilters ? 'No se encontraron movimientos con ese criterio.' : 'No hay movimientos aún.' }}
    </div>

    <!-- Table -->
    <template v-else>
      <AccountingTable
        :columns="columns"
        :rows="pagedMovements"
        @edit="handleEdit"
        @delete="handleDelete"
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
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { PlusIcon } from '@heroicons/vue/24/outline';
import ConfirmModal from '~/components/ConfirmModal.vue';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingFilterPanel from '~/components/accounting/AccountingFilterPanel.vue';
import PocketMovementFormModal from '~/components/accounting/PocketMovementFormModal.vue';
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

const pocketBalance = computed(() => {
  const meta = store.metaFor('pocket');
  return meta.balance !== undefined && meta.balance !== null
    ? Number(meta.balance)
    : store.pocketBalance;
});

const filteredMovements = computed(() =>
  applyFilters(store.pocketWithRunningBalance),
);

const {
  currentPage,
  totalPages,
  totalItems,
  rangeFrom,
  rangeTo,
  paginatedItems: pagedMovements,
  goTo: goToPage,
  next: nextPage,
  prev: prevPage,
  reset: resetPage,
} = usePagination(filteredMovements, { pageSize: 15 });

watch(filteredMovements, () => resetPage(), { deep: false });

const columns = [
  { key: 'movement_date', label: 'Fecha', format: 'date' },
  { key: 'concept', label: 'Concepto' },
  { key: 'direction_label', label: 'Tipo' },
  { key: 'amount', label: 'Valor', format: 'money' },
  { key: 'running_balance', label: 'Saldo', format: 'money' },
];

async function loadRecords() {
  await store.fetchRecords('pocket');
}

onMounted(loadRecords);
usePanelRefresh(loadRecords);
onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer);
});

// -------------------------------------------------------------------
// Auto-managed guard
// -------------------------------------------------------------------

function warnAutoManaged() {
  notify.warning({
    title: 'Movimiento automático',
    detail: 'Se gestiona desde el ingreso o gasto vinculado.',
  });
}

// -------------------------------------------------------------------
// Create / edit modal
// -------------------------------------------------------------------

const isModalOpen = ref(false);
const editingRecord = ref(null);

function openCreateModal() {
  editingRecord.value = null;
  isModalOpen.value = true;
}

function handleEdit(record) {
  if (record.is_auto_managed) {
    warnAutoManaged();
    return;
  }
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
    ? await store.updateRecord('pocket', editing.id, payload)
    : await store.createRecord('pocket', payload);

  if (result.success) {
    notify.success({ title: editing ? 'Movimiento actualizado' : 'Movimiento creado' });
    closeModal();
  } else {
    notify.error({ title: 'No se pudo guardar', detail: result.message || '' });
  }
}

// -------------------------------------------------------------------
// Delete
// -------------------------------------------------------------------

function handleDelete(record) {
  if (record.is_auto_managed) {
    warnAutoManaged();
    return;
  }
  requestConfirm({
    title: 'Eliminar movimiento',
    message: `Esto eliminará el movimiento "${record.concept}" de forma permanente. Esta acción no se puede deshacer.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    cancelText: 'Cancelar',
    onConfirm: async () => {
      const result = await store.deleteRecord('pocket', record.id);
      if (result.success) {
        notify.success('Movimiento eliminado');
      } else {
        notify.error({ title: 'No se pudo eliminar', detail: result.message || '' });
      }
    },
  });
}
</script>
