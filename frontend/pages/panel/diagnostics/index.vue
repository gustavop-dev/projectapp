<template>
  <div>
    <header class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100">Diagnósticos de aplicaciones</h1>
      <NuxtLink
        :to="localePath('/panel/diagnostics/create')"
        class="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl
               font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm
               dark:bg-emerald-700 dark:hover:bg-emerald-600"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo diagnóstico
      </NuxtLink>
    </header>

    <!-- Search + Filter toggle -->
    <div class="flex flex-col sm:flex-row gap-3 mb-4">
      <div class="relative flex-1 max-w-sm">
        <svg
          class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Buscar por título o cliente..."
          data-testid="diagnostics-search-input"
          class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-xl text-sm
                 focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 outline-none
                 dark:border-white/[0.08] dark:bg-gray-800 dark:text-white"
        />
      </div>
      <UiFilterToggleButton
        :open="isFilterPanelOpen"
        :count="activeFilterCount"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      />
      <button
        type="button"
        class="text-sm text-gray-500 hover:text-gray-700 underline"
        @click="reload"
      >Actualizar</button>
    </div>

    <!-- Filter panel -->
    <DiagnosticFilterPanel
      :model-value="currentFilters"
      :is-open="isFilterPanelOpen"
      :filter-count="activeFilterCount"
      @update:model-value="Object.assign(currentFilters, $event)"
      @reset="handleResetFilters"
    />

    <div v-if="store.isLoading" class="text-gray-500 text-sm">Cargando…</div>

    <div
      v-else-if="!filteredDiagnostics.length"
      class="text-center py-16 bg-gray-50 rounded-xl border border-dashed"
    >
      <p class="text-gray-600">
        {{ hasActiveFilters || searchQuery ? 'No hay diagnósticos que coincidan con los filtros.' : 'Aún no has creado diagnósticos.' }}
      </p>
      <NuxtLink
        v-if="!store.diagnostics.length"
        :to="localePath('/panel/diagnostics/create')"
        class="inline-block mt-3 text-emerald-600 hover:underline text-sm"
      >Crear el primero</NuxtLink>
    </div>

    <table v-else class="min-w-full bg-white border rounded-xl overflow-hidden text-sm">
      <thead class="bg-gray-50">
        <tr class="text-left text-gray-600">
          <th class="px-4 py-3">Cliente</th>
          <th class="px-4 py-3">Título</th>
          <th class="px-4 py-3">Estado</th>
          <th class="px-4 py-3">Inversión</th>
          <th class="px-4 py-3">Última vista</th>
          <th class="px-4 py-3"></th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="d in filteredDiagnostics"
          :key="d.id"
          class="border-t hover:bg-gray-50"
          :data-testid="`diagnostic-row-${d.id}`"
        >
          <td class="px-4 py-3">
            <div class="font-medium text-gray-900">{{ d.client?.name || '—' }}</div>
            <div class="text-xs text-gray-500">{{ d.client?.email }}</div>
          </td>
          <td class="px-4 py-3 text-gray-700">{{ d.title }}</td>
          <td class="px-4 py-3">
            <DiagnosticStatusBadge :status="d.status" />
          </td>
          <td class="px-4 py-3 text-gray-700">
            <span v-if="d.investment_amount">{{ formatMoney(d.investment_amount) }} {{ d.currency }}</span>
            <span v-else class="text-gray-400">—</span>
          </td>
          <td class="px-4 py-3 text-gray-500 text-xs">
            <span v-if="d.last_viewed_at">{{ formatDate(d.last_viewed_at) }} ({{ d.view_count }} vistas)</span>
            <span v-else>—</span>
          </td>
          <td class="px-4 py-3 text-right">
            <NuxtLink
              :to="localePath(`/panel/diagnostics/${d.id}/edit`)"
              class="text-emerald-600 hover:underline text-sm"
            >Abrir</NuxtLink>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import DiagnosticStatusBadge from '~/components/WebAppDiagnostic/DiagnosticStatusBadge.vue';
import DiagnosticFilterPanel from '~/components/WebAppDiagnostic/DiagnosticFilterPanel.vue';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const localePath = useLocalePath();
const store = useDiagnosticsStore();

const searchQuery = ref('');
const isFilterPanelOpen = ref(false);

const DEFAULT_FILTERS = {
  statuses: [],
  investmentMin: null,
  investmentMax: null,
  createdAfter: null,
  createdBefore: null,
};
const currentFilters = reactive({ ...DEFAULT_FILTERS });

const activeFilterCount = computed(() => {
  let count = 0;
  if (currentFilters.statuses.length) count += 1;
  if (currentFilters.investmentMin != null && currentFilters.investmentMin !== '') count += 1;
  if (currentFilters.investmentMax != null && currentFilters.investmentMax !== '') count += 1;
  if (currentFilters.createdAfter) count += 1;
  if (currentFilters.createdBefore) count += 1;
  return count;
});

const hasActiveFilters = computed(() => activeFilterCount.value > 0);

function handleResetFilters() {
  Object.assign(currentFilters, DEFAULT_FILTERS);
}

const filteredDiagnostics = computed(() => {
  const needle = searchQuery.value.trim().toLowerCase();
  const statuses = currentFilters.statuses;
  const invMin = currentFilters.investmentMin;
  const invMax = currentFilters.investmentMax;
  const after = currentFilters.createdAfter ? new Date(currentFilters.createdAfter) : null;
  const before = currentFilters.createdBefore ? new Date(currentFilters.createdBefore) : null;

  return store.diagnostics.filter((d) => {
    if (needle) {
      const haystack = [
        d.title || '',
        d.client?.name || '',
        d.client?.email || '',
      ].join(' ').toLowerCase();
      if (!haystack.includes(needle)) return false;
    }
    if (statuses.length && !statuses.includes(d.status)) return false;

    const amount = Number(d.investment_amount || 0);
    if (invMin != null && invMin !== '' && amount < Number(invMin)) return false;
    if (invMax != null && invMax !== '' && amount > Number(invMax)) return false;

    if (after || before) {
      if (!d.created_at) return false;
      const created = new Date(d.created_at);
      if (after && created < after) return false;
      if (before && created > new Date(before.getTime() + 24 * 60 * 60 * 1000 - 1)) return false;
    }
    return true;
  });
});

function reload() {
  store.fetchAll();
}

function formatMoney(amount) {
  const n = Number(amount);
  if (Number.isNaN(n)) return amount;
  return new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 }).format(n);
}
function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
}

onMounted(reload);
</script>
