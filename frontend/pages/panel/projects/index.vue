<template>
  <div :class="PAGE_MAX_WIDTH">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Proyectos</h1>
        <p class="text-sm text-text-subtle mt-1">
          El producto entregado a cada cliente: lo que hostings, ingresos y
          cuentas de cobro referencian.
        </p>
      </div>
    </div>

    <!-- Meta cards -->
    <div class="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
      <AccountingStatCard
        label="Proyectos activos"
        :value="String(store.meta.active ?? 0)"
        tone="brand"
        data-testid="panel-projects-stat-active"
      />
      <AccountingStatCard
        label="Archivados"
        :value="String(store.meta.archived ?? 0)"
        data-testid="panel-projects-stat-archived"
      />
      <AccountingStatCard
        label="Clientes sin proyecto"
        :value="String(store.meta.clients_without_projects ?? 0)"
        :tone="(store.meta.clients_without_projects ?? 0) > 0 ? 'warning' : 'default'"
        sub="Por registrar de forma deliberada"
        data-testid="panel-projects-stat-orphans"
      />
    </div>

    <!-- Search + scope -->
    <div class="flex flex-col sm:flex-row sm:items-center gap-2 mb-5">
      <BaseInput
        v-model="searchInput"
        type="text"
        placeholder="Buscar por proyecto o cliente..."
        data-testid="projects-search-input"
        class="w-full sm:max-w-xs"
      />
      <BaseSegmented
        v-model="scope"
        :options="SCOPE_OPTIONS"
        size="sm"
      />
    </div>

    <!-- Error -->
    <AccountingErrorState
      v-if="store.error === 'fetch_failed'"
      title="No se pudieron cargar los proyectos"
      :retrying="store.isLoading"
      @retry="loadRecords"
    />

    <!-- Empty -->
    <BaseEmptyState
      v-else-if="!store.isLoading && filteredRecords.length === 0"
      :title="hasActiveFilters ? 'Sin resultados con esos filtros' : 'No hay proyectos aún'"
      :description="hasActiveFilters
        ? 'Ajusta la búsqueda o cambia de pestaña para ver más registros.'
        : 'Registra el primer proyecto de un cliente.'"
    />

    <!-- Table -->
    <template v-else>
      <AccountingTable
        :show-actions="false"
        :loading="store.isLoading"
        :highlight-id="lastMutatedId"
        :columns="columns"
        :rows="pagedRecords"
        :highlight-query="searchInput"
        :sort-key="sortKey"
        :sort-dir="sortDir"
        @sort="toggleSort"
      >
        <template #cell-client_name="{ row }">
          <span class="inline-flex flex-col">
            <HighlightText :text="row.client_name" :query="searchInput" />
            <span v-if="row.client_company" class="text-xs text-text-subtle">
              <HighlightText :text="row.client_company" :query="searchInput" />
            </span>
          </span>
        </template>
        <template #cell-created_at="{ row }">
          <span class="text-text-muted text-xs whitespace-nowrap">
            {{ formatDate(row.created_at) }}
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
  </div>
</template>

<script setup>
import { PAGE_MAX_WIDTH } from '~/utils/tableLayout';
import { computed, onMounted, ref } from 'vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import HighlightText from '~/components/ui/HighlightText.vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import { useAccountingCrudPage } from '~/composables/useAccountingCrudPage';
import { usePanelProjectsStore } from '~/stores/panel_projects';
import { normalizeName } from '~/utils/clientMatch';
import { formatDate } from '~/utils/formatDate';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const store = usePanelProjectsStore();

// ── Scope + search (client-side over the full list, like the accounting tabs;
//    no saved tabs here on purpose — a BaseSegmented covers the module) ──

const SCOPE_OPTIONS = [
  { value: 'active', label: 'Activos', testId: 'projects-scope-active' },
  { value: 'archived', label: 'Archivados', testId: 'projects-scope-archived' },
  { value: 'all', label: 'Todos', testId: 'projects-scope-all' },
];

const scope = ref('active');
const searchInput = ref('');

const hasActiveFilters = computed(
  () => Boolean(searchInput.value.trim()) || scope.value !== 'active',
);

/** Rows flattened for the table: the client object becomes sortable columns. */
const displayRecords = computed(() => store.records.map((record) => ({
  ...record,
  client_name: record.client?.name || '',
  client_company: record.client?.company || '',
})));

const filteredRecords = computed(() => {
  const term = normalizeName(searchInput.value);
  return displayRecords.value.filter((record) => {
    if (scope.value === 'active' && record.status === 'archived') return false;
    if (scope.value === 'archived' && record.status !== 'archived') return false;
    if (!term) return true;
    return [record.name, record.client_name, record.client_company]
      .some((field) => normalizeName(field).includes(term));
  });
});

// ── Table controller (sorting + pagination + the mutation flow F4 wires) ──

const {
  lastMutatedId,
  sortKey,
  sortDir,
  toggleSort,
  currentPage,
  totalPages,
  totalItems,
  rangeFrom,
  rangeTo,
  pagedRecords,
  prevPage,
  nextPage,
  goToPage,
} = useAccountingCrudPage({
  entity: 'projects',
  store,
  filteredRecords,
  labels: {
    created: 'Proyecto creado',
    updated: 'Proyecto actualizado',
    deleted: 'Proyecto archivado',
    saveErrorTitle: (editing) => (editing
      ? 'No se pudo actualizar el proyecto'
      : 'No se pudo crear el proyecto'),
    deleteErrorTitle: 'No se pudo archivar el proyecto',
    deleteTitle: 'Archivar proyecto',
    deleteMessage: (record) => `¿Archivar el proyecto "${record.name}"?`,
  },
});

const columns = computed(() => [
  { key: 'name', label: 'Proyecto', sortable: true, size: 'name' },
  { key: 'client_name', label: 'Cliente', sortable: true, size: 'name' },
  {
    key: 'status_label',
    label: 'Estado',
    format: 'badge',
    sortable: true,
    size: 'badge',
    badgeTones: {
      Activo: 'success',
      Pausado: 'warning',
      Completado: 'info',
      Archivado: 'neutral',
    },
  },
  { key: 'created_at', label: 'Creado', sortable: true, size: 'date' },
  { key: 'hostings_count', label: 'Hostings', sortable: true, size: 'text', align: 'right' },
  { key: 'incomes_count', label: 'Ingresos', sortable: true, size: 'text', align: 'right' },
]);

function loadRecords() {
  store.fetchProjects();
}

onMounted(loadRecords);
</script>
