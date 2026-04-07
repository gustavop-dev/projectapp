<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8">
      <div>
        <h1 class="text-2xl font-light text-gray-900">Clientes</h1>
        <p class="text-sm text-gray-400 mt-1">Historial de propuestas por cliente</p>
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
    />

    <!-- Search + Filter toggle -->
    <div class="flex items-center gap-2 mb-5">
      <input
        v-model="search"
        type="text"
        placeholder="Buscar por nombre o email..."
        class="w-full sm:max-w-xs px-4 py-2.5 border border-gray-200 rounded-xl text-sm
               focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
      />
      <UiFilterToggleButton :open="isFilterPanelOpen" :count="activeFilterCount" @click="toggleFilterPanel" />
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
    <div v-if="loading" class="text-center py-16 text-gray-400 text-sm">
      Cargando clientes...
    </div>

    <!-- Empty -->
    <div v-else-if="filteredClients.length === 0" class="text-center py-16 text-gray-400 text-sm">
      {{ search || hasActiveFilters ? 'No se encontraron clientes con ese criterio.' : 'No hay clientes aún.' }}
    </div>

    <!-- Client list -->
    <div v-else class="space-y-3">
      <div
        v-for="client in filteredClients"
        :key="client.client_key"
        class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"
      >
        <!-- Client row header -->
        <div
          class="px-5 py-4 flex flex-wrap items-center justify-between gap-3 cursor-pointer hover:bg-gray-50 transition-colors"
          @click="toggleClient(client)"
        >
          <div class="flex items-center gap-4">
            <!-- Avatar -->
            <div class="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
              <span class="text-emerald-700 font-bold text-sm">{{ initials(client.client_name) }}</span>
            </div>
            <div>
              <p class="text-sm font-semibold text-gray-900">{{ client.client_name }}</p>
              <p v-if="client.client_email" class="text-xs text-gray-400 mt-0.5">{{ client.client_email }}</p>
            </div>
          </div>

          <div class="flex items-center gap-3 flex-wrap">
            <!-- Stats pills -->
            <span class="text-xs px-2.5 py-1 rounded-full bg-gray-100 text-gray-600 font-medium">
              {{ client.total_proposals }} propuesta{{ client.total_proposals !== 1 ? 's' : '' }}
            </span>
            <span v-if="client.accepted" class="text-xs px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 font-medium">
              ✅ {{ client.accepted }} aceptada{{ client.accepted !== 1 ? 's' : '' }}
            </span>
            <span v-if="client.rejected" class="text-xs px-2.5 py-1 rounded-full bg-red-50 text-red-600 font-medium">
              ❌ {{ client.rejected }} rechazada{{ client.rejected !== 1 ? 's' : '' }}
            </span>
            <span v-if="client.pending" class="text-xs px-2.5 py-1 rounded-full bg-blue-50 text-blue-600 font-medium">
              🕐 {{ client.pending }} pendiente{{ client.pending !== 1 ? 's' : '' }}
            </span>
            <!-- Last status -->
            <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="statusClass(client.last_status)">
              {{ client.last_status }}
            </span>
            <!-- Expand chevron -->
            <svg
              class="w-4 h-4 text-gray-400 transition-transform flex-shrink-0"
              :class="{ 'rotate-180': expandedClients.has(client.client_key) }"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>

        <!-- Expanded: proposals list -->
        <div
          v-if="expandedClients.has(client.client_key)"
          class="border-t border-gray-100"
        >
          <div class="overflow-x-auto">
            <table class="w-full min-w-[600px] text-sm">
              <thead>
                <tr class="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wider">
                  <th class="px-5 py-3">Propuesta</th>
                  <th class="px-4 py-3">Estado</th>
                  <th class="px-4 py-3">Inversión</th>
                  <th class="px-4 py-3 text-center">Vistas</th>
                  <th class="px-4 py-3">Enviada</th>
                  <th class="px-5 py-3">Motivo rechazo</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr
                  v-for="p in client.proposals"
                  :key="p.id"
                  class="hover:bg-gray-50/60 transition-colors"
                >
                  <td class="px-5 py-3">
                    <NuxtLink
                      :to="localePath(`/panel/proposals/${p.id}/edit`)"
                      class="font-medium text-gray-900 hover:text-emerald-600 transition-colors"
                    >
                      {{ p.title }}
                    </NuxtLink>
                  </td>
                  <td class="px-4 py-3">
                    <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="statusClass(p.status)">
                      {{ p.status }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-gray-600 tabular-nums">
                    ${{ Number(p.total_investment).toLocaleString() }} {{ p.currency }}
                  </td>
                  <td class="px-4 py-3 text-center text-gray-600">{{ p.view_count }}</td>
                  <td class="px-4 py-3 text-gray-500 text-xs">
                    {{ p.sent_at ? formatDate(p.sent_at) : '—' }}
                  </td>
                  <td class="px-5 py-3">
                    <template v-if="p.rejection_reason">
                      <span class="text-xs text-red-600 font-medium">{{ p.rejection_reason }}</span>
                      <p v-if="p.rejection_comment" class="text-xs text-gray-400 mt-0.5 max-w-[200px] truncate" :title="p.rejection_comment">
                        {{ p.rejection_comment }}
                      </p>
                    </template>
                    <span v-else class="text-gray-300">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useClientFilters } from '~/composables/useClientFilters';
import ClientFilterPanel from '~/components/clients/ClientFilterPanel.vue';
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue';

const localePath = useLocalePath();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const proposalStore = useProposalStore();

const clients = ref([]);
const loading = ref(true);
const search = ref('');
const expandedClients = ref(new Set());

const {
  currentFilters,
  savedTabs,
  activeTabId,
  isFilterPanelOpen,
  hasActiveFilters,
  activeFilterCount,
  isTabLimitReached,
  applyFilters,
  resetFilters,
  selectTab,
  saveTab,
  deleteTab,
  renameTab,
} = useClientFilters();

const filteredClients = computed(() => {
  const q = search.value.trim().toLowerCase();
  return applyFilters(clients.value).filter(
    (c) =>
      !q ||
      c.client_name.toLowerCase().includes(q) ||
      c.client_email.toLowerCase().includes(q),
  );
});

onMounted(async () => {
  const result = await proposalStore.fetchClients();
  if (result.success) {
    clients.value = result.data;
  }
  loading.value = false;
});

function toggleFilterPanel() {
  isFilterPanelOpen.value = !isFilterPanelOpen.value;
}

function handleCreateTab(name) {
  saveTab(name);
  isFilterPanelOpen.value = true;
}

function handleResetFilters() {
  resetFilters();
  isFilterPanelOpen.value = false;
}

function toggleClient(client) {
  const key = client.client_key;
  if (expandedClients.value.has(key)) {
    expandedClients.value.delete(key);
  } else {
    expandedClients.value.add(key);
  }
  expandedClients.value = new Set(expandedClients.value);
}

function initials(name) {
  return (name || '?')
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() || '')
    .join('');
}

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' });
}

function statusClass(s) {
  const map = {
    draft: 'bg-gray-100 text-gray-600',
    sent: 'bg-blue-50 text-blue-700',
    viewed: 'bg-green-50 text-green-700',
    accepted: 'bg-emerald-50 text-emerald-700',
    rejected: 'bg-red-50 text-red-600',
    expired: 'bg-yellow-50 text-yellow-700',
  };
  return map[s] || 'bg-gray-100 text-gray-600';
}
</script>
