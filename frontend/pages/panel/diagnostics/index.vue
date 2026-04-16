<template>
  <div>
    <header class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100">Diagnósticos de aplicaciones</h1>
      <NuxtLink
        :to="localePath('/panel/diagnostics/create')"
        class="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl
               font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm"
      >
        + Nuevo diagnóstico
      </NuxtLink>
    </header>

    <div class="mb-4 flex flex-wrap gap-3 items-center">
      <select v-model="statusFilter" class="border rounded px-3 py-2 text-sm" @change="reload">
        <option v-for="opt in STATUS_FILTER_OPTIONS" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
      <button class="text-sm text-gray-600 underline" @click="reload">Actualizar</button>
    </div>

    <div v-if="store.isLoading" class="text-gray-500 text-sm">Cargando…</div>

    <div v-else-if="!store.diagnostics.length" class="text-center py-16 bg-gray-50 rounded-xl border border-dashed">
      <p class="text-gray-600">Aún no has creado diagnósticos.</p>
      <NuxtLink
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
        <tr v-for="d in store.diagnostics" :key="d.id" class="border-t hover:bg-gray-50">
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
import { ref, onMounted } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import { STATUS_FILTER_OPTIONS } from '~/stores/diagnostics_constants';
import DiagnosticStatusBadge from '~/components/WebAppDiagnostic/DiagnosticStatusBadge.vue';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const localePath = useLocalePath();
const store = useDiagnosticsStore();
const statusFilter = ref('');

function reload() {
  store.fetchAll(statusFilter.value ? { status: statusFilter.value } : {});
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
