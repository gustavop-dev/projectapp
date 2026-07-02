<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Contabilidad — Ads</h1>
        <p class="text-sm text-text-subtle mt-1">
          Gastos en publicidad por plataforma y tarjeta de origen.
        </p>
      </div>
      <BaseButton
        variant="primary"
        size="md"
        data-testid="ads-new-button"
        @click="openCreateModal"
      >
        <PlusIcon class="w-4 h-4" />
        <span>Nuevo gasto en Ads</span>
      </BaseButton>
    </div>

    <AccountingSubnav active="ads" />

    <!-- Stat card -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
      <AccountingStatCard
        label="Total filtrado"
        :value="money(filteredTotal)"
        :sub="`${filteredRows.length} registro${filteredRows.length === 1 ? '' : 's'}`"
      />
    </div>

    <!-- Filter toggle -->
    <div class="flex items-center justify-end gap-2 mb-5">
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
      @reset="resetFilters"
    />

    <!-- Loading -->
    <div v-if="store.isLoading" class="text-center py-16 text-text-subtle text-sm">
      Cargando gastos en Ads...
    </div>

    <template v-else>
      <AccountingTable
        :columns="columns"
        :rows="pagedRows"
        @edit="openEditModal"
        @delete="confirmDelete"
      >
        <template #cell-origin_card="{ row }">
          {{ row.origin_card || '—' }}
        </template>
        <template #cell-accumulated="{ row }">
          <span class="tabular-nums text-text-muted">
            {{ row.accumulated !== null && row.accumulated !== undefined && row.accumulated !== ''
              ? money(row.accumulated)
              : '—' }}
          </span>
        </template>
      </AccountingTable>

      <p class="text-xs text-text-muted mt-2">
        El acumulado se calcula sobre el historial completo.
      </p>

      <BasePagination
        v-if="filteredRows.length > 0"
        :current-page="currentPage"
        :total-pages="totalPages"
        :total-items="totalItems"
        :range-from="rangeFrom"
        :range-to="rangeTo"
        class="mt-4"
        @prev="prev"
        @next="next"
        @go="goTo"
      />
    </template>

    <!-- Create / edit modal -->
    <AdSpendFormModal
      :open="showFormModal"
      :record="editingRecord"
      :saving="store.isUpdating"
      @close="closeFormModal"
      @submit="submitForm"
    />

    <!-- Confirm delete -->
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
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingFilterPanel from '~/components/accounting/AccountingFilterPanel.vue';
import AdSpendFormModal from '~/components/accounting/AdSpendFormModal.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import UiFilterToggleButton from '~/components/ui/FilterToggleButton.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useAccountingCrudPage } from '~/composables/useAccountingCrudPage';
import {
  useAccountingFilters,
  matchDateRange,
  matchIncludes,
  matchNumberRange,
} from '~/composables/useAccountingFilters';
import { useAccountingStore } from '~/stores/accounting';
import { formatMoney } from '~/utils/formatMoney';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useAccountingStore();
const notify = usePanelNotify();

// -------------------------------------------------------------------
// Filters (no saved tabs UI: the backend has no 'accounting_ads' view choice)
// -------------------------------------------------------------------

const {
  currentFilters,
  isFilterPanelOpen,
  activeFilterCount,
  applyFilters,
  resetFilters,
} = useAccountingFilters({
  viewName: 'accounting_ads',
  defaults: {
    spend_from: '',
    spend_to: '',
    origin_card: [],
    platform: [],
    amount_min: '',
    amount_max: '',
  },
  matchers: {
    spendRange: matchDateRange('spend_date', 'spend_from', 'spend_to'),
    origin_card: matchIncludes('origin_card', 'origin_card'),
    platform: matchIncludes('platform', 'platform'),
    amountRange: matchNumberRange('amount', 'amount_min', 'amount_max'),
  },
});

const originCardOptions = computed(() => {
  const values = new Set();
  store.adsRecords.forEach((record) => {
    if (record.origin_card) values.add(record.origin_card);
  });
  return Array.from(values).sort().map((value) => ({ value, label: value }));
});

const filterFields = computed(() => [
  { kind: 'daterange', minKey: 'spend_from', maxKey: 'spend_to', label: 'Fecha' },
  { kind: 'multi', key: 'origin_card', label: 'Tarjeta', options: originCardOptions.value },
  {
    kind: 'multi',
    key: 'platform',
    label: 'Plataforma',
    options: [
      { value: 'facebook', label: 'Facebook Ads' },
      { value: 'google', label: 'Google Ads' },
      { value: 'other', label: 'Otro' },
    ],
  },
  { kind: 'range', minKey: 'amount_min', maxKey: 'amount_max', label: 'Valor' },
]);

// -------------------------------------------------------------------
// Data + table (keeps the backend chronological order)
// -------------------------------------------------------------------

const columns = [
  { key: 'spend_date', label: 'Fecha', format: 'date' },
  { key: 'platform_label', label: 'Plataforma' },
  { key: 'origin_card', label: 'Tarjeta' },
  { key: 'amount', label: 'Valor', format: 'money' },
  { key: 'accumulated', label: 'Acumulado', align: 'right' },
];

const filteredRows = computed(() => applyFilters(store.adsRecords));

const filteredTotal = computed(() =>
  filteredRows.value.reduce((total, record) => total + (Number(record.amount) || 0), 0),
);

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

const {
  isModalOpen: showFormModal,
  editingRecord,
  openCreateModal,
  openEditModal,
  closeModal: closeFormModal,
  handleSubmit: submitForm,
  confirmDeleteRecord: confirmDelete,
  confirmState,
  handleConfirmed,
  handleCancelled,
  currentPage,
  totalPages,
  totalItems,
  rangeFrom,
  rangeTo,
  pagedRecords: pagedRows,
  prevPage: prev,
  nextPage: next,
  goToPage: goTo,
} = useAccountingCrudPage({
  entity: 'ads',
  store,
  filteredRecords: filteredRows,
  labels: {
    created: 'Gasto en Ads creado',
    updated: 'Gasto en Ads actualizado',
    deleted: 'Gasto en Ads eliminado',
    saveErrorTitle: (editing) =>
      editing ? 'No se pudo actualizar el gasto en Ads' : 'No se pudo crear el gasto en Ads',
    deleteErrorTitle: 'No se pudo eliminar el gasto en Ads',
    deleteTitle: 'Eliminar gasto en Ads',
    deleteMessage: (record) =>
      `Esto eliminará el gasto del ${record.spend_date} por ${money(record.amount)} ` +
      'de forma permanente. Esta acción no se puede deshacer.',
  },
  // Refetch: the accumulated column depends on the full history order.
  onAfterMutation: loadRecords,
});

async function loadRecords() {
  const result = await store.fetchRecords('ads');
  if (!result.success) {
    notify.error({ title: 'No se pudieron cargar los gastos en Ads', detail: result.message });
  }
}

onMounted(loadRecords);
usePanelRefresh(loadRecords);
</script>
