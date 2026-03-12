<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-light text-gray-900">Portfolio Works</h1>
      <NuxtLink
        :to="localePath('/panel/portfolio/create')"
        class="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl
               font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo Proyecto
      </NuxtLink>
    </div>

    <!-- Loading -->
    <div v-if="portfolioStore.isLoading" class="flex justify-center py-12">
      <div class="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
    </div>

    <div v-else>
      <div v-if="works.length === 0" class="bg-white rounded-xl shadow-sm border border-gray-100 px-6 py-12 text-center text-gray-400 text-sm">
        No hay proyectos aún. Crea el primero.
      </div>

      <!-- Mobile cards -->
      <div v-else class="sm:hidden space-y-3">
        <div v-for="work in works" :key="work.id" class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <div class="flex items-start justify-between gap-3 mb-2">
            <NuxtLink :to="localePath(`/panel/portfolio/${work.id}/edit`)" class="text-sm font-medium text-gray-900 hover:text-emerald-600 transition-colors leading-tight">
              {{ work.title_es }}
            </NuxtLink>
            <span class="text-[10px] px-2 py-0.5 rounded-full font-medium flex-shrink-0" :class="statusBadgeClass(work)">
              {{ statusLabel(work) }}
            </span>
          </div>
          <p class="text-xs text-gray-400 mb-3">{{ work.slug }} · {{ formatDate(work.published_at || work.created_at) }}</p>
          <div class="flex items-center gap-3">
            <NuxtLink :to="localePath(`/panel/portfolio/${work.id}/edit`)" class="text-xs text-emerald-600 font-medium">Editar</NuxtLink>
            <button class="text-xs text-gray-500 hover:text-emerald-600 transition-colors" @click="handleDuplicate(work)">Duplicar</button>
            <button class="text-xs text-red-400 hover:text-red-600 transition-colors" @click="handleDelete(work)">Eliminar</button>
          </div>
        </div>
      </div>

      <!-- Desktop table -->
      <div class="hidden sm:block bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100 text-left">
                <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Título</th>
                <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Orden</th>
                <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                <th class="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="work in works" :key="work.id" class="hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4">
                  <NuxtLink :to="localePath(`/panel/portfolio/${work.id}/edit`)" class="text-sm font-medium text-gray-900 hover:text-emerald-600 transition-colors">
                    {{ work.title_es }}
                  </NuxtLink>
                  <p class="text-xs text-gray-400 mt-0.5">{{ work.title_en }} · {{ work.slug }}</p>
                </td>
                <td class="px-6 py-4">
                  <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="statusBadgeClass(work)">
                    {{ statusLabel(work) }}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">{{ work.order }}</td>
                <td class="px-6 py-4 text-sm text-gray-500">{{ formatDate(work.published_at || work.created_at) }}</td>
                <td class="px-6 py-4 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <NuxtLink :to="localePath(`/panel/portfolio/${work.id}/edit`)" class="text-xs text-gray-500 hover:text-emerald-600 transition-colors">Editar</NuxtLink>
                    <button class="text-xs text-gray-500 hover:text-emerald-600 transition-colors" @click="handleDuplicate(work)">Duplicar</button>
                    <button class="text-xs text-red-400 hover:text-red-600 transition-colors" @click="handleDelete(work)">Eliminar</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { usePortfolioWorksStore } from '~/stores/portfolio_works';

const localePath = useLocalePath();

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const portfolioStore = usePortfolioWorksStore();
const works = computed(() => portfolioStore.works);

onMounted(() => { portfolioStore.fetchAdminWorks(); });

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('es-CO', { year: 'numeric', month: 'short', day: 'numeric' });
}

function statusLabel(work) {
  return work.is_published ? 'Publicado' : 'Borrador';
}

function statusBadgeClass(work) {
  return work.is_published ? 'bg-emerald-50 text-emerald-700' : 'bg-gray-100 text-gray-600';
}

async function handleDuplicate(work) {
  if (!confirm(`¿Duplicar "${work.title_es}"?`)) return;
  await portfolioStore.duplicateWork(work.id);
}

async function handleDelete(work) {
  if (!confirm(`¿Eliminar "${work.title_es}"?`)) return;
  await portfolioStore.deleteWork(work.id);
}
</script>
