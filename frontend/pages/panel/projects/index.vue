<template>
  <div :class="PAGE_MAX_WIDTH" data-testid="projects-page">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Proyectos</h1>
        <p class="text-sm text-text-subtle mt-1">
          El producto entregado a cada cliente: lo que hostings, ingresos y
          cuentas de cobro referencian.
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <BaseButton
          as="NuxtLink"
          to="/panel/projects/statuses"
          variant="secondary"
          size="md"
          data-testid="projects-manage-states"
        >
          Administrar estados
        </BaseButton>
        <BaseButton
          variant="primary"
          size="md"
          data-testid="projects-new-button"
          @click="openCreate"
        >
          <BaseActionIcon action="create" />
          <span>Nuevo proyecto</span>
        </BaseButton>
      </div>
    </div>

    <!-- Meta cards -->
    <div class="mb-6 grid grid-cols-2 gap-3 panel-landscape:grid-cols-4">
      <div
        v-for="state in store.meta.by_state || []"
        :key="state.state_id"
        class="relative min-w-0"
      >
        <AccountingStatCard
          :label="state.name"
          :value="String(state.count ?? 0)"
          :tone="statTone(state.color)"
          clickable
          :data-testid="`panel-projects-stat-state-${state.state_id}`"
          @click="scope = `state:${state.state_id}`"
        />
        <ProjectStateHelpBadge
          :state="{ ...state, id: state.state_id }"
          position="bottom"
          class="absolute bottom-2 right-2 z-20"
          :test-id="`project-stat-state-help-${state.state_id}`"
        />
      </div>
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
        v-if="(store.meta.review_required ?? 0) > 0"
        label="Por revisar"
        :value="String(store.meta.review_required)"
        tone="warning"
        clickable
        data-testid="panel-projects-stat-review"
        @click="scope = 'review'"
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
      <BaseSelect
        v-model="scope"
        :options="scopeOptions"
        size="sm"
        aria-label="Estado de los proyectos"
        data-testid="projects-state-filter"
        class="w-full sm:max-w-xs"
      />
      <ProjectStateHelpBadge
        v-if="selectedScopeState"
        :state="selectedScopeState"
        position="bottom"
        test-id="project-filter-state-help"
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
          <BaseActionIcon action="create" />
          <span>Nuevo proyecto</span>
        </BaseButton>
      </template>
    </BaseEmptyState>

    <!-- Table -->
    <template v-else>
      <div v-if="isCompact" class="space-y-4">
        <div class="grid grid-cols-[minmax(0,1fr)_auto] gap-2 rounded-xl border border-border-muted bg-surface p-3">
          <BaseSelect
            :model-value="sortKey"
            :options="MOBILE_SORT_OPTIONS"
            size="sm"
            aria-label="Ordenar proyectos por"
            data-testid="projects-sort-mobile"
            @update:model-value="setMobileSortKey"
          />
          <BaseButton
            variant="secondary"
            size="md"
            :disabled="!sortKey"
            disabled-reason="Elige primero el criterio para ordenar los proyectos."
            :aria-label="sortDir === 'asc' ? 'Orden ascendente' : 'Orden descendente'"
            data-testid="projects-sort-direction"
            @click="toggleMobileSortDirection"
          >
          <BaseActionIcon :action="sortDir === 'asc' ? 'sort-ascending' : 'sort-descending'" />
          {{ sortDir === 'asc' ? 'A a Z' : 'Z a A' }}
          </BaseButton>
        </div>

        <div class="grid grid-cols-1 gap-4 panel-portrait:grid-cols-2" data-testid="projects-card-list">
          <ProjectCard
            v-for="row in pagedRecords"
            :key="row.id"
            :project="row"
            :is-superuser="isSuperuser"
            :highlighted="row.id === (lastMutatedId ?? queryHighlightId)"
            @assign="openAssign"
            @actions="projectActionTarget = $event"
            @change-state="openStateTransition"
          />
        </div>
      </div>

      <AccountingTable
        v-else
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
        <template #cell-status_label="{ row }">
          <span class="inline-flex items-center gap-1.5">
            <BaseBadge :variant="stateBadgeVariant(row.current_state)">
              {{ row.status_label }}
            </BaseBadge>
            <ProjectStateHelpBadge
              v-if="row.current_state"
              :state="row.current_state"
              position="bottom"
              :test-id="`project-table-state-help-${row.id}`"
            />
          </span>
        </template>
        <template #cell-client_name="{ row }">
          <span class="inline-flex flex-col items-start">
            <HighlightText :text="row.client_name" :query="searchInput" />
            <span v-if="row.client_company" class="text-xs text-text-subtle">
              <HighlightText :text="row.client_company" :query="searchInput" />
            </span>
            <!-- Terminal states keep their history but receive no new rows. -->
            <BaseButton
              v-if="unlinkedTotal(row) > 0 && !isTerminal(row)"
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
          <!-- The platform space remains available for every historical row. -->
          <ProjectSpaceLink
            :project-id="row.id"
            :data-testid="`project-space-${row.id}`"
          />
          <BaseActionButton
            action="communications"
            as="NuxtLink"
            :to="{ path: '/panel/communications', query: { project: row.id } }"
            variant="ghost"
            size="sm"
            label="Ver comunicaciones"
            tooltip="Ver comunicaciones de este proyecto"
            :data-testid="`project-communications-${row.id}`"
            @click.stop
          />
          <BaseActionButton
            action="edit"
            variant="ghost"
            size="sm"
            label="Editar proyecto"
            :data-testid="`project-edit-${row.id}`"
            @click.stop="openEditModal(row)"
          />
          <BaseActionButton
            action="change-status"
            variant="ghost"
            size="sm"
            label="Cambiar estado"
            tooltip="Revisar consecuencias y cambiar estado"
            :data-testid="`project-change-state-${row.id}`"
            @click.stop="openStateTransition(row)"
          />
          <BaseActionButton
            action="list"
            variant="ghost"
            size="sm"
            label="Ver histórico de estados"
            :data-testid="`project-state-history-${row.id}`"
            @click.stop="openStateHistory(row)"
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

    <BaseDrawer
      v-model="showProjectActions"
      placement="bottom"
      :title="projectActionTarget?.name || 'Acciones del proyecto'"
      test-id="project-actions-drawer"
    >
      <div v-if="projectActionTarget" class="space-y-2 p-4 panel-portrait:p-6">
        <BaseButton
          variant="secondary"
          size="md"
          class="min-h-11 w-full justify-start"
          @click="editProjectFromActions"
        >
          Editar proyecto
        </BaseButton>
        <BaseButton
          variant="secondary"
          size="md"
          class="min-h-11 w-full justify-start"
          @click="communicationsFromActions"
        >
          Ver comunicaciones
        </BaseButton>
        <BaseButton
          variant="secondary"
          size="md"
          class="min-h-11 w-full justify-start"
          @click="stateProjectFromActions"
        >
          Cambiar estado…
        </BaseButton>
        <BaseButton
          variant="secondary"
          size="md"
          class="min-h-11 w-full justify-start"
          @click="historyProjectFromActions"
        >
          Ver histórico de estados
        </BaseButton>
      </div>
    </BaseDrawer>

    <!-- Create/edit modal -->
    <ProjectFormModal
      :open="isModalOpen"
      :record="editingRecord"
      :saving="store.isUpdating"
      :seed-client="seedClient"
      :existing-projects="store.records"
      @close="closeModal"
      @submit="onFormSubmit"
      @change-client="openChangeClient"
    />

    <!-- Guided cascade: the only path that moves a project between clients -->
    <ProjectChangeClientModal
      :open="changeClientOpen"
      :project="changeClientProject"
      @close="closeChangeClient"
      @changed="onClientChanged"
    />

    <ProjectStateTransitionModal
      :open="stateTransitionOpen"
      :project="stateProject"
      @close="closeStateTransition"
      @changed="onStateChanged"
    />

    <ProjectStateHistoryModal
      v-model="stateHistoryOpen"
      :project="historyProject"
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
              <p class="max-w-full truncate text-sm text-text-default" :title="client.name || client.email">{{ client.name || client.email }}</p>
              <p v-if="client.company" class="max-w-full truncate text-xs text-text-subtle" :title="client.company">
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

  </div>
</template>

<script setup>
import { PAGE_MAX_WIDTH } from '~/utils/tableLayout';
import { computed, onMounted, ref, watch } from 'vue';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import HighlightText from '~/components/ui/HighlightText.vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import ProjectAssignUnlinkedModal from '~/components/panel/projects/ProjectAssignUnlinkedModal.vue';
import ProjectCard from '~/components/panel/projects/ProjectCard.vue';
import ProjectChangeClientModal from '~/components/panel/projects/ProjectChangeClientModal.vue';
import ProjectFormModal from '~/components/panel/projects/ProjectFormModal.vue';
import ProjectSpaceLink from '~/components/panel/projects/ProjectSpaceLink.vue';
import ProjectStateHelpBadge from '~/components/panel/projects/ProjectStateHelpBadge.vue';
import ProjectStateHistoryModal from '~/components/panel/projects/ProjectStateHistoryModal.vue';
import ProjectStateTransitionModal from '~/components/panel/projects/ProjectStateTransitionModal.vue';
import { useAccountingCrudPage } from '~/composables/useAccountingCrudPage';
import { useIsMobile } from '~/composables/useIsMobile';
import { PANEL_BREAKPOINTS } from '~/config/responsive';
import { usePanelProjectsStore } from '~/stores/panel_projects';
import { useProposalStore } from '~/stores/proposals';
import { normalizeName } from '~/utils/clientMatch';
import { stateBadgeVariant } from '~/utils/documentState';
import { formatDate } from '~/utils/formatDate';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const store = usePanelProjectsStore();
const notify = usePanelNotify();
const { isMobile: isCompact } = useIsMobile(PANEL_BREAKPOINTS.landscape - 1);
// The count links point at superuser-only accounting pages; hide them from
// plain admins (same flag the sidebar uses).
const proposalStore = useProposalStore();
const isSuperuser = computed(() => proposalStore.isSuperuser);

// ── State + search. The options come from the administrable catalog, so a
//    newly created state immediately becomes a real filter. ──

const scopeOptions = computed(() => [
  { value: 'all', label: 'Todos los estados' },
  ...(store.meta.by_state || []).map((state) => ({
    value: `state:${state.state_id}`,
    label: `${state.name} (${state.count})`,
  })),
  ...(store.meta.review_required
    ? [{ value: 'review', label: `Por revisar (${store.meta.review_required})` }]
    : []),
]);

const MOBILE_SORT_OPTIONS = [
  { value: '', label: 'Orden original' },
  { value: 'name', label: 'Nombre del proyecto' },
  { value: 'client_name', label: 'Cliente' },
  { value: 'status_label', label: 'Estado' },
  { value: 'created_at', label: 'Fecha de creación' },
  { value: 'hostings_count', label: 'Cantidad de hostings' },
  { value: 'incomes_count', label: 'Cantidad de ingresos' },
];

const scope = ref('all');
const searchInput = ref('');
const selectedScopeState = computed(() => {
  if (!scope.value.startsWith('state:')) return null;
  const stateId = Number(scope.value.slice(6));
  const state = (store.meta.by_state || []).find(
    (item) => item.state_id === stateId,
  );
  return state ? { ...state, id: state.state_id } : null;
});

const hasActiveFilters = computed(
  () => Boolean(searchInput.value.trim()) || scope.value !== 'all',
);

function clearFilters() {
  searchInput.value = '';
  scope.value = 'all';
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
    if (scope.value === 'review' && !record.state_review_required) return false;
    if (scope.value.startsWith('state:')) {
      const stateId = Number(scope.value.slice(6));
      if (record.current_state?.id !== stateId) return false;
    }
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
    saveErrorTitle: (editing) => (editing
      ? 'No se pudo actualizar el proyecto'
      : 'No se pudo crear el proyecto'),
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
    badgeTones: Object.fromEntries((store.meta.by_state || []).map((state) => [
      state.name,
      stateBadgeVariant({ color: state.color }),
    ])),
  },
  { key: 'created_at', label: 'Creado', sortable: true, size: 'date' },
  { key: 'hostings_count', label: 'Hostings', sortable: true, size: 'text', align: 'right' },
  { key: 'incomes_count', label: 'Ingresos', sortable: true, size: 'text', align: 'right' },
  { key: 'row_actions', label: 'Acciones', size: 'icons', align: 'center' },
]);

function setMobileSortKey(key) {
  sortKey.value = key;
  sortDir.value = 'asc';
}

function toggleMobileSortDirection() {
  if (!sortKey.value) return;
  sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc';
}

function statTone(color) {
  return {
    emerald: 'success',
    yellow: 'warning',
    orange: 'warning',
    red: 'danger',
    blue: 'brand',
    purple: 'brand',
  }[color] || 'default';
}

function isTerminal(project) {
  return ['completed', 'decommissioned'].includes(
    project.current_state?.operational_effect,
  );
}

const projectActionTarget = ref(null);
const showProjectActions = computed({
  get: () => Boolean(projectActionTarget.value),
  set: (isOpen) => {
    if (!isOpen) projectActionTarget.value = null;
  },
});

function editProjectFromActions() {
  const row = projectActionTarget.value;
  projectActionTarget.value = null;
  if (row) openEditModal(row);
}

function communicationsFromActions() {
  const row = projectActionTarget.value;
  projectActionTarget.value = null;
  if (row) {
    navigateTo({
      path: '/panel/communications',
      query: { project: String(row.id) },
    });
  }
}

function stateProjectFromActions() {
  const row = projectActionTarget.value;
  projectActionTarget.value = null;
  if (row) openStateTransition(row);
}

function historyProjectFromActions() {
  const row = projectActionTarget.value;
  projectActionTarget.value = null;
  if (row) openStateHistory(row);
}

// ── Lifecycle transition + immutable history ──

const stateTransitionOpen = ref(false);
const stateProject = ref(null);
const stateHistoryOpen = ref(false);
const historyProject = ref(null);

function openStateTransition(project) {
  stateProject.value = project;
  stateTransitionOpen.value = true;
}

function closeStateTransition() {
  stateTransitionOpen.value = false;
  stateProject.value = null;
}

async function onStateChanged(project) {
  await store.refreshAfterExternalMutation();
  notify.success({
    title: 'Estado actualizado',
    detail: `${project.name} ahora está ${project.status_label}.`,
  });
}

function openStateHistory(project) {
  historyProject.value = project;
  stateHistoryOpen.value = true;
}

watch(stateHistoryOpen, (open) => {
  if (!open) historyProject.value = null;
});

// ── Assign the client's unlinked records (PA-51) ──

const assignOpen = ref(false);
const assignProject = ref(null);

function unlinkedTotal(row) {
  return (row.unlinked_hostings_count ?? 0)
    + (row.unlinked_incomes_count ?? 0)
    + (row.unlinked_documents_count ?? 0);
}

function openAssign(row) {
  assignProject.value = row;
  assignOpen.value = true;
}

function closeAssign() {
  assignOpen.value = false;
  assignProject.value = null;
}

// ── Change-client cascade (opened from the edit form's ghost button) ──

const changeClientOpen = ref(false);
const changeClientProject = ref(null);

function openChangeClient() {
  if (!editingRecord.value) return;
  changeClientProject.value = editingRecord.value;
  changeClientOpen.value = true;
}

function closeChangeClient() {
  changeClientOpen.value = false;
  changeClientProject.value = null;
}

function onClientChanged() {
  // The store already refetched projects and the loaded accounting lists;
  // closing both modals is all that is left — the table under them is fresh.
  closeChangeClient();
  closeModal();
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
