<template>
  <div>
    <AccountingSubnav active="hostings" />

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

    <!-- Meta cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
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
      Cargando hostings...
    </div>

    <!-- Empty -->
    <div
      v-else-if="filteredRecords.length === 0"
      class="text-center py-16 text-text-subtle text-sm"
    >
      {{ hasActiveFilters ? 'No se encontraron hostings con ese criterio.' : 'No hay hostings aún.' }}
    </div>

    <!-- Table -->
    <template v-else>
      <AccountingTable
        :columns="columns"
        :rows="pagedRecords"
        @edit="openEditModal"
        @delete="confirmDeleteRecord"
      >
        <template #cell-domain_url="{ row }">
          <a
            v-if="row.domain_url"
            :href="row.domain_url"
            target="_blank"
            rel="noopener noreferrer"
            class="text-text-brand hover:underline truncate inline-block max-w-[180px] align-middle"
            :title="row.domain_url"
          >
            {{ row.domain_url }}
          </a>
          <span v-else class="text-text-subtle">—</span>
        </template>
        <template #cell-validity="{ row }">
          <span class="text-text-muted text-xs whitespace-nowrap">
            {{ row.valid_from || row.valid_to ? `${row.valid_from || '—'} → ${row.valid_to || '—'}` : '—' }}
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
import { computed, onMounted } from 'vue';
import { PlusIcon } from '@heroicons/vue/24/outline';
import ConfirmModal from '~/components/ConfirmModal.vue';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingFilterPanel from '~/components/accounting/AccountingFilterPanel.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import HostingFormModal from '~/components/accounting/HostingFormModal.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import BasePagination from '~/components/base/BasePagination.vue';
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
import { formatMoney } from '~/utils/formatMoney';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useAccountingStore();

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
  { kind: 'range', label: 'Valor/mes', minKey: 'valueMin', maxKey: 'valueMax', type: 'number' },
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

// -------------------------------------------------------------------
// Data + CRUD controller (modal, delete confirm, pagination)
// -------------------------------------------------------------------

const hostingsMeta = computed(() => store.metaFor('hostings'));

const filteredRecords = computed(() => applyFilters(store.hostings));

const {
  isModalOpen,
  editingRecord,
  openCreateModal,
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
  { key: 'client_name', label: 'Cliente' },
  { key: 'domain_url', label: 'Dominio' },
  { key: 'monthly_value', label: 'Valor/mes', format: 'money' },
  { key: 'payment_modality_label', label: 'Modalidad' },
  { key: 'validity', label: 'Vigencia' },
  { key: 'cycles_count', label: 'Ciclos', align: 'center' },
  { key: 'total_paid', label: 'Total pagado', format: 'money' },
  { key: 'is_active', label: 'Estado' },
];

async function loadRecords() {
  await store.fetchRecords('hostings');
}

onMounted(loadRecords);
usePanelRefresh(loadRecords);
</script>
