<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8">
      <h1 class="text-2xl font-light text-gray-900">Propuestas</h1>
      <NuxtLink
        to="/panel/proposals/create"
        class="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl
               font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nueva Propuesta
      </NuxtLink>
    </div>

    <!-- KPI Dashboard -->
    <ProposalDashboard />

    <!-- Floating metrics manual -->
    <MetricsManual />

    <!-- Zombie proposals segment -->
    <div v-if="zombieAlerts.length" class="mb-4 bg-gray-800 border border-gray-700 rounded-xl p-4">
      <div class="flex items-center justify-between mb-3 cursor-pointer" @click="zombieExpanded = !zombieExpanded">
        <div class="flex items-center gap-2">
          <span class="text-lg">🧟</span>
          <h3 class="text-sm font-semibold text-gray-200">Propuestas zombie ({{ zombieAlerts.length }})</h3>
        </div>
        <span class="text-xs text-gray-400">{{ zombieExpanded ? '▲' : '▼' }}</span>
      </div>
      <div v-if="zombieExpanded" class="space-y-2">
        <div
          v-for="alert in zombieAlerts"
          :key="`zombie-${alert.id}-${alert.alert_type}`"
          class="flex items-center justify-between bg-gray-700/50 rounded-lg px-4 py-2.5 border border-gray-600 cursor-pointer hover:border-gray-500 transition-colors"
          @click="router.push(`/panel/proposals/${alert.id}/edit`)"
        >
          <div class="flex items-center gap-3">
            <span class="text-sm">{{ alert.alert_type === 'zombie_draft' ? '📝💀' : alert.alert_type === 'zombie_sent_stale' ? '📤💀' : '💀' }}</span>
            <div>
              <span class="text-sm font-medium text-gray-200">{{ alert.client_name }}</span>
              <span class="text-xs text-gray-400 ml-2">{{ alert.title }}</span>
            </div>
          </div>
          <span class="text-xs text-gray-400 font-medium">{{ alert.message }}</span>
        </div>
      </div>
    </div>

    <!-- Alerts panel -->
    <div v-if="activeAlerts.length || showAlertForm" class="mb-6 bg-amber-50 border border-amber-200 rounded-xl p-4">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <span class="text-lg">⚠️</span>
          <h3 class="text-sm font-semibold text-amber-800">Propuestas que necesitan atención ({{ activeAlerts.length }})</h3>
        </div>
        <button
          type="button"
          class="text-xs text-amber-700 font-medium hover:text-amber-900 transition-colors"
          @click="showAlertForm = !showAlertForm"
        >
          {{ showAlertForm ? 'Cancelar' : '+ Crear recordatorio' }}
        </button>
      </div>

      <!-- Create alert form -->
      <div v-if="showAlertForm" class="mb-4 bg-white rounded-lg border border-amber-100 p-4 space-y-3">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label class="block text-xs text-gray-500 mb-1">Propuesta</label>
            <select v-model="newAlert.proposal" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white outline-none focus:ring-1 focus:ring-emerald-500">
              <option value="">Seleccionar...</option>
              <option v-for="p in proposalStore.proposals" :key="p.id" :value="p.id">{{ p.client_name }} — {{ p.title }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Tipo</label>
            <select v-model="newAlert.alert_type" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white outline-none focus:ring-1 focus:ring-emerald-500">
              <option value="reminder">Recordatorio</option>
              <option value="followup">Seguimiento</option>
              <option value="call">Llamada</option>
              <option value="meeting">Reunión</option>
              <option value="custom">Personalizado</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Fecha</label>
            <input v-model="newAlert.alert_date" type="datetime-local" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none focus:ring-1 focus:ring-emerald-500" />
          </div>
        </div>
        <div class="flex gap-3 items-end">
          <div class="flex-1">
            <label class="block text-xs text-gray-500 mb-1">Mensaje</label>
            <input v-model="newAlert.message" type="text" placeholder="Ej: Llamar al cliente para seguimiento..." class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none focus:ring-1 focus:ring-emerald-500" />
          </div>
          <button
            type="button"
            :disabled="!newAlert.proposal || !newAlert.message"
            class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50"
            @click="handleCreateAlert"
          >
            Crear
          </button>
        </div>
        <p v-if="alertError" class="text-xs text-red-500">{{ alertError }}</p>
      </div>

      <div class="space-y-2">
        <div
          v-for="alert in activeAlerts"
          :key="`${alert.id}-${alert.alert_type}-${alert.manual_alert_id || ''}`"
          class="flex items-center justify-between bg-white rounded-lg px-4 py-2.5 border border-amber-100 cursor-pointer hover:border-amber-300 transition-colors"
          @click="router.push(`/panel/proposals/${alert.id}/edit`)"
        >
          <div class="flex items-center gap-3">
            <span class="text-sm">{{ alertIcon(alert.alert_type) }}</span>
            <div>
              <span class="text-sm font-medium text-gray-800">{{ alert.client_name }}</span>
              <span class="text-xs text-gray-400 ml-2">{{ alert.title }}</span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs text-amber-700 font-medium">{{ alert.message }}</span>
            <button
              v-if="alert.manual_alert_id"
              type="button"
              class="text-xs text-gray-400 hover:text-red-500 transition-colors"
              title="Descartar"
              @click.stop="handleDismissAlert(alert.manual_alert_id)"
            >✕</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Search + Status filter -->
    <div class="flex flex-col sm:flex-row gap-3 mb-6">
      <div class="relative flex-1 max-w-sm">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Buscar por título o cliente..."
          class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-xl text-sm focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
        />
      </div>
      <div class="flex gap-2 flex-wrap">
        <button
          v-for="opt in statusOptions"
          :key="opt.value"
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border"
          :class="activeFilter === opt.value
            ? 'bg-emerald-600 text-white border-emerald-600'
            : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'"
          @click="filterByStatus(opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="proposalStore.isLoading" class="text-center py-12 text-gray-400 text-sm">
      Cargando...
    </div>

    <!-- Empty state -->
    <div v-else-if="proposals.length === 0" class="text-center py-16">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
        <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <p class="text-gray-500 text-sm">No hay propuestas{{ activeFilter ? ` con estado "${activeFilter}"` : '' }}.</p>
    </div>

    <!-- Table -->
    <div v-else class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-x-auto">
      <table class="w-full min-w-[800px]">
        <thead>
          <tr class="border-b border-gray-100 text-left">
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-emerald-600" @click="toggleSort('title')">
              Título <span v-if="sortKey === 'title'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-emerald-600" @click="toggleSort('client_name')">
              Cliente <span v-if="sortKey === 'client_name'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-emerald-600" @click="toggleSort('total_investment')">
              Inversión <span v-if="sortKey === 'total_investment'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-emerald-600" @click="toggleSort('last_activity_at')">
              Última actividad <span v-if="sortKey === 'last_activity_at'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Vistas</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-center" title="Score de calor (1-10)">🔥</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="(p, rowIdx) in paginatedProposals" :key="p.id" class="transition-colors cursor-pointer" :class="p.is_active ? 'hover:bg-gray-50' : 'bg-gray-50 opacity-60'" @click="navigateToProposal(p.id)">
            <td class="px-6 py-4">
              <NuxtLink
                :to="`/panel/proposals/${p.id}/edit`"
                class="text-sm font-medium text-gray-900 hover:text-emerald-600"
              >
                {{ p.title }}
              </NuxtLink>
            </td>
            <td class="px-6 py-4">
              <div class="text-sm text-gray-600">{{ p.client_name }}</div>
              <div v-if="p.client_phone" class="text-[10px] text-gray-400">📱 {{ p.client_phone }}</div>
            </td>
            <td class="px-6 py-4">
              <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="statusClass(p.status)">
                {{ p.status }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600 tabular-nums">
              ${{ Number(p.total_investment).toLocaleString() }} {{ p.currency }}
            </td>
            <td class="px-6 py-4 text-sm text-gray-500">
              <template v-if="p.last_activity_at">
                {{ timeAgo(p.last_activity_at) }}
              </template>
              <template v-else-if="p.created_at">
                {{ timeAgo(p.created_at) }}
                <span class="text-[10px] text-gray-300 ml-1">(creada)</span>
              </template>
              <span v-else class="text-gray-300">—</span>
              <span v-if="isInactive(p)" class="ml-1 inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-red-100 text-red-700">
                {{ inactiveDays(p) }}d sin actividad
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600 tabular-nums">{{ p.view_count }}</td>
            <td class="px-6 py-4 text-center">
              <span v-if="p.heat_score > 0" class="inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold text-white" :class="heatScoreColor(p.heat_score)">
                {{ p.heat_score }}
              </span>
              <span v-else class="text-gray-300 text-xs">—</span>
            </td>
            <td class="px-6 py-4">
              <div class="relative">
                <button
                  class="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-600"
                  @click.stop="toggleDropdown(p.id)"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                  </svg>
                </button>
                <div
                  v-if="openDropdownId === p.id"
                  class="absolute right-0 w-40 bg-white rounded-xl shadow-lg border border-gray-100 py-1 z-50"
                  :class="rowIdx >= proposals.length - 2 ? 'bottom-full mb-1' : 'mt-1'"
                >
                  <NuxtLink
                    :to="`/panel/proposals/${p.id}/edit`"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Editar
                  </NuxtLink>
                  <button
                    v-if="p.status === 'draft'"
                    class="block w-full text-left px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 transition-colors"
                    @click="handleSend(p.id)"
                  >
                    Enviar
                  </button>
                  <button
                    v-if="['sent', 'viewed'].includes(p.status)"
                    class="block w-full text-left px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 transition-colors"
                    @click="handleResend(p.id)"
                  >
                    Re-enviar
                  </button>
                  <button
                    class="block w-full text-left px-4 py-2 text-sm transition-colors"
                    :class="p.is_active ? 'text-yellow-600 hover:bg-yellow-50' : 'text-emerald-600 hover:bg-emerald-50'"
                    @click="handleToggleActive(p.id, p.is_active)"
                  >
                    {{ p.is_active ? 'Desactivar' : 'Activar' }}
                  </button>
                  <button
                    class="block w-full text-left px-4 py-2 text-sm text-indigo-600 hover:bg-indigo-50 transition-colors"
                    @click="handleDuplicate(p.id)"
                  >
                    Duplicar
                  </button>
                  <button
                    class="block w-full text-left px-4 py-2 text-sm transition-colors"
                    :class="copiedId === p.id ? 'text-emerald-600' : 'text-gray-700 hover:bg-gray-50'"
                    @click="handleCopyLink(p)"
                  >
                    {{ copiedId === p.id ? '¡Copiado!' : 'Copiar enlace' }}
                  </button>
                  <a
                    :href="buildWhatsAppUrl(p)"
                    target="_blank"
                    class="block px-4 py-2 text-sm text-green-600 hover:bg-green-50 transition-colors"
                    @click.stop
                  >
                    Enviar por WhatsApp
                  </a>
                  <a
                    :href="'/proposal/' + p.uuid + '?preview=1'"
                    target="_blank"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Preview
                  </a>
                  <button
                    class="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                    @click="handleDelete(p.id)"
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-between px-6 py-3 border-t border-gray-100">
        <span class="text-xs text-gray-400">{{ filteredProposals.length }} propuestas</span>
        <div class="flex gap-1">
          <button
            v-for="page in totalPages"
            :key="page"
            class="w-8 h-8 rounded-lg text-xs font-medium transition-colors"
            :class="currentPage === page ? 'bg-emerald-600 text-white' : 'text-gray-500 hover:bg-gray-100'"
            @click="currentPage = page"
          >
            {{ page }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import ProposalDashboard from '~/components/BusinessProposal/admin/ProposalDashboard.vue';
import MetricsManual from '~/components/BusinessProposal/admin/MetricsManual.vue';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const proposalStore = useProposalStore();
const proposals = computed(() => proposalStore.proposals);
const activeFilter = ref('');
const openDropdownId = ref(null);
const copiedId = ref(null);
const searchQuery = ref('');
const showAlertForm = ref(false);
const alertError = ref('');
const newAlert = reactive({
  proposal: '',
  alert_type: 'reminder',
  message: '',
  alert_date: '',
});
const sortKey = ref('created_at');
const sortDir = ref('desc');
const currentPage = ref(1);
const pageSize = 15;
const zombieExpanded = ref(false);

const ZOMBIE_TYPES = ['zombie', 'zombie_draft', 'zombie_sent_stale'];
const zombieAlerts = computed(() =>
  alerts.value.filter(a => ZOMBIE_TYPES.includes(a.alert_type))
);
const activeAlerts = computed(() =>
  alerts.value.filter(a => !ZOMBIE_TYPES.includes(a.alert_type))
);

function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortDir.value = 'desc';
  }
  currentPage.value = 1;
}

const filteredProposals = computed(() => {
  let list = [...proposals.value];
  // Status filter (client-side fallback)
  if (activeFilter.value) {
    list = list.filter(p => p.status === activeFilter.value);
  }
  // Search
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase();
    list = list.filter(p =>
      (p.title || '').toLowerCase().includes(q) ||
      (p.client_name || '').toLowerCase().includes(q) ||
      (p.client_email || '').toLowerCase().includes(q)
    );
  }
  // Sort
  list.sort((a, b) => {
    let va = a[sortKey.value];
    let vb = b[sortKey.value];
    if (sortKey.value === 'total_investment') {
      va = Number(va) || 0;
      vb = Number(vb) || 0;
    } else {
      va = va || '';
      vb = vb || '';
    }
    if (va < vb) return sortDir.value === 'asc' ? -1 : 1;
    if (va > vb) return sortDir.value === 'asc' ? 1 : -1;
    return 0;
  });
  return list;
});

const totalPages = computed(() => Math.ceil(filteredProposals.value.length / pageSize));
const paginatedProposals = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return filteredProposals.value.slice(start, start + pageSize);
});

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const now = new Date();
  const d = new Date(dateStr);
  const diffMs = now - d;
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'ahora';
  if (mins < 60) return `hace ${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `hace ${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `hace ${days}d`;
  return d.toLocaleDateString();
}

function toggleDropdown(id) {
  openDropdownId.value = openDropdownId.value === id ? null : id;
}

function closeDropdown(e) {
  if (openDropdownId.value !== null) {
    openDropdownId.value = null;
  }
}

const router = useRouter();
function navigateToProposal(id) {
  router.push(`/panel/proposals/${id}/edit`);
}

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown);
});

const statusOptions = [
  { value: '', label: 'Todas' },
  { value: 'draft', label: 'Borrador' },
  { value: 'sent', label: 'Enviadas' },
  { value: 'viewed', label: 'Vistas' },
  { value: 'accepted', label: 'Aceptadas' },
  { value: 'rejected', label: 'Rechazadas' },
  { value: 'expired', label: 'Expiradas' },
];

const alerts = ref([]);

onMounted(async () => {
  proposalStore.fetchProposals();
  document.addEventListener('click', closeDropdown);
  const alertResult = await proposalStore.fetchAlerts();
  if (alertResult.success) alerts.value = alertResult.data || [];
});

function alertIcon(type) {
  const map = {
    not_viewed: '👁️‍🗨️', not_responded: '⏳', expiring_soon: '🔥',
    manual_reminder: '🔔', manual_followup: '📩', manual_call: '📞',
    manual_meeting: '🤝', manual_custom: '📝',
    seller_inactive: '🏷️', zombie: '💀', late_return: '🔄',
    manual_discount_suggestion: '💰', discount_suggestion: '💰',
  };
  return map[type] || '⚠️';
}

async function handleCreateAlert() {
  alertError.value = '';
  const payload = {
    proposal: newAlert.proposal,
    alert_type: newAlert.alert_type,
    message: newAlert.message,
    alert_date: newAlert.alert_date
      ? new Date(newAlert.alert_date).toISOString()
      : new Date().toISOString(),
  };
  const result = await proposalStore.createAlert(payload);
  if (result.success) {
    showAlertForm.value = false;
    newAlert.proposal = '';
    newAlert.alert_type = 'reminder';
    newAlert.message = '';
    newAlert.alert_date = '';
    const alertResult = await proposalStore.fetchAlerts();
    if (alertResult.success) alerts.value = alertResult.data || [];
  } else {
    alertError.value = 'Error al crear el recordatorio.';
  }
}

async function handleDismissAlert(alertId) {
  const result = await proposalStore.dismissAlert(alertId);
  if (result.success) {
    alerts.value = alerts.value.filter(a => a.manual_alert_id !== alertId);
  }
}

function filterByStatus(status) {
  activeFilter.value = status;
  proposalStore.fetchProposals(status || undefined);
}

async function handleSend(id) {
  if (!confirm('¿Enviar esta propuesta al cliente?')) return;
  await proposalStore.sendProposal(id);
  proposalStore.fetchProposals(activeFilter.value || undefined);
}

async function handleResend(id) {
  if (!confirm('¿Re-enviar esta propuesta? Se mantendrá la misma fecha de expiración.')) return;
  await proposalStore.resendProposal(id);
  proposalStore.fetchProposals(activeFilter.value || undefined);
}

async function handleToggleActive(id, currentlyActive) {
  const label = currentlyActive ? 'desactivar' : 'activar';
  if (!confirm(`¿${label.charAt(0).toUpperCase() + label.slice(1)} esta propuesta?`)) return;
  await proposalStore.toggleProposalActive(id);
}

async function handleDuplicate(id) {
  openDropdownId.value = null;
  const result = await proposalStore.duplicateProposal(id);
  if (result.success) {
    router.push(`/panel/proposals/${result.data.id}/edit`);
  }
}

function handleCopyLink(p) {
  const url = `${window.location.origin}/proposal/${p.uuid}`;
  navigator.clipboard.writeText(url).then(() => {
    copiedId.value = p.id;
    setTimeout(() => { copiedId.value = null; }, 1500);
  });
}

async function handleDelete(id) {
  if (!confirm('¿Eliminar esta propuesta? Esta acción no se puede deshacer.')) return;
  await proposalStore.deleteProposal(id);
}

function statusClass(status) {
  const map = {
    draft: 'bg-gray-100 text-gray-600',
    sent: 'bg-blue-50 text-blue-700',
    viewed: 'bg-green-50 text-green-700',
    accepted: 'bg-emerald-50 text-emerald-700',
    rejected: 'bg-red-50 text-red-700',
    expired: 'bg-yellow-50 text-yellow-700',
  };
  return map[status] || 'bg-gray-100 text-gray-600';
}

function isInactive(p) {
  if (!['sent', 'viewed'].includes(p.status)) return false;
  const ref = p.last_activity_at || p.sent_at || p.created_at;
  if (!ref) return false;
  return (Date.now() - new Date(ref).getTime()) / 86400000 >= 3;
}

function inactiveDays(p) {
  const ref = p.last_activity_at || p.sent_at || p.created_at;
  if (!ref) return 0;
  return Math.floor((Date.now() - new Date(ref).getTime()) / 86400000);
}

function heatScoreColor(score) {
  if (score >= 8) return 'bg-red-500';
  if (score >= 5) return 'bg-orange-400';
  if (score >= 2) return 'bg-yellow-400 text-gray-800';
  return 'bg-gray-300 text-gray-700';
}

function buildWhatsAppUrl(p) {
  const url = `${window.location.origin}/proposal/${p.uuid}`;
  const phone = (p.client_phone || '').replace(/\D/g, '');
  const msg = encodeURIComponent(
    `Hola ${p.client_name}, te comparto la propuesta "${p.title}": ${url}\n\n¿Tienes alguna pregunta?`
  );
  return phone
    ? `https://wa.me/${phone}?text=${msg}`
    : `https://wa.me/?text=${msg}`;
}
</script>
