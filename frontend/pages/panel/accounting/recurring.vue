<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Contabilidad — Pagos recurrentes</h1>
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
        v-model="currentFilters.search"
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
      Cargando pagos recurrentes...
    </div>

    <template v-else>
      <AccountingTable
        :columns="columns"
        :rows="pagedRows"
        @edit="openEditModal"
        @delete="confirmDelete"
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
import { computed, onMounted, ref, watch } from 'vue';
import { PlusIcon } from '@heroicons/vue/24/outline';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingFilterPanel from '~/components/accounting/AccountingFilterPanel.vue';
import RecurringPaymentFormModal from '~/components/accounting/RecurringPaymentFormModal.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseInput from '~/components/base/BaseInput.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import UiFilterToggleButton from '~/components/ui/FilterToggleButton.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { usePagination } from '~/composables/usePagination';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import {
  useAccountingFilters,
  matchEquals,
  matchIncludes,
  matchNumberRange,
} from '~/composables/useAccountingFilters';
import { useAccountingStore } from '~/stores/accounting';
import { formatMoney } from '~/utils/formatMoney';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useAccountingStore();
const notify = usePanelNotify();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

// -------------------------------------------------------------------
// Filters
// -------------------------------------------------------------------

function matchIsActive() {
  const fn = (record, _value, filters) => {
    if (filters.is_active === '') return true;
    return record.is_active === (filters.is_active === 'true');
  };
  fn.keys = ['is_active'];
  return fn;
}

const {
  currentFilters,
  savedTabs,
  activeTabId,
  isFilterPanelOpen,
  activeFilterCount,
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
    isActive: matchIsActive(),
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
  { kind: 'range', minKey: 'price_min', maxKey: 'price_max', label: 'Precio' },
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

function handleCreateTab(name) {
  saveTab(name);
  isFilterPanelOpen.value = true;
}

// -------------------------------------------------------------------
// Data + table
// -------------------------------------------------------------------

const columns = [
  { key: 'name', label: 'Nombre' },
  { key: 'price', label: 'Precio', align: 'right' },
  { key: 'cop_equivalent', label: 'Equiv. COP', format: 'money' },
  { key: 'payment_method_label', label: 'Método' },
  { key: 'frequency_label', label: 'Frecuencia' },
  { key: 'billing_day', label: 'Día', align: 'center' },
  { key: 'cost_type_label', label: 'Tipo' },
  { key: 'is_active', label: 'Estado' },
];

const filteredRows = computed(() => applyFilters(store.recurringPayments));

const {
  currentPage,
  totalPages,
  totalItems,
  rangeFrom,
  rangeTo,
  paginatedItems: pagedRows,
  goTo,
  next,
  prev,
  reset: resetPage,
} = usePagination(filteredRows, { pageSize: 15 });

watch(filteredRows, () => resetPage(), { deep: false });

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

// -------------------------------------------------------------------
// Create / edit / delete
// -------------------------------------------------------------------

const showFormModal = ref(false);
const editingRecord = ref(null);

function openCreateModal() {
  editingRecord.value = null;
  showFormModal.value = true;
}

function openEditModal(record) {
  editingRecord.value = record;
  showFormModal.value = true;
}

function closeFormModal() {
  showFormModal.value = false;
  editingRecord.value = null;
}

async function submitForm(payload) {
  const isEdit = !!editingRecord.value;
  const result = isEdit
    ? await store.updateRecord('recurring', editingRecord.value.id, payload)
    : await store.createRecord('recurring', payload);
  if (result.success) {
    closeFormModal();
    notify.success(isEdit ? 'Pago recurrente actualizado' : 'Pago recurrente creado');
    // Refetch to refresh the server-side monthly total meta.
    await loadRecords();
  } else {
    notify.error({
      title: isEdit
        ? 'No se pudo actualizar el pago recurrente'
        : 'No se pudo crear el pago recurrente',
      detail: result.message,
    });
  }
}

function confirmDelete(record) {
  requestConfirm({
    title: 'Eliminar pago recurrente',
    message: `Esto eliminará "${record.name}" de forma permanente. Esta acción no se puede deshacer.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    cancelText: 'Cancelar',
    onConfirm: async () => {
      const result = await store.deleteRecord('recurring', record.id);
      if (result.success) {
        notify.success('Pago recurrente eliminado');
        await loadRecords();
      } else {
        notify.error({
          title: 'No se pudo eliminar el pago recurrente',
          detail: result.message,
        });
      }
    },
  });
}
</script>
