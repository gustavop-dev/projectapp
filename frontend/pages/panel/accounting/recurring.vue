<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Pagos recurrentes</h1>
        <p class="text-sm text-text-subtle mt-1">
          Suscripciones y costos operativos que se repiten mes a mes o año a año.
        </p>
      </div>
      <BaseButton
        variant="primary"
        size="md"
        data-testid="recurring-new-button"
        @click="openCreateModal"
      >
        <PlusIcon class="w-4 h-4" />
        <span>Nuevo pago recurrente</span>
      </BaseButton>
    </div>

    <AccountingSubnav active="recurring" />

    <!-- Stat cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
      <AccountingStatCard
        label="Costo mensual (COP)"
        :value="money(monthlyCopTotal)"
        sub="Pagos activos prorrateados por mes"
      />
      <div class="bg-surface rounded-xl border border-border-muted shadow-sm p-4 sm:p-5">
        <p class="text-xs text-text-muted uppercase tracking-wider mb-2">Por frecuencia</p>
        <p v-if="frequencyEntries.length === 0" class="text-xs text-text-subtle">Sin pagos activos.</p>
        <dl v-else class="space-y-1 text-sm">
          <div
            v-for="[label, total] in frequencyEntries"
            :key="label"
            class="flex items-center justify-between"
          >
            <dt class="text-text-muted">{{ label }}</dt>
            <dd class="tabular-nums text-text-default">{{ money(total) }}</dd>
          </div>
        </dl>
      </div>
      <div class="bg-surface rounded-xl border border-border-muted shadow-sm p-4 sm:p-5">
        <p class="text-xs text-text-muted uppercase tracking-wider mb-2">Por método de pago</p>
        <p v-if="methodEntries.length === 0" class="text-xs text-text-subtle">Sin pagos activos.</p>
        <dl v-else class="space-y-1 text-sm">
          <div
            v-for="[label, total] in methodEntries"
            :key="label"
            class="flex items-center justify-between"
          >
            <dt class="text-text-muted">{{ label }}</dt>
            <dd class="tabular-nums text-text-default">{{ money(total) }}</dd>
          </div>
        </dl>
      </div>
    </div>

    <!-- Saved filter tabs -->
    <ProposalFilterTabs
      :tabs="savedTabs"
      :active-tab-id="activeTabId"
      :is-tab-limit-reached="isTabLimitReached"
      @select="selectTab"
      @create="handleCreateTab"
      @rename="renameTab"
      @delete="deleteTab"
    />

    <!-- Search + Filter toggle -->
    <div class="flex items-center gap-2 mb-5">
      <BaseInput
        v-model="searchInput"
        type="text"
        placeholder="Buscar por nombre o notas..."
        data-testid="recurring-search-input"
        class="w-full sm:max-w-xs"
      />
      <UiFilterToggleButton
        :open="isFilterPanelOpen"
        :count="activeFilterCount"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      />
      <AccountingExportButton section="recurring" :params="exportParams" />
    </div>

    <!-- Filter panel -->
    <AccountingFilterPanel
      :fields="filterFields"
      :model-value="currentFilters"
      :is-open="isFilterPanelOpen"
      :results-count="filteredRows.length"
      :search-value="currentFilters.search"
      @update:model-value="Object.assign(currentFilters, $event)"
      @reset="resetFilters"
      @clear-search="searchInput = ''"
    />

    <!-- Error -->
    <AccountingErrorState
      v-if="store.error === 'fetch_failed'"
      title="No se pudieron cargar los pagos recurrentes"
      :retrying="store.isLoading"
      @retry="loadRecords"
    />

    <!-- Empty -->
    <BaseEmptyState
      v-else-if="!store.isLoading && filteredRows.length === 0"
      :title="hasActiveFilters ? 'Sin resultados con esos filtros' : 'No hay pagos recurrentes aún'"
      :description="hasActiveFilters
        ? 'Ajusta o limpia los filtros para ver más registros.'
        : 'Registra la primera suscripción o costo operativo.'"
    >
      <template #actions>
        <BaseButton
          v-if="hasActiveFilters"
          variant="secondary"
          size="sm"
          @click="resetFilters"
        >
          Limpiar filtros
        </BaseButton>
        <BaseButton v-else variant="primary" size="sm" @click="openCreateModal">
          <PlusIcon class="w-4 h-4" />
          <span>Nuevo pago recurrente</span>
        </BaseButton>
      </template>
    </BaseEmptyState>

    <template v-else>
      <AccountingTable
        :loading="store.isLoading"
        :highlight-id="lastMutatedId"
        :columns="columns"
        :rows="pagedRows"
        :highlight-query="currentFilters.search"
        :sort-key="sortKey"
        :sort-dir="sortDir"
        @edit="openEditModal"
        @delete="confirmDelete"
        @sort="toggleSort"
      >
        <template #cell-price="{ row }">
          <span class="tabular-nums">{{ formatMoney(Number(row.price), row.currency) }}</span>
        </template>
        <template #cell-billing_day="{ row }">
          {{ row.billing_day || '—' }}
        </template>
        <template #cell-cost_type_label="{ row }">
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium"
            :class="row.cost_type === 'variable'
              ? 'bg-warning-soft text-warning-strong'
              : 'bg-surface-raised text-text-muted'"
          >
            {{ row.cost_type_label }}
          </span>
        </template>
        <template #cell-is_active="{ row }">
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium"
            :class="row.is_active
              ? 'bg-success-soft text-success-strong'
              : 'bg-surface-raised text-text-muted'"
          >
            {{ row.is_active ? 'Activo' : 'Inactivo' }}
          </span>
        </template>
      </AccountingTable>

      <BasePagination
        v-if="!store.isLoading && filteredRows.length > 0"
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
    <RecurringPaymentFormModal
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
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import AccountingFilterPanel from '~/components/accounting/AccountingFilterPanel.vue';
import AccountingExportButton from '~/components/accounting/AccountingExportButton.vue';
import RecurringPaymentFormModal from '~/components/accounting/RecurringPaymentFormModal.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseInput from '~/components/base/BaseInput.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import UiFilterToggleButton from '~/components/ui/FilterToggleButton.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useAccountingCrudPage } from '~/composables/useAccountingCrudPage';
import {
  useAccountingFilters,
  matchBoolean,
  matchEquals,
  matchIncludes,
  matchNumberRange,
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
  activeTabId,
  isFilterPanelOpen,
  activeFilterCount,
  hasActiveFilters,
  isTabLimitReached,
  applyFilters,
  resetFilters,
  selectTab,
  saveTab,
  deleteTab,
  renameTab,
} = useAccountingFilters({
  viewName: 'accounting_recurring',
  defaults: {
    frequency: [],
    payment_method: [],
    currency: '',
    cost_type: '',
    price_min: '',
    price_max: '',
    is_active: '',
  },
  matchers: {
    frequency: matchIncludes('frequency', 'frequency'),
    payment_method: matchIncludes('payment_method', 'payment_method'),
    currency: matchEquals('currency', 'currency'),
    cost_type: matchEquals('cost_type', 'cost_type'),
    priceRange: matchNumberRange('price', 'price_min', 'price_max'),
    isActive: matchBoolean('is_active', 'is_active'),
  },
  searchFields: ['name', 'notes'],
});

const filterFields = [
  {
    kind: 'multi',
    key: 'frequency',
    label: 'Frecuencia',
    options: [
      { value: 'monthly', label: 'Mensual' },
      { value: 'annual', label: 'Anual' },
      { value: 'biennial', label: 'Cada 2 años' },
      { value: 'triennial', label: 'Cada 3 años' },
    ],
  },
  {
    kind: 'multi',
    key: 'payment_method',
    label: 'Método de pago',
    options: [
      { value: 'cash', label: 'Efectivo' },
      { value: 'credit_card', label: 'T.C' },
    ],
  },
  {
    kind: 'segmented',
    key: 'currency',
    label: 'Moneda',
    options: [
      { value: '', label: 'Todas' },
      { value: 'COP', label: 'COP' },
      { value: 'USD', label: 'USD' },
    ],
  },
  {
    kind: 'segmented',
    key: 'cost_type',
    label: 'Tipo',
    options: [
      { value: '', label: 'Todos' },
      { value: 'fixed', label: 'Fijo' },
      { value: 'variable', label: 'Variable' },
    ],
  },
  { kind: 'range', minKey: 'price_min', maxKey: 'price_max', label: 'Precio', type: 'money' },
  {
    kind: 'segmented',
    key: 'is_active',
    label: 'Estado',
    options: [
      { value: '', label: 'Todos' },
      { value: 'true', label: 'Activos' },
      { value: 'false', label: 'Inactivos' },
    ],
  },
];

const EXPORT_MAPPING = {
  frequency: 'frequency',
  payment_method: 'payment_method',
  currency: 'currency',
  cost_type: 'cost_type',
  price_min: 'amount_min',
  price_max: 'amount_max',
  is_active: 'is_active',
  search: 'q',
};

const exportParams = computed(() =>
  buildExportParams(currentFilters, EXPORT_MAPPING),
);

// -------------------------------------------------------------------
// Data + table
// -------------------------------------------------------------------

const columns = [
  { key: 'name', label: 'Nombre', sortable: true },
  { key: 'price', label: 'Precio', align: 'right' },
  { key: 'cop_equivalent', label: 'Equiv. COP', format: 'money', sortable: true },
  { key: 'payment_method_label', label: 'Método' },
  { key: 'frequency_label', label: 'Frecuencia' },
  { key: 'billing_day', label: 'Día', align: 'center', sortable: true },
  { key: 'cost_type_label', label: 'Tipo' },
  { key: 'is_active', label: 'Estado' },
];

const filteredRows = computed(() => applyFilters(store.recurringPayments));

const {
  isModalOpen: showFormModal,
  editingRecord,
  openCreateModal,
  lastMutatedId,
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
  handleCreateFilterTab: handleCreateTab,
  sortKey,
  sortDir,
  toggleSort,
} = useAccountingCrudPage({
  entity: 'recurring',
  store,
  filteredRecords: filteredRows,
  labels: {
    created: 'Pago recurrente creado',
    updated: 'Pago recurrente actualizado',
    deleted: 'Pago recurrente eliminado',
    saveErrorTitle: (editing) =>
      editing
        ? 'No se pudo actualizar el pago recurrente'
        : 'No se pudo crear el pago recurrente',
    deleteErrorTitle: 'No se pudo eliminar el pago recurrente',
    deleteTitle: 'Eliminar pago recurrente',
    deleteMessage: (record) =>
      `Esto eliminará "${record.name}" de forma permanente. ` +
      'Esta acción no se puede deshacer.',
  },
  // Refetch: the monthly COP total meta is computed server-side.
  onAfterMutation: loadRecords,
  saveTab,
  isFilterPanelOpen,
});

const monthlyCopTotal = computed(() => store.metaFor('recurring').monthly_cop_total ?? 0);
const frequencyEntries = computed(() => Object.entries(store.recurringTotalsByFrequency));
const methodEntries = computed(() => Object.entries(store.recurringTotalsByMethod));

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

async function loadRecords() {
  const result = await store.fetchRecords('recurring');
  if (!result.success) {
    notify.error({ title: 'No se pudieron cargar los pagos recurrentes', detail: result.message });
  }
}

onMounted(loadRecords);
usePanelRefresh(loadRecords);
</script>
