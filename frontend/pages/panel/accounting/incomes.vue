<template>
  <div>
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
            <button
              v-if="row.payment_status === 'pending'"
              type="button"
              class="p-1.5 rounded-md text-text-muted hover:text-danger-strong hover:bg-surface-raised transition-colors"
              aria-label="Marcar como perdido"
              title="Marcar como perdido"
              :data-testid="`income-write-off-${row.id}`"
              @click.stop="confirmWriteOff(row)"
            >
              <XCircleIcon class="w-5 h-5" />
            </button>
          </template>
        </template>
        <template #cell-kind_label="{ row }">
          <div
            class="flex flex-col items-start gap-1"
            :data-testid="row.payment_status ? `income-payment-${row.id}` : undefined"
          >
            <div class="flex flex-wrap items-center gap-1.5">
              <span
                class="text-xs px-2.5 py-1 rounded-full font-medium"
                :class="KIND_BADGE_CLASSES[row.kind] || KIND_BADGE_CLASSES.expected"
              >
                {{ row.kind_label }}
              </span>
              <span
                v-if="PAYMENT_BADGE_CLASSES[row.payment_status]"
                class="text-xs px-2.5 py-1 rounded-full font-medium"
                :class="PAYMENT_BADGE_CLASSES[row.payment_status]"
              >
                {{ row.payment_status_label }}
              </span>
            </div>
            <!-- Own line and nowrap: inlining it in the badge stretched the
                 column until the actions were pushed out of the table. -->
            <span
              v-if="row.payment_status === 'partial'"
              class="text-[11px] text-warning-strong tabular-nums whitespace-nowrap"
            >
              faltan {{ formatMoney(Number(row.pending_amount)) }}
            </span>
          </div>
        </template>
        <template #cell-ledger_label="{ row }">
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium"
            :class="row.ledger === 'company'
              ? 'bg-surface-raised text-text-muted'
              : 'bg-info-soft text-info-strong'"
          >
            {{ row.ledger === 'company' ? 'Empresa' : row.ledger_label }}
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
    ledger: '',
  },
  matchers: {
    period: matchDateRange('period_date', 'periodAfter', 'periodBefore'),
    amount: matchNumberRange('total_amount', 'amountMin', 'amountMax'),
    kind: matchEquals('kind', 'kind'),
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
  partner: 'partner',
  ledger: 'ledger',
  search: 'q',
};

const exportParams = computed(() => {
  const params = buildExportParams(currentFilters, EXPORT_MAPPING);
  // Mirror the "Todos" rule: without this the CSV would carry the
  // written-off rows the table is hiding. The server ORs comma lists.
  if (!currentFilters.kind) params.kind = 'expected,liquid';
  return params;
});

// -------------------------------------------------------------------
// Data + CRUD controller (modal, delete confirm, pagination)
// -------------------------------------------------------------------

// Written-off income is money we already know is gone, so it stays out of
// the working set until asked for by name. This has to happen before
// applyFilters: that helper skips any matcher still sitting on its default,
// so a `kind: ''` rule inside it would never run.
const workingSet = computed(() =>
  currentFilters.kind
    ? store.incomes
    : store.incomes.filter((record) => record.kind !== 'lost'),
);

const filteredRecords = computed(() => applyFilters(workingSet.value));

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
  // carry. Without a refetch its badge and tint stay stale.
  onAfterMutation: () => store.fetchRecords('incomes'),
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

const PAYMENT_BADGE_CLASSES = {
  paid: 'bg-success-soft text-success-strong',
  partial: 'bg-warning-soft text-warning-strong',
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
  const result = await runMutation(
    () => store.createRecord('incomes', payload),
    {
      successTitle: 'Ingreso liquidado',
      errorTitle: 'No se pudo liquidar',
      // Flash the expected row: it is the one whose state just changed.
      flashId: liquidatingRecord.value?.id,
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

const columns = [
  { key: 'concept', label: 'Concepto', sortable: true },
  { key: 'kind_label', label: 'Tipo' },
  { key: 'ledger_label', label: 'Contabilidad' },
  { key: 'period_label', label: 'Mes', sortable: true },
  { key: 'total_amount', label: 'Total', format: 'money', sortable: true },
  { key: 'gustavo_amount', label: 'Gustavo', format: 'money', sortable: true },
  { key: 'carlos_amount', label: 'Carlos', format: 'money', sortable: true },
];

async function loadRecords() {
  await store.fetchRecords('incomes');
}

onMounted(loadRecords);
usePanelRefresh(loadRecords);
</script>
