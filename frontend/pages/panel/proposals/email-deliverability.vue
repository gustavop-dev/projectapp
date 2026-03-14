<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8">
      <div>
        <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100">Email Deliverability</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Monitoreo de emails enviados en los últimos 30 días.
        </p>
      </div>
      <NuxtLink
        :to="localePath('/panel/proposals')"
        class="inline-flex items-center gap-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Volver a Propuestas
      </NuxtLink>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="text-center py-16 text-gray-400 text-sm">
      Cargando estadísticas de email...
    </div>

    <template v-else-if="stats">
      <!-- KPI Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm dark:bg-gray-800 dark:border-gray-700">
          <div class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Total Enviados</div>
          <div class="text-3xl font-bold text-gray-900 dark:text-gray-100 tabular-nums">{{ stats.total_emails_30d }}</div>
          <div class="text-xs text-gray-400 mt-1">últimos 30 días</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm dark:bg-gray-800 dark:border-gray-700">
          <div class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Tasa de Éxito</div>
          <div class="text-3xl font-bold tabular-nums" :class="stats.success_rate >= 95 ? 'text-emerald-600' : stats.success_rate >= 80 ? 'text-amber-600' : 'text-red-600'">
            {{ stats.success_rate }}%
          </div>
          <div class="text-xs text-gray-400 mt-1">enviados correctamente</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm dark:bg-gray-800 dark:border-gray-700">
          <div class="text-xs font-medium text-emerald-600 uppercase tracking-wider mb-1">Exitosos</div>
          <div class="text-3xl font-bold text-emerald-600 tabular-nums">{{ stats.sent_count }}</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm dark:bg-gray-800 dark:border-gray-700">
          <div class="text-xs font-medium text-red-600 uppercase tracking-wider mb-1">Fallidos</div>
          <div class="text-3xl font-bold tabular-nums" :class="stats.failed_count > 0 ? 'text-red-600' : 'text-gray-300'">
            {{ stats.failed_count }}
          </div>
        </div>
      </div>

      <!-- Per-template breakdown -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm mb-8 overflow-hidden dark:bg-gray-800 dark:border-gray-700">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
          <h2 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Por Plantilla</h2>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 dark:bg-gray-700/50">
              <tr>
                <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Plantilla</th>
                <th class="text-center px-4 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total</th>
                <th class="text-center px-4 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Exitosos</th>
                <th class="text-center px-4 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Fallidos</th>
                <th class="text-center px-4 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tasa</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50 dark:divide-gray-700">
              <tr v-for="tpl in stats.by_template" :key="tpl.template_key" class="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <td class="px-6 py-3 font-medium text-gray-900 dark:text-gray-100">
                  <code class="text-xs bg-gray-100 dark:bg-gray-700 dark:text-gray-300 px-2 py-0.5 rounded">{{ tpl.template_key }}</code>
                </td>
                <td class="px-4 py-3 text-center text-gray-600 dark:text-gray-300 tabular-nums">{{ tpl.total }}</td>
                <td class="px-4 py-3 text-center text-emerald-600 tabular-nums">{{ tpl.sent }}</td>
                <td class="px-4 py-3 text-center tabular-nums" :class="tpl.failed > 0 ? 'text-red-600 font-medium' : 'text-gray-300'">{{ tpl.failed }}</td>
                <td class="px-4 py-3 text-center">
                  <span class="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
                    :class="tpl.success_rate >= 95 ? 'bg-emerald-50 text-emerald-700' : tpl.success_rate >= 80 ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700'">
                    {{ tpl.success_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="!stats.by_template.length" class="px-6 py-8 text-center text-gray-400 text-sm">
          No hay datos de email en los últimos 30 días.
        </div>
      </div>

      <!-- Daily trend (simple bar chart) -->
      <div v-if="stats.daily_trend.length" class="bg-white rounded-xl border border-gray-100 shadow-sm mb-8 overflow-hidden dark:bg-gray-800 dark:border-gray-700">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
          <h2 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Tendencia Diaria</h2>
        </div>
        <div class="px-6 py-4">
          <div class="flex items-end gap-1 h-32">
            <div
              v-for="day in stats.daily_trend"
              :key="day.date"
              class="flex-1 flex flex-col items-center justify-end h-full group relative"
            >
              <div
                class="w-full rounded-t transition-all"
                :class="day.failed > 0 ? 'bg-red-400' : 'bg-emerald-400'"
                :style="{ height: `${Math.max(4, (day.total / maxDailyTotal) * 100)}%` }"
              />
              <div class="absolute bottom-full mb-1 hidden group-hover:block bg-gray-900 text-white text-[10px] px-2 py-1 rounded whitespace-nowrap z-10">
                {{ day.date }}: {{ day.total }} emails
                <span v-if="day.failed > 0" class="text-red-300">({{ day.failed }} fallidos)</span>
              </div>
            </div>
          </div>
          <div class="flex justify-between mt-2 text-[10px] text-gray-400">
            <span>{{ stats.daily_trend[0]?.date }}</span>
            <span>{{ stats.daily_trend[stats.daily_trend.length - 1]?.date }}</span>
          </div>
        </div>
      </div>

      <!-- Recent failures -->
      <div v-if="stats.recent_failures.length" class="bg-white rounded-xl border border-red-100 shadow-sm overflow-hidden dark:bg-gray-800 dark:border-red-900/50">
        <div class="px-6 py-4 border-b border-red-100 bg-red-50 dark:bg-red-900/20 dark:border-red-900/50">
          <h2 class="text-sm font-semibold text-red-800 dark:text-red-400">Fallos Recientes ({{ stats.recent_failures.length }})</h2>
        </div>
        <div class="divide-y divide-gray-50 dark:divide-gray-700">
          <div v-for="(failure, idx) in stats.recent_failures" :key="idx" class="px-6 py-3 text-sm">
            <div class="flex flex-wrap items-center gap-2 mb-1">
              <code class="text-xs bg-gray-100 dark:bg-gray-700 dark:text-gray-300 px-2 py-0.5 rounded">{{ failure.template_key }}</code>
              <span class="text-gray-400">→</span>
              <span class="text-gray-700 dark:text-gray-300 font-medium">{{ failure.recipient }}</span>
              <span class="text-xs px-1.5 py-0.5 rounded-full font-medium"
                :class="failure.status === 'bounced' ? 'bg-orange-50 text-orange-700' : 'bg-red-50 text-red-700'">
                {{ failure.status }}
              </span>
              <span class="text-xs text-gray-400 ml-auto">{{ formatDate(failure.sent_at) }}</span>
            </div>
            <p v-if="failure.error_message" class="text-xs text-red-500 truncate max-w-full">
              {{ failure.error_message }}
            </p>
          </div>
        </div>
      </div>
    </template>

    <!-- Empty state -->
    <div v-else class="text-center py-16">
      <div class="text-4xl mb-3">📭</div>
      <p class="text-gray-500 text-sm">No se pudieron cargar las estadísticas de email.</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';

const localePath = useLocalePath();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const proposalStore = useProposalStore();

const stats = ref(null);
const isLoading = ref(false);

const maxDailyTotal = computed(() => {
  if (!stats.value?.daily_trend?.length) return 1;
  return Math.max(1, ...stats.value.daily_trend.map(d => d.total));
});

function formatDate(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  return d.toLocaleDateString('es-CO', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

async function loadStats() {
  isLoading.value = true;
  try {
    const result = await proposalStore.fetchEmailDeliverability();
    if (result.success) {
      stats.value = result.data;
    }
  } finally {
    isLoading.value = false;
  }
}

onMounted(() => {
  loadStats();
});
</script>
