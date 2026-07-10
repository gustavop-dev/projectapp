<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Hostings</h1>
        <p class="text-sm text-text-subtle mt-1">
          Servicios de hosting cobrados a clientes y su ingreso mensual.
        </p>
      </div>
      <BaseButton
        variant="primary"
        size="md"
        data-testid="hostings-new-button"
        @click="openCreateModal"
      >
        <PlusIcon class="w-4 h-4" />
        <span>Nuevo hosting</span>
      </BaseButton>
    </div>

    <AccountingSubnav active="hostings" />

    <!-- Meta cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
      <AccountingStatCard
        label="Hostings activos"
        :value="String(hostingsMeta.active_count ?? 0)"
        tone="brand"
      />
      <AccountingStatCard
        label="Ingreso mensual"
        :value="formatMoney(hostingsMeta.monthly_income ?? 0)"
        tone="success"
      />
      <AccountingStatCard
        label="Por vencer en 30 días"
        :value="String(hostingsMeta.expiring_soon_count ?? 0)"
        :tone="(hostingsMeta.expiring_soon_count ?? 0) > 0 ? 'warning' : 'default'"
        sub="Activos con vigencia próxima"
      />
      <AccountingStatCard
        label="Total pagado histórico"
        :value="formatMoney(hostingsMeta.total_paid ?? 0)"
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
        placeholder="Buscar por cliente o dominio..."
        data-testid="hostings-search-input"
        class="w-full sm:max-w-xs"
      />
      <UiFilterToggleButton
        :open="isFilterPanelOpen"
        :count="activeFilterCount"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      />
      <AccountingExportButton section="hosting" :params="exportParams" />
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

    <!-- Error -->
    <AccountingErrorState
      v-if="store.error === 'fetch_failed'"
      title="No se pudieron cargar los hostings"
      :retrying="store.isLoading"
      @retry="loadRecords"
    />

    <!-- Empty -->
    <BaseEmptyState
      v-else-if="!store.isLoading && filteredRecords.length === 0"
      :title="hasActiveFilters ? 'Sin resultados con esos filtros' : 'No hay hostings aún'"
      :description="hasActiveFilters
        ? 'Ajusta o limpia los filtros para ver más registros.'
        : 'Registra el primer contrato de hosting de un cliente.'"
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
          <span>Nuevo hosting</span>
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
        @edit="openEditModal"
        @delete="confirmDeleteRecord"
        @sort="toggleSort"
      >
        <template #cell-client_name="{ row }">
          <AccountingInlineCell
            :value="row.client_name"
            :saving="inlineSavingKey === `${row.id}:client_name`"
            @save="saveInline(row, 'client_name', $event)"
          />
        </template>
        <template #cell-domain_url="{ row }">
          <AccountingInlineCell
            :value="row.domain_url"
            :saving="inlineSavingKey === `${row.id}:domain_url`"
            @save="saveInline(row, 'domain_url', $event)"
          >
            <a
              v-if="row.domain_url"
              :href="row.domain_url"
              target="_blank"
              rel="noopener noreferrer"
              class="text-text-brand hover:underline truncate inline-block max-w-[180px] align-middle"
              :title="row.domain_url"
              @click.stop
            >
              {{ row.domain_url }}
            </a>
            <span v-else class="text-text-subtle">—</span>
          </AccountingInlineCell>
        </template>
        <template #cell-monthly_value="{ row }">
          <AccountingInlineCell
            type="money"
            :value="row.monthly_value"
            :saving="inlineSavingKey === `${row.id}:monthly_value`"
            @save="saveInline(row, 'monthly_value', $event)"
          >
            <span class="tabular-nums">{{ formatMoney(row.monthly_value, 'COP') }}</span>
          </AccountingInlineCell>
        </template>
        <template #cell-validity="{ row }">
          <span class="text-text-muted text-xs whitespace-nowrap">
            {{ row.valid_from || row.valid_to ? `${row.valid_from || '—'} → ${row.valid_to || '—'}` : '—' }}
          </span>
        </template>
        <template #cell-is_active="{ row }">
          <AccountingStatusSelect
            :value="row.is_active"
            :updating="statusUpdatingId === row.id"
            aria-label="Cambiar estado del hosting"
            @change="changeStatus(row, $event)"
          />
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
    <HostingFormModal
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
import { computed, onMounted, ref } from 'vue';
import { PlusIcon } from '@heroicons/vue/24/outline';
import ConfirmModal from '~/components/ConfirmModal.vue';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import AccountingFilterPanel from '~/components/accounting/AccountingFilterPanel.vue';
import AccountingExportButton from '~/components/accounting/AccountingExportButton.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import AccountingStatusSelect from '~/components/accounting/AccountingStatusSelect.vue';
import AccountingInlineCell from '~/components/accounting/AccountingInlineCell.vue';
import HostingFormModal from '~/components/accounting/HostingFormModal.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useAccountingCrudPage } from '~/composables/useAccountingCrudPage';
import {
  useAccountingFilters,
  matchDateRange,
  matchNumberRange,
  matchIncludes,
  matchBoolean,
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
  viewName: 'accounting_hosting',
  defaults: {
    modalities: [],
    valueMin: '',
    valueMax: '',
    validToAfter: '',
    validToBefore: '',
    isActive: '',
  },
  matchers: {
    modalities: matchIncludes('payment_modality', 'modalities'),
    value: matchNumberRange('monthly_value', 'valueMin', 'valueMax'),
    validTo: matchDateRange('valid_to', 'validToAfter', 'validToBefore'),
    isActive: matchBoolean('is_active', 'isActive'),
  },
  searchFields: ['client_name', 'domain_url', 'notes'],
});

const filterFields = [
  {
    kind: 'multi',
    key: 'modalities',
    label: 'Modalidad',
    options: [
      { value: 'monthly', label: 'Mensual' },
      { value: 'quarterly', label: 'Trimestral' },
      { value: 'semiannual', label: 'Semestral' },
      { value: 'annual', label: 'Anual' },
    ],
  },
  { kind: 'range', label: 'Valor/mes', minKey: 'valueMin', maxKey: 'valueMax', type: 'money' },
  { kind: 'daterange', label: 'Vencimiento', minKey: 'validToAfter', maxKey: 'validToBefore' },
  {
    kind: 'segmented',
    key: 'isActive',
    label: 'Estado',
    options: [
      { value: '', label: 'Todos' },
      { value: 'true', label: 'Vigentes' },
      { value: 'false', label: 'Inactivos' },
    ],
  },
];

// validTo range has no server-side equivalent (list filters valid_from)
const EXPORT_MAPPING = {
  valueMin: 'amount_min',
  valueMax: 'amount_max',
  modalities: 'payment_modality',
  isActive: 'is_active',
  search: 'q',
};

const exportParams = computed(() =>
  buildExportParams(currentFilters, EXPORT_MAPPING),
);

// -------------------------------------------------------------------
// Data + CRUD controller (modal, delete confirm, pagination)
// -------------------------------------------------------------------

const hostingsMeta = computed(() => store.metaFor('hostings'));

const filteredRecords = computed(() => applyFilters(store.hostings));

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
} = useAccountingCrudPage({
  entity: 'hostings',
  store,
  filteredRecords,
  saveTab,
  resetFilters,
  isFilterPanelOpen,
  labels: {
    entityName: 'hosting',
    created: 'Hosting creado',
    updated: 'Hosting actualizado',
    deleted: 'Hosting eliminado',
    saveErrorTitle: 'No se pudo guardar',
    deleteErrorTitle: 'No se pudo eliminar',
    deleteTitle: 'Eliminar hosting',
    deleteMessage: (record) =>
      `Esto eliminará el hosting de "${record.client_name}" de forma permanente. Esta acción no se puede deshacer.`,
  },
  // Refresh meta (active_count / monthly_income) after changes.
  onAfterMutation: () => loadRecords(),
});

const columns = [
  { key: 'client_name', label: 'Cliente', sortable: true },
  { key: 'domain_url', label: 'Dominio' },
  { key: 'monthly_value', label: 'Valor/mes', format: 'money', sortable: true },
  { key: 'payment_modality_label', label: 'Modalidad' },
  { key: 'validity', label: 'Vigencia' },
  { key: 'cycles_count', label: 'Ciclos', align: 'center' },
  { key: 'total_paid', label: 'Total pagado', format: 'money', sortable: true },
  { key: 'is_active', label: 'Estado' },
];

async function loadRecords() {
  await store.fetchRecords('hostings');
}

// -------------------------------------------------------------------
// Inline edits: estado dropdown + double-click cells
// -------------------------------------------------------------------

const statusUpdatingId = ref(null);

async function changeStatus(row, isActive) {
  statusUpdatingId.value = row.id;
  const result = await store.updateRecord('hostings', row.id, { is_active: isActive });
  statusUpdatingId.value = null;
  if (result.success) {
    notify.success({ title: isActive ? 'Hosting activado' : 'Hosting desactivado' });
    loadRecords();
  } else {
    notify.error({ title: 'No se pudo cambiar el estado', detail: result.message });
  }
}

const inlineSavingKey = ref(null);

async function saveInline(row, field, value) {
  inlineSavingKey.value = `${row.id}:${field}`;
  const result = await store.updateRecord('hostings', row.id, { [field]: value });
  inlineSavingKey.value = null;
  if (result.success) {
    notify.success({ title: 'Hosting actualizado' });
    loadRecords();
  } else {
    notify.error({ title: 'No se pudo actualizar', detail: result.message });
  }
}

onMounted(loadRecords);
usePanelRefresh(loadRecords);
</script>
