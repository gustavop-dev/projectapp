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
            <th class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider w-12">ID</th>
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
            <td class="px-4 py-4 text-xs text-gray-400 tabular-nums">#{{ p.id }}</td>
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
              <div class="flex items-center gap-2">
                <button
                  v-if="p.status === 'draft' && p.client_email"
                  class="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-xs font-medium hover:bg-blue-100 transition-colors border border-blue-200"
                  @click.stop="handleSend(p.id)"
                >
                  📤 Enviar
                </button>
                <button
                  class="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-600"
                  @click.stop="actionsModalProposal = p"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

    <!-- Actions modal -->
    <Teleport to="body">
      <Transition name="fade-modal">
        <div
          v-if="actionsModalProposal"
          class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
          @click.self="actionsModalProposal = null"
        >
          <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full">
            <!-- Header -->
            <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <div>
                <h3 class="text-base font-bold text-gray-900 truncate">{{ actionsModalProposal.title }}</h3>
                <p class="text-xs text-gray-500 mt-0.5">{{ actionsModalProposal.client_name }}</p>
              </div>
              <button class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-100 transition-colors" @click="actionsModalProposal = null">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <!-- Actions list -->
            <div class="p-3 space-y-1 max-h-[60vh] overflow-y-auto">
              <template v-for="action in proposalActions" :key="action.key">
                <component
                  :is="action.href ? 'a' : action.to ? 'NuxtLink' : 'button'"
                  v-bind="action.href ? { href: action.href, target: '_blank', rel: 'noopener noreferrer' } : action.to ? { to: action.to } : {}"
                  class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-colors group"
                  :class="action.danger ? 'hover:bg-red-50' : 'hover:bg-gray-50'"
                  @click="action.onClick ? action.onClick() : null"
                >
                  <span class="w-9 h-9 rounded-lg flex items-center justify-center text-lg flex-shrink-0"
                    :class="action.danger ? 'bg-red-50 text-red-500' : action.bgClass || 'bg-gray-100'"
                  >
                    {{ action.icon }}
                  </span>
                  <div class="flex-1 min-w-0">
                    <span class="text-sm font-medium block" :class="action.danger ? 'text-red-600' : action.textClass || 'text-gray-800'">{{ action.label }}</span>
                  </div>
                  <!-- Info tooltip -->
                  <div class="relative flex-shrink-0 group/info">
                    <span class="w-6 h-6 rounded-full bg-gray-100 group-hover/info:bg-emerald-50 flex items-center justify-center text-gray-400 group-hover/info:text-emerald-600 text-[11px] cursor-help transition-colors">?</span>
                    <div class="absolute right-0 bottom-full mb-2 w-52 bg-gray-900 text-white text-xs rounded-xl px-3 py-2 shadow-lg opacity-0 pointer-events-none group-hover/info:opacity-100 group-hover/info:pointer-events-auto transition-opacity z-10 leading-relaxed">
                      {{ action.info }}
                      <div class="absolute -bottom-1 right-3 w-2 h-2 bg-gray-900 rotate-45" />
                    </div>
                  </div>
                </component>
              </template>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Send confirmation modal -->
    <Teleport to="body">
      <Transition name="fade-modal">
        <div
          v-if="sendConfirmId"
          class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
          @click.self="sendConfirmId = null"
        >
          <div class="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6 text-center">
            <div class="text-4xl mb-3">📤</div>
            <h3 class="text-lg font-bold text-gray-900 mb-2">¿Enviar esta propuesta?</h3>
            <p class="text-sm text-gray-500 mb-6">Se enviará un email al cliente con el enlace de la propuesta.</p>
            <div class="flex gap-3 justify-center">
              <button
                class="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 transition-colors"
                :disabled="isSending"
                @click="confirmSend"
              >
                {{ isSending ? 'Enviando...' : 'Sí, enviar' }}
              </button>
              <button
                class="px-6 py-2.5 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors"
                @click="sendConfirmId = null"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

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
import { computed, onMounted, reactive, ref } from 'vue';
import ProposalDashboard from '~/components/BusinessProposal/admin/ProposalDashboard.vue';
import MetricsManual from '~/components/BusinessProposal/admin/MetricsManual.vue';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const proposalStore = useProposalStore();
const proposals = computed(() => proposalStore.proposals);
const activeFilter = ref('');
const actionsModalProposal = ref(null);
const copiedId = ref(null);
const sendConfirmId = ref(null);
const isSending = ref(false);
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


const proposalActions = computed(() => {
  const p = actionsModalProposal.value;
  if (!p) return [];
  const actions = [];

  actions.push({
    key: 'edit',
    icon: '✏️',
    label: 'Editar propuesta',
    info: 'Abre el editor para modificar secciones, precios y contenido de la propuesta.',
    to: `/panel/proposals/${p.id}/edit`,
    bgClass: 'bg-gray-100',
    textClass: 'text-gray-800',
    onClick: () => { actionsModalProposal.value = null; },
  });

  actions.push({
    key: 'preview',
    icon: '👁️',
    label: 'Ver preview',
    info: 'Abre la propuesta tal como la ve el cliente, sin registrar vistas.',
    href: `/proposal/${p.uuid}?preview=1`,
    bgClass: 'bg-purple-50 text-purple-600',
    textClass: 'text-purple-700',
  });

  if (p.status === 'draft') {
    actions.push({
      key: 'send',
      icon: '📤',
      label: 'Enviar al cliente',
      info: 'Envía un email al cliente con el enlace de la propuesta. Cambia el estado a "enviada".',
      bgClass: 'bg-blue-50 text-blue-600',
      textClass: 'text-blue-700',
      onClick: () => { actionsModalProposal.value = null; handleSend(p.id); },
    });
  }

  if (['sent', 'viewed'].includes(p.status)) {
    actions.push({
      key: 'resend',
      icon: '🔄',
      label: 'Re-enviar email',
      info: 'Envía nuevamente el email al cliente. Mantiene la misma fecha de expiración.',
      bgClass: 'bg-blue-50 text-blue-600',
      textClass: 'text-blue-700',
      onClick: () => { actionsModalProposal.value = null; handleResend(p.id); },
    });
  }

  actions.push({
    key: 'copy',
    icon: copiedId.value === p.id ? '✅' : '🔗',
    label: copiedId.value === p.id ? '¡Enlace copiado!' : 'Copiar enlace',
    info: 'Copia el enlace público de la propuesta al portapapeles para compartir manualmente.',
    bgClass: copiedId.value === p.id ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-100',
    textClass: copiedId.value === p.id ? 'text-emerald-600' : 'text-gray-800',
    onClick: () => { handleCopyLink(p); },
  });

  actions.push({
    key: 'whatsapp',
    icon: '💬',
    label: 'Enviar por WhatsApp',
    info: 'Abre WhatsApp con un mensaje pre-escrito incluyendo el enlace de la propuesta.',
    href: buildWhatsAppUrl(p),
    bgClass: 'bg-green-50 text-green-600',
    textClass: 'text-green-700',
  });

  actions.push({
    key: 'duplicate',
    icon: '📋',
    label: 'Duplicar propuesta',
    info: 'Crea una copia exacta de esta propuesta para reutilizar con otro cliente.',
    bgClass: 'bg-indigo-50 text-indigo-600',
    textClass: 'text-indigo-700',
    onClick: () => { actionsModalProposal.value = null; handleDuplicate(p.id); },
  });

  actions.push({
    key: 'toggle',
    icon: p.is_active ? '⏸️' : '▶️',
    label: p.is_active ? 'Desactivar' : 'Activar',
    info: p.is_active
      ? 'Desactiva la propuesta. El cliente no podrá acceder al enlace.'
      : 'Reactiva la propuesta para que el cliente pueda verla nuevamente.',
    bgClass: p.is_active ? 'bg-yellow-50 text-yellow-600' : 'bg-emerald-50 text-emerald-600',
    textClass: p.is_active ? 'text-yellow-700' : 'text-emerald-700',
    onClick: () => { actionsModalProposal.value = null; handleToggleActive(p.id, p.is_active); },
  });

  actions.push({
    key: 'delete',
    icon: '🗑️',
    label: 'Eliminar',
    info: 'Elimina permanentemente la propuesta. Esta acción no se puede deshacer.',
    danger: true,
    onClick: () => { actionsModalProposal.value = null; handleDelete(p.id); },
  });

  return actions;
});

const router = useRouter();
function navigateToProposal(id) {
  router.push(`/panel/proposals/${id}/edit`);
}

const statusOptions = [
  { value: '', label: 'Todas' },
  { value: 'draft', label: 'Borrador' },
  { value: 'sent', label: 'Enviadas' },
  { value: 'viewed', label: 'Vistas' },
  { value: 'accepted', label: 'Aceptadas' },
  { value: 'rejected', label: 'Rechazadas' },
  { value: 'negotiating', label: 'Negociando' },
  { value: 'expired', label: 'Expiradas' },
];

const alerts = ref([]);

onMounted(async () => {
  proposalStore.fetchProposals();
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
    manual_post_expiration_visit: '🔥🕰️', post_expiration_visit: '🔥🕰️',
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

function handleSend(id) {
  sendConfirmId.value = id;
}

async function confirmSend() {
  if (!sendConfirmId.value) return;
  isSending.value = true;
  try {
    await proposalStore.sendProposal(sendConfirmId.value);
    sendConfirmId.value = null;
    proposalStore.fetchProposals(activeFilter.value || undefined);
  } finally {
    isSending.value = false;
  }
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
    negotiating: 'bg-amber-50 text-amber-700',
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

<style scoped>
.fade-modal-enter-active,
.fade-modal-leave-active {
  transition: opacity 0.2s ease;
}
.fade-modal-enter-from,
.fade-modal-leave-to {
  opacity: 0;
}
</style>
