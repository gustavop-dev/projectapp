<template>
  <div>
    <h1 class="text-2xl font-light text-gray-900 mb-8">Dashboard</h1>

    <!-- Stats cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <p class="text-sm text-gray-500 mb-1">Total Propuestas</p>
        <p class="text-3xl font-light text-gray-900">{{ proposals.length }}</p>
      </div>
      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <p class="text-sm text-gray-500 mb-1">Enviadas</p>
        <p class="text-3xl font-light text-emerald-600">
          {{ proposals.filter(p => p.status === 'sent').length }}
        </p>
      </div>
      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <p class="text-sm text-gray-500 mb-1">Vistas por clientes</p>
        <p class="text-3xl font-light text-blue-600">
          {{ proposals.filter(p => p.status === 'viewed').length }}
        </p>
      </div>
    </div>

    <!-- Quick action -->
    <div class="mb-10">
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

    <!-- Recent proposals -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100">
      <div class="px-6 py-4 border-b border-gray-100">
        <h2 class="text-sm font-medium text-gray-700">Propuestas recientes</h2>
      </div>
      <div v-if="proposals.length === 0" class="px-6 py-12 text-center text-gray-400 text-sm">
        No hay propuestas aún. Crea la primera.
      </div>
      <ul v-else class="divide-y divide-gray-50">
        <li
          v-for="p in recentProposals"
          :key="p.id"
          class="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div>
            <NuxtLink
              :to="`/admin/proposals/${p.id}/edit`"
              class="text-sm font-medium text-gray-900 hover:text-emerald-600 transition-colors"
            >
              {{ p.title }}
            </NuxtLink>
            <p class="text-xs text-gray-400 mt-0.5">{{ p.client_name }}</p>
          </div>
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium"
            :class="statusClass(p.status)"
          >
            {{ p.status }}
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const proposalStore = useProposalStore();
const proposals = computed(() => proposalStore.proposals);
const recentProposals = computed(() => proposals.value.slice(0, 5));

onMounted(() => {
  proposalStore.fetchProposals();
});

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
