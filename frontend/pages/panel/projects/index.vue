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
      <BaseButton
        variant="primary"
        size="md"
        data-testid="projects-new-button"
        @click="openCreate"
      >
        <PlusIcon class="w-4 h-4" />
        <span>Nuevo proyecto</span>
      </BaseButton>
    </div>

    <!-- Meta cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
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
        clickable
        data-testid="panel-projects-stat-orphans"
        @click="openOrphansPanel"
      />
      <AccountingStatCard
        label="Registros sin proyecto"
        :value="String(store.meta.records_without_project ?? 0)"
        :tone="(store.meta.records_without_project ?? 0) > 0 ? 'warning' : 'default'"
        sub="Hostings e ingresos por asignar"
        data-testid="panel-projects-stat-unlinked"
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
    >
      <template #actions>
        <BaseButton
          v-if="hasActiveFilters"
          variant="secondary"
          size="sm"
          @click="clearFilters"
        >
          Limpiar filtros
        </BaseButton>
        <BaseButton v-else variant="primary" size="sm" @click="openCreate">
          <PlusIcon class="w-4 h-4" />
          <span>Nuevo proyecto</span>
        </BaseButton>
      </template>
    </BaseEmptyState>

    <!-- Table -->
    <template v-else>
      <AccountingTable
        :show-actions="false"
        :loading="store.isLoading"
        :highlight-id="lastMutatedId ?? queryHighlightId"
        :columns="columns"
        :rows="pagedRecords"
        :highlight-query="searchInput"
        :sort-key="sortKey"
        :sort-dir="sortDir"
        @sort="toggleSort"
      >
        <template #cell-client_name="{ row }">
          <span class="inline-flex flex-col items-start">
            <HighlightText :text="row.client_name" :query="searchInput" />
            <span v-if="row.client_company" class="text-xs text-text-subtle">
              <HighlightText :text="row.client_company" :query="searchInput" />
            </span>
            <!-- The client's completion backlog: opens the confirm-first
                 assign modal. Hidden on archived rows (the backend refuses
                 assigning to an archived project anyway). -->
            <BaseButton
              v-if="unlinkedTotal(row) > 0 && row.status !== 'archived'"
              variant="ghost"
              size="sm"
              class="!px-1.5 !py-0.5 text-xs text-warning-strong"
              :title="`${unlinkedTotal(row)} registros de este cliente sin proyecto — asignar`"
              :data-testid="`project-assign-unlinked-${row.id}`"
              @click.stop="openAssign(row)"
            >
              {{ unlinkedTotal(row) }} sin proyecto
            </BaseButton>
          </span>
        </template>
        <template #cell-created_at="{ row }">
          <span class="text-text-muted text-xs whitespace-nowrap">
            {{ formatDate(row.created_at) }}
          </span>
        </template>
        <!-- Counts jump into the accounting tabs pre-filtered by this project.
             Superuser-gated links: the target pages are superuser-only. -->
        <template #cell-hostings_count="{ row }">
          <NuxtLink
            v-if="isSuperuser && row.hostings_count > 0"
            :to="{ path: '/panel/accounting/hostings', query: { project: row.id } }"
            class="text-text-brand hover:underline tabular-nums"
            :data-testid="`project-hostings-link-${row.id}`"
            @click.stop
          >
            {{ row.hostings_count }}
          </NuxtLink>
          <span v-else class="tabular-nums text-text-muted">{{ row.hostings_count }}</span>
        </template>
        <template #cell-incomes_count="{ row }">
          <NuxtLink
            v-if="isSuperuser && row.incomes_count > 0"
            :to="{
              path: '/panel/accounting/incomes',
              query: { accounting_incomeTab: 'all', project: row.id },
            }"
            class="text-text-brand hover:underline tabular-nums"
            :data-testid="`project-incomes-link-${row.id}`"
            @click.stop
          >
            {{ row.incomes_count }}
          </NuxtLink>
          <span v-else class="tabular-nums text-text-muted">{{ row.incomes_count }}</span>
        </template>
        <template #cell-row_actions="{ row }">
          <!-- PA-50: the space exists for every row (same record), archived
               included — platform shows its own Archivado chip. -->
          <ProjectSpaceLink
            :project-id="row.id"
            :data-testid="`project-space-${row.id}`"
          />
          <BaseButton
            variant="ghost"
            size="sm"
            icon-only
            aria-label="Editar"
            :data-testid="`project-edit-${row.id}`"
            :disabled="row.status === 'archived'"
            :title="row.status === 'archived'
              ? 'Restaura el proyecto para editarlo'
              : 'Editar proyecto'"
            @click.stop="openEditModal(row)"
          >
            <PencilSquareIcon class="w-4 h-4" />
          </BaseButton>
          <BaseButton
            v-if="row.status !== 'archived'"
            variant="ghost"
            size="sm"
            icon-only
            aria-label="Archivar"
            title="Archivar proyecto (sale de la vista, nunca se elimina)"
            :data-testid="`project-archive-${row.id}`"
            @click.stop="askArchive(row)"
          >
            <ArchiveBoxArrowDownIcon class="w-4 h-4" />
          </BaseButton>
          <BaseButton
            v-else
            variant="ghost"
            size="sm"
            icon-only
            aria-label="Restaurar"
            title="Restaurar proyecto"
            :data-testid="`project-unarchive-${row.id}`"
            @click.stop="doRestore(row)"
          >
            <ArrowUturnLeftIcon class="w-4 h-4" />
          </BaseButton>
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
    <ProjectFormModal
      :open="isModalOpen"
      :record="editingRecord"
      :saving="store.isUpdating"
      :seed-client="seedClient"
      :existing-projects="store.records"
      @close="closeModal"
      @submit="onFormSubmit"
    />

    <!-- Assign the client's unlinked records to a project (PA-51) -->
    <ProjectAssignUnlinkedModal
      :open="assignOpen"
      :project="assignProject"
      @close="closeAssign"
      @assigned="closeAssign"
    />

    <!-- Clients without a project -->
    <BaseModal
      :model-value="orphansOpen"
      size="md"
      title-id="projects-orphans-title"
      @close="orphansOpen = false"
    >
      <div class="px-6 pt-6 pb-2">
        <h3 id="projects-orphans-title" class="text-lg font-bold text-text-default">
          Clientes sin proyecto
        </h3>
        <p class="text-sm text-text-subtle mt-1">
          Cada uno debería tener registrado el producto que se le entrega.
        </p>
      </div>
      <div class="px-6 py-4" data-testid="panel-projects-orphans">
        <p v-if="store.isLoadingClientsWithoutProjects" class="text-sm text-text-subtle">
          Cargando clientes...
        </p>
        <p
          v-else-if="store.clientsWithoutProjects.length === 0"
          class="text-sm text-text-subtle"
          data-testid="panel-projects-orphans-empty"
        >
          Todos los clientes visibles tienen al menos un proyecto.
        </p>
        <ul v-else class="divide-y divide-border-muted">
          <li
            v-for="client in store.clientsWithoutProjects"
            :key="client.id"
            class="flex items-center justify-between gap-3 py-2.5"
          >
            <div class="min-w-0">
              <p class="text-sm text-text-default truncate">{{ client.name || client.email }}</p>
              <p v-if="client.company" class="text-xs text-text-subtle truncate">
                {{ client.company }}
              </p>
            </div>
            <BaseButton
              variant="secondary"
              size="sm"
              :data-testid="`projects-orphan-create-${client.id}`"
              @click="openCreateFromOrphan(client)"
            >
              Crear proyecto
            </BaseButton>
          </li>
        </ul>
      </div>
    </BaseModal>

    <!-- Confirm modal (archive) -->
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
import { computed, onMounted, ref, watch } from 'vue';
import {
  ArchiveBoxArrowDownIcon,
  ArrowUturnLeftIcon,
  PencilSquareIcon,
  PlusIcon,
} from '@heroicons/vue/24/outline';
import ConfirmModal from '~/components/ConfirmModal.vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import HighlightText from '~/components/ui/HighlightText.vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import ProjectAssignUnlinkedModal from '~/components/panel/projects/ProjectAssignUnlinkedModal.vue';
import ProjectFormModal from '~/components/panel/projects/ProjectFormModal.vue';
import ProjectSpaceLink from '~/components/panel/projects/ProjectSpaceLink.vue';
import { useAccountingCrudPage } from '~/composables/useAccountingCrudPage';
import { usePanelProjectsStore } from '~/stores/panel_projects';
import { useProposalStore } from '~/stores/proposals';
import { normalizeName } from '~/utils/clientMatch';
import { formatDate } from '~/utils/formatDate';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const store = usePanelProjectsStore();
// The count links point at superuser-only accounting pages; hide them from
// plain admins (same flag the sidebar uses).
const proposalStore = useProposalStore();
const isSuperuser = computed(() => proposalStore.isSuperuser);

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

function clearFilters() {
  searchInput.value = '';
  scope.value = 'active';
}

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

// ── Table controller: modal, confirm, mutation flow, sorting, pagination ──

const {
  isModalOpen,
  editingRecord,
  openCreateModal,
  openEditModal,
  closeModal,
  handleSubmit,
  lastMutatedId,
  confirmState,
  handleConfirmed,
  handleCancelled,
  requestConfirm,
  runMutation,
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
  { key: 'row_actions', label: 'Acciones', size: 'icons', align: 'center' },
]);

// ── Archive / restore (PA-29: never delete) ──

function askArchive(record) {
  requestConfirm({
    title: 'Archivar proyecto',
    message: `"${record.name}" saldrá de la vista de activos. Sus hostings e ingresos siguen vinculados y podrás restaurarlo cuando quieras.`,
    confirmText: 'Archivar',
    cancelText: 'Cancelar',
    onConfirm: () => runMutation(
      () => store.archiveProject(record.id),
      {
        successTitle: 'Proyecto archivado',
        errorTitle: 'No se pudo archivar el proyecto',
        flashId: record.id,
      },
    ),
  });
}

function doRestore(record) {
  runMutation(
    () => store.unarchiveProject(record.id),
    {
      successTitle: 'Proyecto restaurado',
      successDetail: 'Vuelve a la pestaña Activos.',
      errorTitle: 'No se pudo restaurar el proyecto',
      flashId: record.id,
    },
  );
}

// ── Assign the client's unlinked records (PA-51) ──

const assignOpen = ref(false);
const assignProject = ref(null);

function unlinkedTotal(row) {
  return (row.unlinked_hostings_count ?? 0) + (row.unlinked_incomes_count ?? 0);
}

function openAssign(row) {
  assignProject.value = row;
  assignOpen.value = true;
}

function closeAssign() {
  assignOpen.value = false;
  assignProject.value = null;
}

/**
 * Create/update passthrough that, after a CREATE, offers the assign modal
 * when the new project's client has records without a project. Offering,
 * never doing: the modal is itself the confirmation step.
 */
async function onFormSubmit(payload) {
  const wasEditing = Boolean(editingRecord.value);
  const result = await handleSubmit(payload);
  if (!wasEditing && result?.success && unlinkedTotal(result.data) > 0) {
    openAssign(result.data);
  }
}

// ── Clients without a project (the deliberate-gap indicator) ──

const orphansOpen = ref(false);
const seedClient = ref(null);

function openOrphansPanel() {
  orphansOpen.value = true;
  store.fetchClientsWithoutProjects();
}

function openCreate() {
  seedClient.value = null;
  openCreateModal();
}

function openCreateFromOrphan(client) {
  orphansOpen.value = false;
  seedClient.value = client;
  openCreateModal();
}

// The seed belongs to one modal opening; a later plain "Nuevo proyecto"
// must not inherit it.
watch(isModalOpen, (open) => {
  if (!open) seedClient.value = null;
});

async function loadRecords() {
  await store.fetchProjects();
}

// ── Deep link from the platform space (PA-50 return path) ──

const route = useRoute();
const queryHighlightId = Number.parseInt(route.query.highlight, 10) || null;

/**
 * Make the linked row visible no matter the scope or page: widen to "Todos"
 * and seed the search with the project's name. Degrades harmlessly when the
 * id is gone (full listing) — the point is never landing on an empty view.
 */
function applyHighlightDeepLink() {
  if (!queryHighlightId) return;
  const row = store.records.find((record) => record.id === queryHighlightId);
  if (!row) return;
  scope.value = 'all';
  searchInput.value = row.name;
}

onMounted(async () => {
  await loadRecords();
  applyHighlightDeepLink();
});
</script>
