<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-gray-900 dark:text-white">Clientes</h1>
        <p class="text-sm text-gray-400 dark:text-green-light/60 mt-1">
          Perfiles de clientes para propuestas y plataforma. Los huérfanos pueden eliminarse.
        </p>
      </div>
      <button
        type="button"
        data-testid="clients-new-button"
        class="inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-xl transition-colors"
        @click="openCreateModal"
      >
        <PlusIcon class="w-4 h-4" />
        <span>Nuevo cliente</span>
      </button>
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
            ? 'bg-emerald-600 text-white dark:bg-lemon dark:text-esmerald-dark'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-white/[0.06] dark:text-green-light dark:hover:bg-white/[0.10]',
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
      <input
        v-model="search"
        type="text"
        placeholder="Buscar por nombre, email o empresa..."
        data-testid="clients-search-input"
        class="w-full sm:max-w-xs px-4 py-2.5 border border-gray-200 rounded-xl text-sm
               focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none
               dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-green-light/40"
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
    <div v-if="clientsStore.isLoading" class="text-center py-16 text-gray-400 dark:text-green-light/60 text-sm">
      Cargando clientes...
    </div>

    <!-- Empty -->
    <div
      v-else-if="filteredClients.length === 0"
      class="text-center py-16 text-gray-400 dark:text-green-light/60 text-sm"
    >
      {{ search || hasActiveFilters ? 'No se encontraron clientes con ese criterio.' : 'No hay clientes aún.' }}
    </div>

    <!-- Client list -->
    <div v-else class="space-y-3">
      <div
        v-for="client in filteredClients"
        :key="client.id"
        :data-testid="`client-row-${client.id}`"
        class="bg-white dark:bg-esmerald rounded-xl shadow-sm border border-gray-100 dark:border-white/[0.06] overflow-hidden"
      >
        <!-- Client row header -->
        <div
          class="px-5 py-4 flex flex-wrap items-center justify-between gap-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-white/[0.04] transition-colors"
          @click="toggleClient(client)"
        >
          <div class="flex items-center gap-4 flex-1 min-w-0">
            <!-- Avatar -->
            <div
              class="w-10 h-10 rounded-full bg-emerald-100 dark:bg-white/10 flex items-center justify-center flex-shrink-0"
            >
              <span class="text-emerald-700 dark:text-white font-bold text-sm">{{ initials(client.name) }}</span>
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <p class="text-sm font-semibold text-gray-900 dark:text-white truncate">{{ client.name }}</p>
                <span
                  v-if="client.is_email_placeholder"
                  class="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-50 dark:bg-amber-400/10 text-amber-700 dark:text-amber-300 font-medium uppercase tracking-wide"
                  title="Email pendiente — automatizaciones de correo pausadas para este cliente"
                >
                  📧 placeholder
                </span>
                <span
                  v-if="client.is_orphan"
                  class="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100 dark:bg-white/[0.06] text-gray-500 dark:text-green-light/60 font-medium uppercase tracking-wide"
                  title="Sin propuestas ni proyectos — puede eliminarse"
                >
                  Huérfano
                </span>
              </div>
              <p class="text-xs text-gray-400 dark:text-green-light/60 mt-0.5 truncate">
                {{ client.is_email_placeholder ? 'Email pendiente' : client.email }}
                <span v-if="client.company" class="text-gray-400 dark:text-green-light/60">· {{ client.company }}</span>
              </p>
            </div>
          </div>

          <div class="flex items-center gap-3 flex-shrink-0">
            <!-- Stats pills -->
            <span
              class="text-xs px-2.5 py-1 rounded-full bg-gray-100 dark:bg-white/[0.06] text-gray-600 dark:text-green-light font-medium"
            >
              {{ client.total_proposals }} propuesta{{ client.total_proposals !== 1 ? 's' : '' }}
            </span>

            <button
              v-if="client.accepted_count > 0"
              type="button"
              :data-testid="`client-platform-${client.id}`"
              class="p-1.5 rounded-lg text-gray-400 dark:text-green-light/60 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:text-white dark:hover:bg-white/[0.06] transition-colors"
              :disabled="isBridging"
              title="Ver en plataforma"
              @click.stop="goToPlatform('/platform/clients/' + client.user_id)"
            >
              <SidebarIcon name="external" class="w-4 h-4" />
            </button>

            <!-- Trash button (orphans only) -->
            <button
              v-if="client.is_orphan"
              type="button"
              :data-testid="`client-delete-${client.id}`"
              class="p-1.5 rounded-lg text-gray-400 dark:text-green-light/60 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
              :title="'Eliminar cliente'"
              @click.stop="confirmDelete(client)"
            >
              <TrashIcon class="w-4 h-4" />
            </button>

            <!-- Expand chevron -->
            <svg
              class="w-4 h-4 text-gray-400 dark:text-green-light/60 transition-transform flex-shrink-0"
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

        <!-- Expanded: proposals list -->
        <div
          v-if="expandedClients.has(client.id)"
          class="border-t border-gray-100 dark:border-white/[0.04] bg-gray-50/40 dark:bg-white/[0.03]"
        >
          <div v-if="loadingDetails.has(client.id)" class="px-5 py-4 text-sm text-gray-400 dark:text-green-light/60">
            Cargando propuestas...
          </div>
          <div
            v-else-if="(detailCache[client.id]?.proposals || []).length === 0"
            class="px-5 py-4 text-sm text-gray-400 dark:text-green-light/60"
          >
            Este cliente no tiene propuestas todavía.
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full min-w-[600px] text-sm">
              <thead>
                <tr
                  class="bg-gray-50 dark:bg-white/[0.03] text-left text-xs text-gray-500 dark:text-green-light/60 uppercase tracking-wider"
                >
                  <th class="px-5 py-3">Propuesta</th>
                  <th class="px-4 py-3">Estado</th>
                  <th class="px-4 py-3">Inversión</th>
                  <th class="px-4 py-3 text-center">Vistas</th>
                  <th class="px-4 py-3">Enviada</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50 dark:divide-white/[0.04]">
                <tr
                  v-for="p in detailCache[client.id].proposals"
                  :key="p.id"
                  class="hover:bg-gray-50/60 dark:hover:bg-white/[0.04] transition-colors bg-white dark:bg-transparent"
                >
                  <td class="px-5 py-3">
                    <NuxtLink
                      :to="localePath(`/panel/proposals/${p.id}/edit`)"
                      class="font-medium text-gray-900 dark:text-white hover:text-emerald-600 transition-colors"
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
                  <td class="px-4 py-3 text-gray-600 dark:text-green-light/60 tabular-nums">
                    ${{ Number(p.total_investment).toLocaleString() }} {{ p.currency }}
                  </td>
                  <td class="px-4 py-3 text-center text-gray-600 dark:text-green-light/60">{{ p.view_count }}</td>
                  <td class="px-4 py-3 text-gray-500 dark:text-green-light/60 text-xs">
                    {{ p.sent_at ? formatDate(p.sent_at) : '—' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- New client modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      @click.self="closeCreateModal"
    >
      <div class="bg-white dark:bg-esmerald dark:border dark:border-white/[0.06] rounded-2xl shadow-2xl dark:shadow-black/40 w-full max-w-md overflow-hidden">
        <div class="px-6 pt-6 pb-2">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white">Nuevo cliente</h3>
          <p class="mt-1 text-sm text-gray-500 dark:text-green-light/60">
            Crea un perfil sin propuesta. Si no agregas email, generaremos uno temporal y las
            automatizaciones quedarán pausadas para este cliente.
          </p>
        </div>
        <form @submit.prevent="submitCreate" class="px-6 py-4 space-y-4">
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-green-light/60 mb-1">Nombre</label>
            <input
              v-model="createForm.name"
              type="text"
              required
              data-testid="clients-new-name"
              class="w-full px-3 py-2 border border-gray-200 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-green-light/40 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-green-light/60 mb-1">Email (opcional)</label>
            <input
              v-model="createForm.email"
              type="email"
              data-testid="clients-new-email"
              class="w-full px-3 py-2 border border-gray-200 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-green-light/40 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-green-light/60 mb-1">Teléfono</label>
            <input
              v-model="createForm.phone"
              type="tel"
              data-testid="clients-new-phone"
              class="w-full px-3 py-2 border border-gray-200 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-green-light/40 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-green-light/60 mb-1">Empresa</label>
            <input
              v-model="createForm.company"
              type="text"
              data-testid="clients-new-company"
              class="w-full px-3 py-2 border border-gray-200 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-green-light/40 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
          </div>
          <p v-if="createError" class="text-xs text-red-600">{{ createError }}</p>
          <div class="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-green-light bg-gray-100 dark:bg-white/[0.06] hover:bg-gray-200 dark:hover:bg-white/[0.10] rounded-xl transition-colors"
              @click="closeCreateModal"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="clientsStore.isUpdating"
              data-testid="clients-new-submit"
              class="px-4 py-2 text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 rounded-xl transition-colors"
            >
              Crear cliente
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
      @confirm="handleConfirmed"
      @cancel="handleCancelled"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue';
import { PlusIcon, TrashIcon } from '@heroicons/vue/24/outline';
import SidebarIcon from '~/components/platform/SidebarIcon.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import ClientFilterPanel from '~/components/clients/ClientFilterPanel.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { useClientFilters } from '~/composables/useClientFilters';
import { usePanelToPlatformBridge } from '~/composables/usePanelToPlatformBridge';
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

onMounted(loadClients);
onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer);
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
// Delete (orphan only)
// -------------------------------------------------------------------

function confirmDelete(client) {
  requestConfirm({
    title: 'Eliminar cliente',
    message: `¿Eliminar a "${client.name}" permanentemente? Esto borrará también su cuenta de plataforma.`,
    variant: 'danger',
    confirmText: 'Eliminar',
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
    draft: 'bg-gray-100 dark:bg-white/[0.06] text-gray-600 dark:text-green-light',
    sent: 'bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-300',
    viewed: 'bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-300',
    accepted: 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
    finished: 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
    rejected: 'bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-300',
    expired: 'bg-yellow-50 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-300',
    negotiating: 'bg-purple-50 dark:bg-purple-500/10 text-purple-700 dark:text-purple-300',
  };
  return map[s] || 'bg-gray-100 dark:bg-white/[0.06] text-gray-600 dark:text-green-light';
}
</script>
