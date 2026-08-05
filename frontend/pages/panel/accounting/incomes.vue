<template>
  <div :class="PAGE_MAX_WIDTH">
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

    <AccountingSubnav active="incomes" />

    <!-- KPI cards (year scope, server-computed) -->
    <div class="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
      <AccountingStatCard
        label="Total esperado (año)"
        :value="money(incomesMeta.expected_total)"
      />
      <AccountingStatCard
        label="Total líquido (año)"
        :value="money(incomesMeta.liquid_total)"
        :sub="incomesMeta.received_pct != null ? `${incomesMeta.received_pct}% recibido` : ''"
        tone="success"
      />
      <AccountingStatCard
        label="Mes actual (líquido)"
        :value="money(incomesMeta.current_month_liquid)"
      />
      <AccountingStatCard
        label="Mayor ingreso del año"
        :value="incomesMeta.top_income ? money(incomesMeta.top_income.amount) : '—'"
        :sub="incomesMeta.top_income?.concept || ''"
        tone="brand"
      />
      <AccountingStatCard
        label="Perdido (año)"
        :value="money(incomesMeta.lost_total)"
        :tone="Number(incomesMeta.lost_total) > 0 ? 'danger' : 'default'"
      />
    </div>

    <!-- Quick + saved filter tabs -->
    <ProposalFilterTabs
      :tabs="displayTabs"
      :active-tab-id="filterTabId"
      :is-tab-limit-reached="isTabLimitReached"
      @select="selectFilterTab"
      @create="handleCreateFilterTab"
      @rename="renameFilterTab"
      @delete="deleteFilterTab"
      @restore="restoreFilterTab"
      @rebase="rebaseFilterTab"
    />

    <!-- Search + Filter toggle -->
    <div class="flex items-center gap-2 mb-5">
      <BaseInput
        v-model="searchInput"
        type="text"
        placeholder="Buscar por concepto o notas..."
        data-testid="incomes-search-input"
        class="w-full sm:max-w-xs"
      />
      <UiFilterToggleButton
        :open="isFilterPanelOpen"
        :count="activeFilterCount"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      />
      <AccountingExportButton section="income" :params="exportParams" />
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
      <span
        v-if="totalLost > 0"
        class="text-xs px-2.5 py-1 rounded-full bg-danger-soft text-danger-strong font-medium tabular-nums"
        data-testid="incomes-total-lost"
      >
        Total perdido: {{ formatMoney(totalLost) }}
      </span>
    </div>

    <!-- Error -->
    <AccountingErrorState
      v-if="store.error === 'fetch_failed'"
      title="No se pudieron cargar los ingresos"
      :retrying="store.isLoading"
      @retry="loadRecords"
    />

    <!-- Empty -->
    <BaseEmptyState
      v-else-if="!store.isLoading && filteredRecords.length === 0"
      :title="hasActiveFilters ? 'Sin resultados con esos filtros' : 'No hay ingresos aún'"
      :description="hasActiveFilters
        ? 'Ajusta o limpia los filtros para ver más registros.'
        : 'Registra el primer ingreso esperado o líquido del negocio.'"
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
          <span>Nuevo ingreso</span>
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
        :row-tone="incomeRowTone"
        @edit="openEditModal"
        @delete="confirmDeleteRecord"
        @sort="toggleSort"
      >
        <template #row-actions="{ row }">
          <template v-if="row.kind === 'expected'">
            <button
              type="button"
              class="p-1.5 rounded-md text-text-muted hover:text-success-strong hover:bg-surface-raised transition-colors"
              aria-label="Liquidar"
              title="Liquidar"
              :data-testid="`income-liquidate-${row.id}`"
              @click.stop="openLiquidateModal(row)"
            >
              <BanknotesIcon class="w-5 h-5" />
            </button>
            <BaseButton variant="danger-ghost" icon-only size="sm" v-if="row.payment_status === 'pending'" aria-label="Marcar como perdido" title="Marcar como perdido" :data-testid="`income-write-off-${row.id}`" @click.stop="confirmWriteOff(row)">
              <XCircleIcon class="w-5 h-5" />
            </BaseButton>
          </template>
        </template>
        <template #cell-kind_label="{ row }">
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium"
            :class="KIND_BADGE_CLASSES[row.kind] || KIND_BADGE_CLASSES.expected"
          >
            {{ row.kind_label }}
          </span>
        </template>
        <!-- Collection state gets its own column: sharing the Tipo cell with
             the kind badge wrapped the pills and doubled the row height. -->
        <template #cell-payment_status="{ row }">
          <span
            v-if="row.payment_status"
            class="inline-flex items-center gap-1.5 whitespace-nowrap"
            :data-testid="`income-payment-${row.id}`"
          >
            <span
              v-if="PAYMENT_BADGE_CLASSES[row.payment_status]"
              class="text-xs px-2.5 py-1 rounded-full font-medium"
              :class="PAYMENT_BADGE_CLASSES[row.payment_status]"
            >
              {{ row.payment_status_label }}
            </span>
            <span v-else class="text-text-subtle">—</span>
            <span
              v-if="row.payment_status === 'partial'"
              class="text-2xs text-warning-strong tabular-nums"
            >
              faltan {{ formatMoney(Number(row.pending_amount)) }}
            </span>
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
    <IncomeFormModal
      :open="isModalOpen"
      :record="editingRecord"
      :saving="store.isUpdating"
      @close="closeModal"
      @submit="handleSubmit"
    />

    <!-- Liquidate modal: settles an expected income into a linked liquid one -->
    <IncomeLiquidateModal
      :open="isLiquidateModalOpen"
      :record="liquidatingRecord"
      :saving="store.isUpdating"
      @close="closeLiquidateModal"
      @submit="handleLiquidateSubmit"
    />

    <!-- Confirm modal for delete / write-off -->
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
import { BanknotesIcon, PlusIcon, XCircleIcon } from '@heroicons/vue/24/outline';
import ConfirmModal from '~/components/ConfirmModal.vue';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import AccountingFilterPanel from '~/components/accounting/AccountingFilterPanel.vue';
import AccountingExportButton from '~/components/accounting/AccountingExportButton.vue';
import IncomeFormModal from '~/components/accounting/IncomeFormModal.vue';
import IncomeLiquidateModal from '~/components/accounting/IncomeLiquidateModal.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import BasePagination from '~/components/base/BasePagination.vue';
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

const incomesMeta = computed(() => store.metaFor('incomes'));

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

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
  searchInput,
  displayTabs,
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
  restoreTab: restoreFilterTab,
  rebaseTab: rebaseFilterTab,
} = useAccountingFilters({
  viewName: 'accounting_income',
  // Fixed presets: unlike the seeded saved tabs, editing a filter here never
  // rewrites the tab, which is what the landing tab needs.
  builtinTabs: [
    {
      id: 'expected-pending',
      name: 'Solo esperados',
      filters: { kind: 'expected', paymentStatus: 'pending' },
    },
    {
      id: 'hosting-expected',
      name: 'Hosting esperados',
      filters: { kind: 'expected', paymentStatus: 'pending', search: 'hosting' },
    },
    { id: 'lost', name: 'Perdidos', filters: { kind: 'lost' } },
  ],
  // The day-to-day question is what is still uncollected, not the full ledger.
  defaultTabId: 'expected-pending',
  defaults: {
    periodAfter: '',
    periodBefore: '',
    amountMin: '',
    amountMax: '',
    kind: '',
    paymentStatus: '',
    partner: '',
    ledger: '',
  },
  matchers: {
    period: matchDateRange('period_date', 'periodAfter', 'periodBefore'),
    amount: matchNumberRange('total_amount', 'amountMin', 'amountMax'),
    kind: matchEquals('kind', 'kind'),
    // Liquid and lost rows carry `payment_status: null`, so any active
    // value here already narrows the list down to expected records.
    paymentStatus: matchEquals('payment_status', 'paymentStatus'),
    partner: matchPartner,
    ledger: matchEquals('ledger', 'ledger'),
  },
  searchFields: ['concept', 'notes'],
});

const filterFields = [
  { kind: 'daterange', label: 'Mes', minKey: 'periodAfter', maxKey: 'periodBefore' },
  { kind: 'range', label: 'Total', minKey: 'amountMin', maxKey: 'amountMax', type: 'money' },
  {
    kind: 'segmented',
    key: 'kind',
    label: 'Tipo',
    options: [
      { value: '', label: 'Todos' },
      { value: 'expected', label: 'Esperado' },
      { value: 'liquid', label: 'Líquido' },
      { value: 'lost', label: 'Pérdidas' },
    ],
  },
  {
    kind: 'segmented',
    key: 'paymentStatus',
    label: 'Cobro',
    options: [
      { value: '', label: 'Todos' },
      { value: 'pending', label: 'Sin pagos' },
      { value: 'partial', label: 'Parcial' },
      { value: 'paid', label: 'Pagado' },
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
  {
    kind: 'segmented',
    key: 'ledger',
    label: 'Contabilidad',
    options: [
      { value: '', label: 'Todas' },
      { value: 'company', label: 'Empresa' },
      { value: 'gustavo', label: 'Personal Gustavo' },
      { value: 'carlos', label: 'Personal Carlos' },
    ],
  },
];

const EXPORT_MAPPING = {
  periodAfter: 'date_from',
  periodBefore: 'date_to',
  amountMin: 'amount_min',
  amountMax: 'amount_max',
  kind: 'kind',
  paymentStatus: 'payment_status',
  partner: 'partner',
  ledger: 'ledger',
  search: 'q',
};

const exportParams = computed(() =>
  buildExportParams(currentFilters, EXPORT_MAPPING),
);

// -------------------------------------------------------------------
// Data + CRUD controller (modal, delete confirm, pagination)
// -------------------------------------------------------------------

const filteredRecords = computed(() => applyFilters(store.incomes));

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
  requestConfirm,
  runMutation,
} = useAccountingCrudPage({
  entity: 'incomes',
  // A liquidation creates a CHILD row, so the parent expected row's
  // payment state is computed server-side from data the response doesn't
  // carry. Without a refetch its badge and tint stay stale. A settlement can
  // also book deductions, so the cached expenses list is dropped too.
  onAfterMutation: () => {
    store.expenses = [];
    return store.fetchRecords('incomes');
  },
  // The month column shows the localized label but sorts by the ISO date.
  sortAccessors: { period_label: 'period_date' },
  sortDefaults: {
    period_label: 'desc',
    total_amount: 'desc',
    gustavo_amount: 'desc',
    carlos_amount: 'desc',
  },
  store,
  filteredRecords,
  saveTab,
  resetFilters,
  isFilterPanelOpen,
  labels: {
    entityName: 'ingreso',
    created: 'Ingreso creado',
    updated: 'Ingreso actualizado',
    deleted: 'Ingreso eliminado',
    saveErrorTitle: 'No se pudo guardar',
    deleteErrorTitle: 'No se pudo eliminar',
    deleteTitle: 'Eliminar ingreso',
    deleteMessage: (record) =>
      `Esto eliminará el ingreso "${record.concept}" de forma permanente. Esta acción no se puede deshacer.`,
  },
});

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

const totalLost = computed(() =>
  filteredRecords.value
    .filter((r) => r.kind === 'lost')
    .reduce((sum, r) => sum + (Number(r.total_amount) || 0), 0),
);

const KIND_BADGE_CLASSES = {
  liquid: 'bg-success-soft text-success-strong',
  lost: 'bg-danger-soft text-danger-strong',
  expected: 'bg-surface-raised text-text-muted',
};

// A soft fill would vanish: `incomeRowTone` already paints the whole row in
// that same tint. The chip sits on the plain surface with a colored outline so
// it reads on the tinted row and on the untinted one alike.
const PAYMENT_BADGE_CLASSES = {
  paid: 'bg-surface text-success-strong ring-1 ring-inset ring-success-strong/30',
  partial: 'bg-surface text-warning-strong ring-1 ring-inset ring-warning-strong/30',
};

/** Green once collected, amber while partially collected. */
const incomeRowTone = (row) => {
  if (row.kind !== 'expected') return null;
  if (row.payment_status === 'paid') return 'success';
  if (row.payment_status === 'partial') return 'warning';
  return null;
};

// -------------------------------------------------------------------
// Row actions: liquidate an expected income / write it off
// -------------------------------------------------------------------

const isLiquidateModalOpen = ref(false);
const liquidatingRecord = ref(null);

function openLiquidateModal(record) {
  liquidatingRecord.value = record;
  isLiquidateModalOpen.value = true;
}

function closeLiquidateModal() {
  isLiquidateModalOpen.value = false;
  liquidatingRecord.value = null;
}

async function handleLiquidateSubmit(payload) {
  const incomeId = liquidatingRecord.value?.id;
  const result = await runMutation(
    () => store.settleIncome(incomeId, payload),
    {
      successTitle: 'Ingreso liquidado',
      errorTitle: 'No se pudo liquidar',
      // Flash the expected row: it is the one whose state just changed.
      flashId: incomeId,
    },
  );
  if (result.success) closeLiquidateModal();
}

function confirmWriteOff(record) {
  requestConfirm({
    title: 'Marcar como perdido',
    message:
      `"${record.concept}" (${formatMoney(Number(record.total_amount))}) se `
      + 'contará como pérdida: sale del total esperado y deja de aparecer '
      + 'en la lista salvo que filtres por Pérdidas. No afecta la utilidad.',
    variant: 'danger',
    confirmText: 'Marcar como perdido',
    cancelText: 'Cancelar',
    onConfirm: () => runMutation(
      () => store.updateRecord('incomes', record.id, {
        kind: 'lost',
        destination: 'partners',
      }),
      {
        successTitle: 'Ingreso marcado como perdido',
        errorTitle: 'No se pudo marcar como perdido',
      },
    ),
  });
}

// The three amounts read as one block (`group: 'money'`); concept gets the
// widest floor. Concept, Total, Tipo and Cobro survive every width — the partner
// splits and the period collapse first. The ledger is filter-only: it earned
// no column of its own next to what the row is actually about.
const columns = [
  { key: 'concept', label: 'Concepto', size: 'name', sortable: true },
  { key: 'kind_label', label: 'Tipo', size: 'badge' },
  { key: 'payment_status', label: 'Cobro', size: 'text' },
  { key: 'period_label', label: 'Mes', sortable: true, hideBelow: 'lg' },
  { key: 'total_amount', label: 'Total', format: 'money', group: 'money', sortable: true },
  { key: 'gustavo_amount', label: 'Gustavo', format: 'money', group: 'money', sortable: true, hideBelow: 'md' },
  { key: 'carlos_amount', label: 'Carlos', format: 'money', group: 'money', sortable: true, hideBelow: 'md' },
];

async function loadRecords() {
  await store.fetchRecords('incomes');
}

onMounted(loadRecords);
usePanelRefresh(loadRecords);
</script>
