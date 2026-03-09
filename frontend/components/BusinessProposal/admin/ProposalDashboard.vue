<template>
  <div>
    <!-- Toggle button -->
    <button
      class="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors mb-4"
      @click="isOpen = !isOpen"
    >
      <svg
        class="w-4 h-4 transition-transform" :class="{ 'rotate-180': isOpen }"
        fill="none" stroke="currentColor" viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
      {{ isOpen ? 'Ocultar Dashboard' : 'Mostrar Dashboard KPI' }}
    </button>

    <Transition name="dashboard-slide">
      <div v-if="isOpen" class="space-y-5 mb-8">
        <!-- Loading -->
        <div v-if="loading" class="text-center py-6 text-gray-400 text-sm">
          Cargando métricas...
        </div>

        <template v-else-if="data">
          <!-- KPI summary cards -->
          <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <p class="text-xs text-gray-400 uppercase tracking-wider">Total propuestas</p>
              <p class="text-3xl font-light text-gray-900 mt-1">{{ data.total_proposals }}</p>
            </div>
            <div class="bg-white rounded-xl border border-emerald-100 shadow-sm p-4">
              <p class="text-xs text-emerald-600 uppercase tracking-wider">Tasa conversión</p>
              <p class="text-3xl font-light text-emerald-700 mt-1">{{ data.conversion_rate }}%</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <p class="text-xs text-gray-400 uppercase tracking-wider">Avg tiempo 1ra vista</p>
              <p class="text-2xl font-light text-gray-900 mt-1">
                {{ data.avg_time_to_first_view_hours != null ? data.avg_time_to_first_view_hours + 'h' : '—' }}
              </p>
            </div>
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <p class="text-xs text-gray-400 uppercase tracking-wider">Avg tiempo respuesta</p>
              <p class="text-2xl font-light text-gray-900 mt-1">
                {{ data.avg_time_to_response_hours != null ? data.avg_time_to_response_hours + 'h' : '—' }}
              </p>
            </div>
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <p class="text-xs text-gray-400 uppercase tracking-wider">Avg valor aceptadas</p>
              <p class="text-xl font-light text-gray-900 mt-1">
                ${{ formatNumber(data.avg_value_by_status?.accepted || 0) }}
              </p>
            </div>
          </div>

          <!-- Status distribution + Rejection reasons side by side -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <!-- Status distribution -->
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <h3 class="text-sm font-medium text-gray-900 mb-3">Distribución por estado</h3>
              <div class="space-y-2">
                <div v-for="(count, statusKey) in data.by_status" :key="statusKey" class="flex items-center gap-3">
                  <span class="text-xs w-16 text-gray-500 capitalize">{{ statusKey }}</span>
                  <div class="flex-1 bg-gray-100 rounded-full h-3">
                    <div
                      class="h-3 rounded-full transition-all"
                      :class="statusBarColor(statusKey)"
                      :style="{ width: statusPercent(count) + '%' }"
                    />
                  </div>
                  <span class="text-xs text-gray-600 w-8 text-right font-medium">{{ count }}</span>
                </div>
              </div>
            </div>

            <!-- Top rejection reasons -->
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <h3 class="text-sm font-medium text-gray-900 mb-3">Top motivos de rechazo</h3>
              <div v-if="data.top_rejection_reasons?.length" class="space-y-2">
                <div v-for="reason in data.top_rejection_reasons" :key="reason.rejection_reason" class="flex items-center gap-3">
                  <span class="text-xs text-gray-600 flex-1 truncate">{{ reason.rejection_reason }}</span>
                  <div class="w-20 bg-gray-100 rounded-full h-2">
                    <div
                      class="h-2 rounded-full bg-red-400 transition-all"
                      :style="{ width: rejectionPercent(reason.count) + '%' }"
                    />
                  </div>
                  <span class="text-xs text-gray-500 w-6 text-right">{{ reason.count }}</span>
                </div>
              </div>
              <p v-else class="text-xs text-gray-400">Sin rechazos registrados.</p>
            </div>
          </div>

          <!-- Monthly trend -->
          <div v-if="data.monthly_trend?.length" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="text-sm font-medium text-gray-900 mb-3">Tendencia mensual (últimos 6 meses)</h3>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-left text-xs text-gray-500 uppercase tracking-wider">
                    <th class="px-3 py-2">Mes</th>
                    <th class="px-3 py-2 text-center">Creadas</th>
                    <th class="px-3 py-2 text-center">Enviadas</th>
                    <th class="px-3 py-2 text-center">Aceptadas</th>
                    <th class="px-3 py-2 text-center">Rechazadas</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-50">
                  <tr v-for="row in data.monthly_trend" :key="row.month" class="hover:bg-gray-50/50">
                    <td class="px-3 py-2 text-gray-700">{{ formatMonth(row.month) }}</td>
                    <td class="px-3 py-2 text-center text-gray-600">{{ row.created }}</td>
                    <td class="px-3 py-2 text-center text-blue-600">{{ row.sent }}</td>
                    <td class="px-3 py-2 text-center text-emerald-600 font-medium">{{ row.accepted }}</td>
                    <td class="px-3 py-2 text-center text-red-500">{{ row.rejected }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Avg value by status -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="text-sm font-medium text-gray-900 mb-3">Valor promedio por estado</h3>
            <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div v-for="(val, key) in data.avg_value_by_status" :key="key" class="text-center p-3 rounded-lg bg-gray-50">
                <p class="text-xs text-gray-400 uppercase capitalize">{{ key }}</p>
                <p class="text-sm font-medium text-gray-900 mt-1">${{ formatNumber(val) }}</p>
              </div>
            </div>
          </div>

          <!-- Win rate by project type + market type -->
          <div v-if="data.win_rate_by_project_type?.length || data.win_rate_by_market_type?.length" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div v-if="data.win_rate_by_project_type?.length" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <h3 class="text-sm font-medium text-gray-900 mb-3">Win rate por tipo de proyecto</h3>
              <div class="space-y-2">
                <div v-for="item in data.win_rate_by_project_type" :key="item.type" class="flex items-center gap-3">
                  <span class="text-xs w-20 text-gray-500 capitalize truncate">{{ projectTypeLabel(item.type) }}</span>
                  <div class="flex-1 bg-gray-100 rounded-full h-3">
                    <div
                      class="h-3 rounded-full transition-all"
                      :class="item.win_rate >= bestProjectWinRate ? 'bg-emerald-500' : 'bg-emerald-300'"
                      :style="{ width: Math.max(4, item.win_rate) + '%' }"
                    />
                  </div>
                  <span class="text-xs text-gray-600 w-16 text-right font-medium">{{ item.win_rate }}% <span class="text-gray-400">({{ item.accepted }}/{{ item.total }})</span></span>
                </div>
              </div>
            </div>
            <div v-if="data.win_rate_by_market_type?.length" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <h3 class="text-sm font-medium text-gray-900 mb-3">Win rate por tipo de mercado</h3>
              <div class="space-y-2">
                <div v-for="item in data.win_rate_by_market_type" :key="item.type" class="flex items-center gap-3">
                  <span class="text-xs w-20 text-gray-500 capitalize truncate">{{ marketTypeLabel(item.type) }}</span>
                  <div class="flex-1 bg-gray-100 rounded-full h-3">
                    <div
                      class="h-3 rounded-full transition-all"
                      :class="item.win_rate >= bestMarketWinRate ? 'bg-blue-500' : 'bg-blue-300'"
                      :style="{ width: Math.max(4, item.win_rate) + '%' }"
                    />
                  </div>
                  <span class="text-xs text-gray-600 w-16 text-right font-medium">{{ item.win_rate }}% <span class="text-gray-400">({{ item.accepted }}/{{ item.total }})</span></span>
                </div>
              </div>
            </div>
          </div>

          <!-- Win rate by combination -->
          <div v-if="data.win_rate_by_combination?.length" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 class="text-sm font-medium text-gray-900 mb-3">Mejor combinación proyecto × mercado</h3>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-left text-xs text-gray-500 uppercase tracking-wider">
                    <th class="px-3 py-2">Proyecto</th>
                    <th class="px-3 py-2">Mercado</th>
                    <th class="px-3 py-2 text-center">Win Rate</th>
                    <th class="px-3 py-2 text-center">Aceptadas / Total</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-50">
                  <tr v-for="(row, idx) in data.win_rate_by_combination" :key="idx" class="hover:bg-gray-50/50">
                    <td class="px-3 py-2 text-gray-700 capitalize">{{ projectTypeLabel(row.project_type) }}</td>
                    <td class="px-3 py-2 text-gray-700 capitalize">{{ marketTypeLabel(row.market_type) }}</td>
                    <td class="px-3 py-2 text-center font-medium" :class="idx === 0 ? 'text-emerald-600' : 'text-gray-600'">{{ row.win_rate }}%</td>
                    <td class="px-3 py-2 text-center text-gray-500">{{ row.accepted }} / {{ row.total }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';

const proposalStore = useProposalStore();
const isOpen = ref(true);
const loading = ref(false);
const data = ref(null);
let fetched = false;

async function fetchDashboard() {
  if (fetched) return;
  loading.value = true;
  const result = await proposalStore.fetchProposalDashboard();
  if (result.success) {
    data.value = result.data;
    fetched = true;
  }
  loading.value = false;
}

watch(isOpen, (val) => {
  if (val && !fetched) fetchDashboard();
}, { immediate: true });

function formatNumber(n) {
  if (!n) return '0';
  return Number(n).toLocaleString('es-CO', { maximumFractionDigits: 0 });
}

function formatMonth(isoStr) {
  if (!isoStr) return '—';
  const d = new Date(isoStr);
  return d.toLocaleDateString('es-CO', { month: 'short', year: 'numeric' });
}

function statusPercent(count) {
  const total = data.value?.total_proposals || 1;
  return Math.max(4, Math.round((count / total) * 100));
}

function statusBarColor(status) {
  const map = {
    draft: 'bg-gray-300', sent: 'bg-blue-400', viewed: 'bg-green-400',
    accepted: 'bg-emerald-500', rejected: 'bg-red-400', expired: 'bg-yellow-400',
  };
  return map[status] || 'bg-gray-300';
}

function rejectionPercent(count) {
  const max = data.value?.top_rejection_reasons?.[0]?.count || 1;
  return Math.max(8, Math.round((count / max) * 100));
}

const projectTypeLabels = {
  website: 'Sitio Web', ecommerce: 'E-commerce', webapp: 'App Web',
  landing: 'Landing', redesign: 'Rediseño', other: 'Otro',
};
const marketTypeLabels = {
  b2b: 'B2B', b2c: 'B2C', saas: 'SaaS', retail: 'Retail',
  services: 'Servicios', health: 'Salud', education: 'Educación',
  real_estate: 'Inmobiliaria', other: 'Otro',
};
function projectTypeLabel(t) { return projectTypeLabels[t] || t; }
function marketTypeLabel(t) { return marketTypeLabels[t] || t; }

const bestProjectWinRate = computed(() => {
  const rates = (data.value?.win_rate_by_project_type || []).map(i => i.win_rate);
  return rates.length ? Math.max(...rates) : 0;
});
const bestMarketWinRate = computed(() => {
  const rates = (data.value?.win_rate_by_market_type || []).map(i => i.win_rate);
  return rates.length ? Math.max(...rates) : 0;
});
</script>

<style scoped>
.dashboard-slide-enter-active {
  transition: all 0.3s ease;
}
.dashboard-slide-leave-active {
  transition: all 0.2s ease;
}
.dashboard-slide-enter-from,
.dashboard-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
