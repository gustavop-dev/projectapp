<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-light text-gray-900">Propuestas</h1>
      <NuxtLink
        to="/admin/proposals/create"
        class="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl
               font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nueva Propuesta
      </NuxtLink>
    </div>

    <!-- Status filter -->
    <div class="flex gap-2 mb-6 flex-wrap">
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
    <div v-else class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 text-left">
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Título</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Cliente</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Inversión</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Expira</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Vistas</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="p in proposals" :key="p.id" class="hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4">
              <NuxtLink
                :to="`/admin/proposals/${p.id}/edit`"
                class="text-sm font-medium text-gray-900 hover:text-emerald-600"
              >
                {{ p.title }}
              </NuxtLink>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600">{{ p.client_name }}</td>
            <td class="px-6 py-4">
              <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="statusClass(p.status)">
                {{ p.status }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600 tabular-nums">
              ${{ Number(p.total_investment).toLocaleString() }} {{ p.currency }}
            </td>
            <td class="px-6 py-4 text-sm text-gray-500">
              <template v-if="p.expires_at">
                {{ new Date(p.expires_at).toLocaleDateString() }}
                <span v-if="p.is_expired" class="text-red-500 text-xs ml-1">(expirada)</span>
                <span v-else-if="p.days_remaining !== null" class="text-xs text-gray-400 ml-1">
                  ({{ p.days_remaining }}d)
                </span>
              </template>
              <span v-else class="text-gray-300">—</span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600 tabular-nums">{{ p.view_count }}</td>
            <td class="px-6 py-4">
              <div class="flex items-center gap-2">
                <NuxtLink
                  :to="`/admin/proposals/${p.id}/edit`"
                  class="text-xs text-emerald-600 hover:text-emerald-700 font-medium"
                >
                  Editar
                </NuxtLink>
                <button
                  v-if="p.status === 'draft'"
                  class="text-xs text-blue-600 hover:text-blue-700 font-medium"
                  @click="handleSend(p.id)"
                >
                  Enviar
                </button>
                <button
                  class="text-xs text-red-500 hover:text-red-700 font-medium"
                  @click="handleDelete(p.id)"
                >
                  Eliminar
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const proposalStore = useProposalStore();
const proposals = computed(() => proposalStore.proposals);
const activeFilter = ref('');

const statusOptions = [
  { value: '', label: 'Todas' },
  { value: 'draft', label: 'Borrador' },
  { value: 'sent', label: 'Enviadas' },
  { value: 'viewed', label: 'Vistas' },
  { value: 'accepted', label: 'Aceptadas' },
  { value: 'expired', label: 'Expiradas' },
];

onMounted(() => {
  proposalStore.fetchProposals();
});

function filterByStatus(status) {
  activeFilter.value = status;
  proposalStore.fetchProposals(status || undefined);
}

async function handleSend(id) {
  if (!confirm('¿Enviar esta propuesta al cliente?')) return;
  await proposalStore.sendProposal(id);
  proposalStore.fetchProposals(activeFilter.value || undefined);
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
</script>
