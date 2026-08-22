<template>
  <div :class="PAGE_MAX_WIDTH">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Pagos recurrentes</h1>
        <p class="text-sm text-text-subtle mt-1">
          Suscripciones y costos operativos que se repiten mes a mes o año a año.
        </p>
      </div>
      <div class="flex items-center gap-2">
        <BaseButton
          variant="secondary"
          size="md"
          data-testid="recurring-manage-categories"
          @click="showCategoriesModal = true"
        >
          <TagIcon class="w-4 h-4" />
          <span>Gestionar categorías</span>
        </BaseButton>
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
    </div>

    <AccountingSubnav active="recurring" />

    <!-- Stat cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
      <AccountingStatCard
        data-testid="recurring-monthly-cop-total"
        label="Costo mensual (COP)"
        :value="money(monthlyCopTotal)"
        sub="Pagos activos prorrateados por mes"
      />
      <AccountingStatCard
        label="Costo mensual (USD)"
        :value="monthlyUsdTotal != null ? formatMoney(monthlyUsdTotal, 'USD') : '—'"
        :sub="usdKpiSub"
        tone="brand"
      />
      <div class="bg-surface rounded-xl border border-border-muted shadow-sm p-4 sm:p-5">
        <div class="flex items-center justify-between gap-2 mb-2">
          <p class="text-xs text-text-muted uppercase tracking-wider">Desglose mensual</p>
          <BaseSegmented
            v-model="breakdownView"
            :options="breakdownOptions"
            size="sm"
          />
        </div>
        <p v-if="breakdownEntries.length === 0" class="text-xs text-text-subtle">Sin pagos activos.</p>
        <dl v-else class="space-y-1 text-sm" data-testid="recurring-breakdown">
          <div
            v-for="[label, total] in breakdownEntries"
            :key="label"
            class="flex items-center justify-between gap-3"
          >
            <dt class="text-text-muted truncate">{{ label }}</dt>
            <dd class="tabular-nums text-text-default whitespace-nowrap">{{ money(total) }}</dd>
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
      @restore="restoreTab"
      @rebase="rebaseTab"
      @reorder="reorderTabs"
    />

    <!-- Search + Filter toggle + view mode -->
    <div class="flex flex-wrap items-center gap-2 mb-5">
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
      <BaseSegmented
        v-model="viewMode"
        :options="viewModeOptions"
        size="sm"
        class="ml-auto"
        data-testid="recurring-view-mode"
      />
      <!-- Divider, not a third segment: this opens a modal, it is not another
           way of listing the table. -->
      <span class="w-px h-6 bg-border-muted" aria-hidden="true" />
      <BaseButton
        variant="secondary"
        size="sm"
        data-testid="recurring-charts-button"
        @click="showChartsModal = true"
      >
        <ChartPieIcon class="w-4 h-4" />
        <span>Gráfico</span>
      </BaseButton>
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
      <p
        v-if="isGrouped && groupedWeightSort && !store.isLoading"
        class="text-xs text-text-subtle mb-2"
        data-testid="recurring-weight-sort-hint"
      >
        Orden por peso activo: quítalo para reordenar arrastrando.
      </p>
      <p
        v-else-if="isGrouped && !canReorder && !store.isLoading"
        class="text-xs text-text-subtle mb-2"
        data-testid="recurring-reorder-hint"
      >
        Limpia la búsqueda y los filtros para poder reordenar arrastrando.
      </p>

      <RecurringGroupedTable
        v-if="isGrouped"
        :loading="store.isLoading"
        :highlight-id="lastMutatedId"
        :columns="groupedColumns"
        :groups="displayGroups"
        :highlight-query="currentFilters.search"
        :drag-enabled="canReorder"
        :collapsed-ids="collapsedGroupIds"
        :weight-sort="groupedWeightSort"
        sort-column-key="monthly_cop_cost"
        @edit="openEditModal"
        @delete="confirmDelete"
        @reorder="handleReorder"
        @toggle-group="toggleGroup"
        @toggle-weight-sort="toggleGroupedWeightSort"
      >
        <template #cell-price="{ row }">
          <span class="tabular-nums">{{ formatMoney(Number(row.price), row.currency) }}</span>
        </template>
        <template #cell-monthly_price="{ row }">
          <span class="tabular-nums">{{ formatMonthlyPrice(row) }}</span>
        </template>
        <template #cell-monthly_cop_cost="{ row }">
          <span class="tabular-nums">{{ formatMonthlyCop(row.monthly_cop_cost) }}</span>
          <span
            class="block text-xs text-text-subtle tabular-nums"
            :data-testid="`recurring-weight-${row.id}`"
            title="Peso sobre el total mensual COP de pagos activos"
          >
            {{ formatPercent(row.weight_pct) }}
          </span>
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
      </RecurringGroupedTable>

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
          <template #cell-monthly_price="{ row }">
            <span class="tabular-nums">{{ formatMonthlyPrice(row) }}</span>
          </template>
          <template #cell-monthly_cop_cost="{ row }">
            <span class="tabular-nums">{{ formatMonthlyCop(row.monthly_cop_cost) }}</span>
            <span
              class="block text-xs text-text-subtle tabular-nums"
              :data-testid="`recurring-weight-${row.id}`"
              title="Peso sobre el total mensual COP de pagos activos"
            >
              {{ formatPercent(row.weight_pct) }}
            </span>
          </template>
          <template #cell-category_name="{ row }">
            <span
              class="text-xs px-2.5 py-1 rounded-full font-medium bg-surface-raised text-text-muted"
            >
              {{ row.category_name || 'Sin categoría' }}
            </span>
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
    </template>

    <!-- Create / edit modal -->
    <RecurringPaymentFormModal
      :open="showFormModal"
      :record="editingRecord"
      :saving="store.isUpdating"
      :categories="store.recurringCategories"
      :usd-exchange-rate="store.metaFor('recurring').usd_exchange_rate"
      @close="closeFormModal"
      @submit="submitForm"
    />

    <!-- Charts -->
    <RecurringChartsModal
      :open="showChartsModal"
      :rows="filteredRows"
      :categories="store.recurringCategories"
      :usd-exchange-rate="store.metaFor('recurring').usd_exchange_rate"
      :inherited-chips="inheritedChartChips"
      @close="showChartsModal = false"
      @clear-filters="resetFilters"
    />

    <!-- Category catalog -->
    <RecurringCategoriesModal
      :open="showCategoriesModal"
      :categories="store.recurringCategories"
      :saving="store.isUpdating"
      @close="showCategoriesModal = false"
      @create="createCategory"
      @rename="renameCategory"
      @delete="confirmDeleteCategory"
      @reorder="reorderCategories"
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
import { PAGE_MAX_WIDTH } from '~/utils/tableLayout';
import { computed, onMounted, ref } from 'vue';
import { ChartPieIcon, PlusIcon, TagIcon } from '@heroicons/vue/24/outline';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import RecurringGroupedTable from '~/components/accounting/RecurringGroupedTable.vue';
import RecurringCategoriesModal from '~/components/accounting/RecurringCategoriesModal.vue';
import RecurringChartsModal from '~/components/accounting/stats/RecurringChartsModal.vue';
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
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import UiFilterToggleButton from '~/components/ui/FilterToggleButton.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useAccountingCrudPage } from '~/composables/useAccountingCrudPage';
import { useRecurringViewMode } from '~/composables/useRecurringViewMode';
import {
  useAccountingFilters,
  matchBooleanIncludes,
  matchIncludes,
  matchNumberRange,
} from '~/composables/useAccountingFilters';
import { useAccountingStore } from '~/stores/accounting';
import { buildExportParams } from '~/utils/accountingExportParams';
import { formatMoney } from '~/utils/formatMoney';
import { addWeightPct, formatPercent } from '~/utils/percent';
import {
  FREQUENCY_OPTIONS,
  formatMonthlyCop,
  formatMonthlyPrice,
  groupByCategory,
  withGroupWeights,
} from '~/utils/recurring';

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
  restoreTab,
  rebaseTab,
  reorderTabs,
} = useAccountingFilters({
  viewName: 'accounting_recurring',
  defaults: {
    category: [],
    frequency: [],
    payment_method: [],
    currency: [],
    cost_type: [],
    price_min: '',
    price_max: '',
    is_active: [],
  },
  matchers: {
    category: matchIncludes('category', 'category'),
    frequency: matchIncludes('frequency', 'frequency'),
    payment_method: matchIncludes('payment_method', 'payment_method'),
    currency: matchIncludes('currency', 'currency'),
    cost_type: matchIncludes('cost_type', 'cost_type'),
    priceRange: matchNumberRange('price', 'price_min', 'price_max'),
    isActive: matchBooleanIncludes('is_active', 'is_active'),
  },
  searchFields: ['name', 'notes'],
});

const filterFields = computed(() => [
  {
    kind: 'multi',
    key: 'category',
    label: 'Categoría',
    options: store.recurringCategories.map((category) => ({
      value: category.id,
      label: category.name,
    })),
  },
  {
    kind: 'multi',
    key: 'frequency',
    label: 'Frecuencia',
    // "Personalizada" matches every custom cycle, whatever its month count.
    options: FREQUENCY_OPTIONS,
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
]);

const EXPORT_MAPPING = {
  category: 'category',
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

// Shared by both views. The two monthly columns are derived server-side and
// read-only: they answer "what does this actually cost me per month", which
// the raw price cannot when periodicities differ.
// The three amounts are variants of one number, so `group: 'money'` draws them
// together and puts the wider gap before Frecuencia, which is another kind of
// information. `size` is only declared where the format cannot imply it: Tipo
// and Estado render badges through slots, not `format: 'badge'`.
// `hideBelow` collapses the least load-bearing columns first — name, monthly
// equivalent and status survive every width.
const SHARED_COLUMNS = [
  { key: 'name', label: 'Nombre', size: 'name', sortable: true },
  { key: 'price', label: 'Precio', align: 'right', size: 'money', group: 'money', hideBelow: 'lg' },
  { key: 'monthly_price', label: 'Precio mensual', align: 'right', size: 'money', group: 'money', hideBelow: 'lg' },
  { key: 'monthly_cop_cost', label: 'Equiv. COP mensual', format: 'money', group: 'money', sortable: true },
  { key: 'frequency_label', label: 'Frecuencia', hideBelow: 'lg' },
  { key: 'payment_method_label', label: 'Método', hideBelow: 'lg' },
  { key: 'billing_day', label: 'Día', align: 'center', size: 'tiny', sortable: true, hideBelow: 'md' },
  // Preformatted by the API (like frequency_label), so both view modes render
  // it as plain text and neither has to format a date.
  { key: 'next_charge_label', label: 'Próximo cobro', size: 'text', hideBelow: 'md' },
  { key: 'cost_type_label', label: 'Tipo', size: 'badge', hideBelow: 'md' },
  { key: 'is_active', label: 'Estado', size: 'badge' },
];

// Classic view needs the category as a column; the grouped view has it as a
// group header, so repeating it in every row would be noise.
const columns = [
  SHARED_COLUMNS[0],
  { key: 'category_name', label: 'Categoría', hideBelow: 'lg' },
  ...SHARED_COLUMNS.slice(1),
];

const groupedColumns = SHARED_COLUMNS.map(({ sortable, ...col }) => col);

const filteredRows = computed(() => applyFilters(store.recurringPayments));

// Contribution to the weight base: only active rows count, matching the
// server's monthly_cop_total meta. Inactive rows show 0% and stay out of the
// base, so the active ones read as a 100% composition. NOTE: the grouped
// view's footer grand total still sums active AND inactive rows ("total of
// what is listed"); the percentages deliberately use the active-only base.
function activeMonthlyCop(row) {
  return row.is_active ? Number(row.monthly_cop_cost) || 0 : 0;
}

const weightedRows = computed(() => addWeightPct(filteredRows.value, activeMonthlyCop));

const activeBase = computed(() =>
  filteredRows.value.reduce((total, row) => total + activeMonthlyCop(row), 0),
);

// -------------------------------------------------------------------
// View mode, grouping and manual order
// -------------------------------------------------------------------

const { viewMode } = useRecurringViewMode();
const isGrouped = computed(() => viewMode.value === 'grouped');

const viewModeOptions = [
  { value: 'grouped', label: 'Agrupado' },
  { value: 'table', label: 'Clásico' },
];

const collapsedGroupIds = ref([]);
const showCategoriesModal = ref(false);
const showChartsModal = ref(false);

/**
 * Human labels for whatever the table is filtering by.
 *
 * The charts modal reads the same filtered rows the table shows, so its total
 * can legitimately differ from the "Costo mensual (COP)" card. Spelling the
 * filters out as chips is what turns that from a discrepancy into a caption.
 */
const inheritedChartChips = computed(() => {
  const chips = [];

  if (activeTabId.value !== 'all') {
    const tab = savedTabs.value.find((saved) => String(saved.id) === String(activeTabId.value));
    if (tab) chips.push(`Vista: ${tab.name}`);
  }
  if (currentFilters.search) chips.push(`Búsqueda: "${currentFilters.search}"`);

  filterFields.value.forEach((field) => {
    if (field.kind === 'range') {
      const min = currentFilters[field.minKey];
      const max = currentFilters[field.maxKey];
      if (min || max) {
        chips.push(`${field.label}: ${min ? money(min) : '—'} a ${max ? money(max) : '—'}`);
      }
      return;
    }
    const labelFor = (value) =>
      field.options.find((option) => String(option.value) === String(value))?.label
      ?? String(value);
    const current = currentFilters[field.key];
    if (Array.isArray(current)) {
      if (current.length) chips.push(`${field.label}: ${current.map(labelFor).join(', ')}`);
    } else if (current !== '' && current != null) {
      chips.push(`${field.label}: ${labelFor(current)}`);
    }
  });

  return chips;
});

const groups = computed(() =>
  withGroupWeights(
    groupByCategory(weightedRows.value, store.recurringCategories),
    activeBase.value,
  ),
);

// Temporary weight-sort for the grouped view: '' | 'desc' | 'asc'. It only
// reorders what is DISPLAYED — the persisted manual order is never written.
const groupedWeightSort = ref('');

function toggleGroupedWeightSort() {
  groupedWeightSort.value =
    groupedWeightSort.value === '' ? 'desc'
      : groupedWeightSort.value === 'desc' ? 'asc' : '';
}

// Groups AND the rows inside them sort by weight while the toggle is on:
// the point is scanning "what weighs most", which a catalog-ordered list of
// groups would break. Copies only — clearing the sort falls back to the
// untouched manual order.
const displayGroups = computed(() => {
  if (!groupedWeightSort.value) return groups.value;
  const direction = groupedWeightSort.value === 'desc' ? -1 : 1;
  return [...groups.value]
    .sort((a, b) => direction * (a.groupWeightPct - b.groupWeightPct))
    .map((group) => ({
      ...group,
      rows: [...group.rows].sort((a, b) => direction * (a.weight_pct - b.weight_pct)),
    }));
});

/**
 * Dragging is only offered on the complete list in its manual order.
 * Reordering a filtered view would let the operator arrange rows around
 * neighbours they cannot see, and a weight-sorted view would persist an
 * order they meant as a temporary reading.
 */
const canReorder = computed(() =>
  isGrouped.value && !hasActiveFilters.value && !groupedWeightSort.value,
);

function toggleGroup(id) {
  collapsedGroupIds.value = collapsedGroupIds.value.includes(id)
    ? collapsedGroupIds.value.filter((groupId) => groupId !== id)
    : [...collapsedGroupIds.value, id];
}

async function handleReorder(items) {
  const result = await store.reorderRecurring(items);
  if (!result.success) {
    notify.error({
      title: 'No se pudo guardar el nuevo orden',
      detail: result.message || '',
    });
  }
}

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
  requestConfirm,
  runMutation,
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
  resetPageOn: currentFilters,
  store,
  filteredRecords: weightedRows,
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
  // Refetch: the monthly COP total meta is computed server-side, and the
  // per-category payment counts shift whenever a record moves group.
  onAfterMutation: loadAll,
  // Sorting the COP column sorts by weight: identical order for active rows
  // (the % is monotonic on the value), inactive rows (0%) sink to the end.
  sortAccessors: { monthly_cop_cost: 'weight_pct' },
  sortDefaults: { monthly_cop_cost: 'desc' },
  saveTab,
  isFilterPanelOpen,
});

const monthlyCopTotal = computed(() => store.metaFor('recurring').monthly_cop_total ?? 0);

const monthlyUsdTotal = computed(() => {
  const value = store.metaFor('recurring').monthly_usd_total;
  return value == null ? null : Number(value);
});

const usdKpiSub = computed(() => {
  const meta = store.metaFor('recurring');
  const parts = [];
  if (meta.usd_exchange_rate != null) {
    parts.push(`Tasa: ${formatMoney(Number(meta.usd_exchange_rate), 'COP')}/USD`);
  }
  if (Number(meta.usd_native_total ?? 0) > 0) {
    parts.push(`Nativos USD: ${formatMoney(Number(meta.usd_native_total), 'USD')}`);
  }
  return parts.join(' · ');
});
const breakdownView = ref('category');
const breakdownOptions = [
  { value: 'category', label: 'Categoría' },
  { value: 'frequency', label: 'Frecuencia' },
  { value: 'payment_method', label: 'Método' },
];

// Every breakdown is monthly, so all three add up to the "Costo mensual (COP)"
// card above them.
const breakdownEntries = computed(() => {
  if (breakdownView.value === 'category') {
    return store.recurringTotalsByCategory.map((entry) => [entry.name, entry.total]);
  }
  return Object.entries(store.recurringMonthlyTotalsBy(breakdownView.value));
});

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

// -------------------------------------------------------------------
// Category catalog
// -------------------------------------------------------------------

async function createCategory(name) {
  await runMutation(
    () => store.createRecord('recurringCategories', { name }),
    {
      successTitle: 'Categoría creada',
      errorTitle: 'No se pudo crear la categoría',
    },
  );
}

async function renameCategory({ id, name }) {
  await runMutation(
    () => store.updateRecord('recurringCategories', id, { name }),
    {
      successTitle: 'Categoría actualizada',
      errorTitle: 'No se pudo renombrar la categoría',
    },
  );
}

function confirmDeleteCategory(category) {
  requestConfirm({
    title: 'Eliminar categoría',
    message: `Esto eliminará "${category.name}". Los recurrentes que la usen deben moverse antes.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    cancelText: 'Cancelar',
    onConfirm: () => runMutation(
      () => store.deleteRecord('recurringCategories', category.id),
      {
        successTitle: 'Categoría eliminada',
        errorTitle: 'No se pudo eliminar la categoría',
      },
    ),
  });
}

async function reorderCategories(ids) {
  const result = await store.reorderRecurringCategories(ids);
  if (!result.success) {
    notify.error({
      title: 'No se pudo guardar el orden de las categorías',
      detail: result.message || '',
    });
  }
}

async function loadCategories() {
  const result = await store.fetchRecords('recurringCategories');
  if (!result.success) {
    notify.error({ title: 'No se pudieron cargar las categorías', detail: result.message });
  }
}

async function loadRecords() {
  const result = await store.fetchRecords('recurring');
  if (!result.success) {
    notify.error({ title: 'No se pudieron cargar los pagos recurrentes', detail: result.message });
  }
}

async function loadAll() {
  // Categories first: grouping and the category filter both read them.
  await loadCategories();
  await loadRecords();
}

onMounted(loadAll);
usePanelRefresh(loadAll);
</script>
