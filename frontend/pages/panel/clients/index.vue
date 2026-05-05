<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Clientes</h1>
        <p class="text-sm text-text-subtle mt-1">
          Perfiles de clientes para propuestas y plataforma. Los huérfanos pueden eliminarse.
        </p>
      </div>
      <BaseButton
        variant="primary"
        size="md"
        data-testid="clients-new-button"
        @click="openCreateModal"
      >
        <PlusIcon class="w-4 h-4" />
        <span>Nuevo cliente</span>
      </BaseButton>
    </div>

    <!-- Filter tabs (Todos / Activos / Huérfanos) -->
    <div class="flex flex-wrap items-center gap-2 mb-5">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :data-testid="`clients-tab-${tab.id}`"
        :class="[
          'px-4 py-2 rounded-xl text-sm font-medium transition-colors',
          activeTab === tab.id
            ? 'bg-primary text-white'
            : 'bg-surface-raised text-text-muted hover:bg-border-muted',
        ]"
        @click="setActiveTab(tab.id)"
      >
        {{ tab.label }}
      </button>
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
        v-model="search"
        type="text"
        placeholder="Buscar por nombre, email o empresa..."
        data-testid="clients-search-input"
        class="w-full sm:max-w-xs"
        @input="onSearchInput"
      />
      <UiFilterToggleButton
        :open="isFilterPanelOpen"
        :count="activeFilterCount"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      />
    </div>

    <!-- Filter panel -->
    <ClientFilterPanel
      :model-value="currentFilters"
      :is-open="isFilterPanelOpen"
      :filter-count="activeFilterCount"
      @update:model-value="Object.assign(currentFilters, $event)"
      @reset="handleResetFilters"
    />

    <!-- Loading -->
    <div v-if="clientsStore.isLoading" class="text-center py-16 text-text-subtle text-sm">
      Cargando clientes...
    </div>

    <!-- Empty -->
    <div
      v-else-if="filteredClients.length === 0"
      class="text-center py-16 text-text-subtle text-sm"
    >
      {{ search || hasActiveFilters ? 'No se encontraron clientes con ese criterio.' : 'No hay clientes aún.' }}
    </div>

    <!-- Client list -->
    <div v-else class="space-y-3">
      <div
        v-for="client in pagedClients"
        :key="client.id"
        :data-testid="`client-row-${client.id}`"
        class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden"
      >
        <!-- Client row header -->
        <div
          class="px-5 py-4 flex flex-col sm:flex-row sm:flex-wrap sm:items-center sm:justify-between gap-3 cursor-pointer hover:bg-surface-raised transition-colors"
          @click="toggleClient(client)"
        >
          <div class="flex items-center gap-4 flex-1 min-w-0 w-full sm:w-auto">
            <!-- Avatar -->
            <div
              class="w-10 h-10 rounded-full bg-primary-soft flex items-center justify-center flex-shrink-0"
            >
              <span class="text-text-brand font-bold text-sm">{{ initials(client.name) }}</span>
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <p class="text-sm font-semibold text-text-default truncate">{{ client.name }}</p>
                <span
                  v-if="client.is_email_placeholder"
                  class="text-[10px] px-1.5 py-0.5 rounded-full bg-warning-soft text-warning-strong font-medium uppercase tracking-wide"
                  title="Email pendiente — automatizaciones de correo pausadas para este cliente"
                >
                  📧 placeholder
                </span>
                <span
                  v-if="client.is_orphan"
                  class="text-[10px] px-1.5 py-0.5 rounded-full bg-surface-raised text-text-muted font-medium uppercase tracking-wide"
                  title="Sin propuestas ni proyectos — puede eliminarse"
                >
                  Huérfano
                </span>
              </div>
              <p class="text-xs text-text-subtle mt-0.5 truncate">
                {{ client.is_email_placeholder ? 'Email pendiente' : client.email }}
                <span v-if="client.company" class="text-text-subtle">· {{ client.company }}</span>
              </p>
            </div>
          </div>

          <div class="flex items-center justify-end gap-3 flex-shrink-0 w-full sm:w-auto">
            <!-- Stats pills -->
            <span
              class="text-xs px-2.5 py-1 rounded-full bg-surface-raised text-text-muted font-medium"
            >
              {{ client.total_proposals }} propuesta{{ client.total_proposals !== 1 ? 's' : '' }}
            </span>

            <button
              v-if="client.accepted_count > 0"
              type="button"
              :data-testid="`client-platform-${client.id}`"
              class="p-1.5 rounded-lg text-text-subtle hover:text-text-brand hover:bg-primary-soft transition-colors"
              :disabled="isBridging"
              title="Ver en plataforma"
              @click.stop="goToPlatform('/platform/clients/' + client.user_id)"
            >
              <SidebarIcon name="external" class="w-4 h-4" />
            </button>

            <!-- Edit button -->
            <button
              type="button"
              :data-testid="`client-edit-${client.id}`"
              class="p-1.5 rounded-lg text-text-subtle hover:text-text-brand hover:bg-primary-soft transition-colors"
              title="Editar cliente"
              @click.stop="openEditModal(client)"
            >
              <PencilSquareIcon class="w-4 h-4" />
            </button>

            <!-- Trash button -->
            <button
              type="button"
              :data-testid="`client-delete-${client.id}`"
              class="p-1.5 rounded-lg text-text-subtle hover:text-danger-strong hover:bg-danger-soft transition-colors"
              :title="'Eliminar cliente'"
              @click.stop="confirmDelete(client)"
            >
              <TrashIcon class="w-4 h-4" />
            </button>

            <!-- Expand chevron -->
            <svg
              class="w-4 h-4 text-text-subtle transition-transform flex-shrink-0"
              :class="{ 'rotate-180': expandedClients.has(client.id) }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </div>
        </div>

        <!-- Expanded: proposals, projects, and diagnostics -->
        <div
          v-if="expandedClients.has(client.id)"
          class="border-t border-border-muted bg-surface-raised"
        >
          <div v-if="loadingDetails.has(client.id)" class="px-5 py-4 text-sm text-text-subtle">
            Cargando...
          </div>
          <template v-else>
            <!-- Proposals -->
            <div class="px-5 pt-4 pb-1">
              <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider mb-2">Propuestas</p>
            </div>
            <div
              v-if="(detailCache[client.id]?.proposals || []).length === 0"
              class="px-5 pb-4 text-sm text-text-subtle"
            >
              Sin propuestas.
            </div>
            <div v-else class="overflow-x-auto">
              <table class="w-full min-w-[600px] text-sm">
                <thead>
                  <tr
                    class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider"
                  >
                    <th class="px-5 py-3">Propuesta</th>
                    <th class="px-4 py-3">Estado</th>
                    <th class="px-4 py-3">Inversión</th>
                    <th class="px-4 py-3 text-center">Vistas</th>
                    <th class="px-4 py-3">Enviada</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-border-muted">
                  <tr
                    v-for="p in detailCache[client.id].proposals"
                    :key="p.id"
                    class="hover:bg-surface-raised transition-colors bg-surface"
                  >
                    <td class="px-5 py-3">
                      <NuxtLink
                        :to="localePath(`/panel/proposals/${p.id}/edit`)"
                        class="font-medium text-text-default hover:text-text-brand transition-colors"
                      >
                        {{ p.title }}
                      </NuxtLink>
                    </td>
                    <td class="px-4 py-3">
                      <span
                        class="text-xs px-2.5 py-1 rounded-full font-medium"
                        :class="statusClass(p.status)"
                      >
                        {{ p.status }}
                      </span>
                    </td>
                    <td class="px-4 py-3 text-text-muted/60 tabular-nums">
                      ${{ Number(p.total_investment).toLocaleString() }} {{ p.currency }}
                    </td>
                    <td class="px-4 py-3 text-center text-text-muted/60">{{ p.view_count }}</td>
                    <td class="px-4 py-3 text-text-muted text-xs">
                      {{ p.sent_at ? formatDate(p.sent_at) : '—' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Platform projects -->
            <template v-if="(detailCache[client.id]?.projects || []).length > 0">
              <div class="px-5 pt-4 pb-1 border-t border-border-muted mt-2">
                <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider mb-2">Proyectos de plataforma</p>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full min-w-[500px] text-sm">
                  <thead>
                    <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
                      <th class="px-5 py-3">Proyecto</th>
                      <th class="px-4 py-3">Estado</th>
                      <th class="px-4 py-3 text-center">Progreso</th>
                      <th class="px-4 py-3">Inicio</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-border-muted">
                    <tr
                      v-for="proj in detailCache[client.id].projects"
                      :key="proj.id"
                      class="hover:bg-surface-raised transition-colors bg-surface"
                    >
                      <td class="px-5 py-3 font-medium text-text-default">{{ proj.name }}</td>
                      <td class="px-4 py-3">
                        <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="statusClass(proj.status)">
                          {{ proj.status }}
                        </span>
                      </td>
                      <td class="px-4 py-3 text-center text-text-muted/60">{{ proj.progress }}%</td>
                      <td class="px-4 py-3 text-text-muted text-xs">
                        {{ proj.start_date ? formatDate(proj.start_date) : '—' }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>

            <!-- Web diagnostics -->
            <template v-if="(detailCache[client.id]?.diagnostics || []).length > 0">
              <div class="px-5 pt-4 pb-1 border-t border-border-muted mt-2">
                <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider mb-2">Diagnósticos web</p>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full min-w-[500px] text-sm">
                  <thead>
                    <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
                      <th class="px-5 py-3">Diagnóstico</th>
                      <th class="px-4 py-3">Estado</th>
                      <th class="px-4 py-3">Creado</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-border-muted">
                    <tr
                      v-for="diag in detailCache[client.id].diagnostics"
                      :key="diag.id"
                      class="hover:bg-surface-raised transition-colors bg-surface"
                    >
                      <td class="px-5 py-3 font-medium text-text-default">{{ diag.title }}</td>
                      <td class="px-4 py-3">
                        <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="statusClass(diag.status)">
                          {{ diag.status }}
                        </span>
                      </td>
                      <td class="px-4 py-3 text-text-muted text-xs">
                        {{ diag.created_at ? formatDate(diag.created_at) : '—' }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>
          </template>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <BasePagination
      v-if="!clientsStore.isLoading && filteredClients.length > 0"
      :current-page="clientsPage"
      :total-pages="clientsTotalPages"
      :total-items="clientsTotalItems"
      :range-from="clientsRangeFrom"
      :range-to="clientsRangeTo"
      class="mt-4"
      @prev="clientsPrev"
      @next="clientsNext"
      @go="clientsGoTo"
    />

    <!-- New client modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      @click.self="closeCreateModal"
    >
      <div class="bg-surface border border-border-muted rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
        <div class="px-6 pt-6 pb-2">
          <h3 class="text-lg font-bold text-text-default">Nuevo cliente</h3>
          <p class="mt-1 text-sm text-text-muted">
            Crea un perfil sin propuesta. Si no agregas email, generaremos uno temporal y las
            automatizaciones quedarán pausadas para este cliente.
          </p>
        </div>
        <form @submit.prevent="submitCreate" class="px-6 py-4 space-y-4">
          <div>
            <label class="block text-xs font-medium text-text-muted mb-1">Nombre</label>
            <input
              v-model="createForm.name"
              type="text"
              required
              data-testid="clients-new-name"
              class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder:text-text-subtle rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-text-muted mb-1">Email (opcional)</label>
            <input
              v-model="createForm.email"
              type="email"
              data-testid="clients-new-email"
              class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder:text-text-subtle rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-text-muted mb-1">Teléfono</label>
            <input
              v-model="createForm.phone"
              type="tel"
              data-testid="clients-new-phone"
              class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder:text-text-subtle rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-text-muted mb-1">Empresa</label>
            <input
              v-model="createForm.company"
              type="text"
              data-testid="clients-new-company"
              class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder:text-text-subtle rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
          </div>
          <p v-if="createError" class="text-xs text-danger-strong">{{ createError }}</p>
          <div class="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium text-text-muted bg-surface-raised hover:bg-border-muted rounded-xl transition-colors"
              @click="closeCreateModal"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="clientsStore.isUpdating"
              data-testid="clients-new-submit"
              class="px-4 py-2 text-sm font-bold text-white bg-primary hover:bg-primary-strong disabled:opacity-50 rounded-xl transition-colors"
            >
              Crear cliente
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit client modal -->
    <div
      v-if="editingClient"
      class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      @click.self="closeEditModal"
    >
      <div class="bg-surface border border-border-muted rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
        <div class="px-6 pt-6 pb-2">
          <h3 class="text-lg font-bold text-text-default">Editar cliente</h3>
          <p class="mt-1 text-sm text-text-muted">
            Los cambios se propagarán a todas las propuestas vinculadas a este cliente.
          </p>
        </div>
        <form @submit.prevent="submitEdit" class="px-6 py-4 space-y-4">
          <div>
            <label class="block text-xs font-medium text-text-muted mb-1">Nombre</label>
            <input
              v-model="editForm.name"
              type="text"
              required
              data-testid="clients-edit-name"
              class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder:text-text-subtle rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-text-muted mb-1">Email (opcional)</label>
            <input
              v-model="editForm.email"
              type="email"
              data-testid="clients-edit-email"
              class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder:text-text-subtle rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-text-muted mb-1">Teléfono</label>
            <input
              v-model="editForm.phone"
              type="tel"
              data-testid="clients-edit-phone"
              class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder:text-text-subtle rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-text-muted mb-1">Empresa</label>
            <input
              v-model="editForm.company"
              type="text"
              data-testid="clients-edit-company"
              class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder:text-text-subtle rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
          </div>
          <p v-if="editError" class="text-xs text-danger-strong">{{ editError }}</p>
          <div class="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium text-text-muted bg-surface-raised hover:bg-border-muted rounded-xl transition-colors"
              @click="closeEditModal"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="clientsStore.isUpdating"
              data-testid="clients-edit-submit"
              class="px-4 py-2 text-sm font-bold text-white bg-primary hover:bg-primary-strong disabled:opacity-50 rounded-xl transition-colors"
            >
              Guardar cambios
            </button>
          </div>
        </form>
      </div>
    </div>

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
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { PlusIcon, TrashIcon, PencilSquareIcon } from '@heroicons/vue/24/outline';
import SidebarIcon from '~/components/platform/SidebarIcon.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import ClientFilterPanel from '~/components/clients/ClientFilterPanel.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { useClientFilters } from '~/composables/useClientFilters';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { usePanelToPlatformBridge } from '~/composables/usePanelToPlatformBridge';
import { usePagination } from '~/composables/usePagination';
import { useProposalClientsStore } from '~/stores/proposalClients';

const localePath = useLocalePath();
const { goToPlatform, isBridging } = usePanelToPlatformBridge();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const clientsStore = useProposalClientsStore();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } =
  useConfirmModal();

const {
  currentFilters,
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
} = useClientFilters();

const filteredClients = computed(() => applyFilters(clientsStore.clients));

const {
  currentPage: clientsPage,
  totalPages: clientsTotalPages,
  totalItems: clientsTotalItems,
  rangeFrom: clientsRangeFrom,
  rangeTo: clientsRangeTo,
  paginatedItems: pagedClients,
  goTo: clientsGoTo,
  next: clientsNext,
  prev: clientsPrev,
  reset: clientsResetPage,
} = usePagination(filteredClients, { pageSize: 10 });

watch(filteredClients, () => clientsResetPage(), { deep: false });

const tabs = [
  { id: 'all', label: 'Todos' },
  { id: 'active', label: 'Activos' },
  { id: 'orphans', label: 'Huérfanos' },
];
const activeTab = ref('all');
const search = ref('');
const expandedClients = ref(new Set());
const loadingDetails = ref(new Set());
const detailCache = reactive({});

let searchTimer = null;

// -------------------------------------------------------------------
// Data loading
// -------------------------------------------------------------------

async function loadClients() {
  let orphans = null;
  if (activeTab.value === 'orphans') orphans = true;
  else if (activeTab.value === 'active') orphans = false;
  await clientsStore.fetchClients({ search: search.value.trim(), orphans });
}

function setActiveTab(tabId) {
  activeTab.value = tabId;
  loadClients();
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(loadClients, 250);
}

function handleCreateFilterTab(name) {
  saveTab(name);
  isFilterPanelOpen.value = true;
}

function handleResetFilters() {
  resetFilters();
  isFilterPanelOpen.value = false;
}

function handleEditEscape(e) {
  if (e.key === 'Escape' && editingClient.value) closeEditModal();
}

onMounted(() => {
  loadClients();
  document.addEventListener('keydown', handleEditEscape);
});

usePanelRefresh(loadClients);
onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer);
  document.removeEventListener('keydown', handleEditEscape);
});

// -------------------------------------------------------------------
// Row expand → fetch nested proposals on demand
// -------------------------------------------------------------------

async function toggleClient(client) {
  const id = client.id;
  if (expandedClients.value.has(id)) {
    expandedClients.value.delete(id);
    expandedClients.value = new Set(expandedClients.value);
    return;
  }
  expandedClients.value.add(id);
  expandedClients.value = new Set(expandedClients.value);

  if (!detailCache[id]) {
    loadingDetails.value.add(id);
    loadingDetails.value = new Set(loadingDetails.value);
    const result = await clientsStore.fetchClient(id);
    if (result.success) {
      detailCache[id] = result.data;
    }
    loadingDetails.value.delete(id);
    loadingDetails.value = new Set(loadingDetails.value);
  }
}

// -------------------------------------------------------------------
// Create modal
// -------------------------------------------------------------------

const showCreateModal = ref(false);
const createForm = reactive({ name: '', email: '', phone: '', company: '' });
const createError = ref('');

function openCreateModal() {
  Object.assign(createForm, { name: '', email: '', phone: '', company: '' });
  createError.value = '';
  showCreateModal.value = true;
}

function closeCreateModal() {
  showCreateModal.value = false;
}

async function submitCreate() {
  createError.value = '';
  const payload = {
    name: createForm.name.trim(),
    email: createForm.email.trim(),
    phone: createForm.phone.trim(),
    company: createForm.company.trim(),
  };
  const result = await clientsStore.createClient(payload);
  if (result.success) {
    closeCreateModal();
    await loadClients();
  } else {
    createError.value =
      result.errors?.message || 'No se pudo crear el cliente. Verifica los datos e intenta nuevamente.';
  }
}

// -------------------------------------------------------------------
// Edit modal
// -------------------------------------------------------------------

const editingClient = ref(null);
const editForm = reactive({ name: '', email: '', phone: '', company: '' });
const editError = ref('');

function openEditModal(client) {
  editingClient.value = client;
  editForm.name = client.name || '';
  editForm.email = client.is_email_placeholder ? '' : (client.email || '');
  editForm.phone = client.phone || '';
  editForm.company = client.company || '';
  editError.value = '';
}

function closeEditModal() {
  editingClient.value = null;
  editError.value = '';
}

async function submitEdit() {
  editError.value = '';
  const payload = {
    name: editForm.name.trim(),
    email: editForm.email.trim(),
    phone: editForm.phone.trim(),
    company: editForm.company.trim(),
  };
  const result = await clientsStore.updateClient(editingClient.value.id, payload);
  if (result.success) {
    closeEditModal();
  } else {
    editError.value =
      result.errors?.error ||
      result.errors?.name?.[0] ||
      result.errors?.email?.[0] ||
      result.errors?.phone?.[0] ||
      result.errors?.company?.[0] ||
      'Error al actualizar el cliente.';
  }
}

// -------------------------------------------------------------------
// Delete
// -------------------------------------------------------------------

function buildBlockedMessage(client) {
  const parts = [];
  const proposals = client.total_proposals || 0;
  const projects = client.projects_count || 0;
  const diagnostics = client.diagnostics_count || 0;
  if (proposals > 0) parts.push(`${proposals} propuesta${proposals === 1 ? '' : 's'}`);
  if (projects > 0) parts.push(`${projects} proyecto${projects === 1 ? '' : 's'} de plataforma`);
  if (diagnostics > 0) parts.push(`${diagnostics} diagnóstico${diagnostics === 1 ? '' : 's'} web`);
  const reason = parts.length > 0 ? parts.join(', ') : 'elementos asociados';
  return `No se puede eliminar a "${client.name}" porque tiene ${reason}. Elimina o archiva esos elementos antes de borrar el cliente.`;
}

function confirmDelete(client) {
  if (!client.is_orphan) {
    requestConfirm({
      title: 'No se puede eliminar',
      message: buildBlockedMessage(client),
      variant: 'info',
      hideCancel: true,
      confirmText: 'Entendido',
    });
    return;
  }

  requestConfirm({
    title: 'Eliminar cliente',
    message: `Esto eliminará a "${client.name}" y su cuenta de plataforma de forma permanente. Esta acción no se puede deshacer.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    cancelText: 'Cancelar',
    requireTypeText: 'DELETE',
    onConfirm: async () => {
      const result = await clientsStore.deleteClient(client.id);
      if (!result.success) {
        // Refresh in case the orphan flag was stale.
        await loadClients();
      }
    },
  });
}

// -------------------------------------------------------------------
// Helpers
// -------------------------------------------------------------------

function initials(name) {
  return (name || '?')
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() || '')
    .join('');
}

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('es-CO', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function statusClass(s) {
  const map = {
    draft: 'bg-surface-raised text-text-muted',
    sent: 'bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-300',
    viewed: 'bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-300',
    accepted: 'bg-primary-soft text-text-brand',
    finished: 'bg-primary-soft text-text-brand',
    rejected: 'bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-300',
    expired: 'bg-yellow-50 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-300',
    negotiating: 'bg-purple-50 dark:bg-purple-500/10 text-purple-700 dark:text-purple-300',
    active: 'bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-300',
    paused: 'bg-yellow-50 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-300',
    completed: 'bg-primary-soft text-text-brand',
    archived: 'bg-surface-raised text-text-muted',
  };
  return map[s] || 'bg-surface-raised text-text-muted';
}
</script>
