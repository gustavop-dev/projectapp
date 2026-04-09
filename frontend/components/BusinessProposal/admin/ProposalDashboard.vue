<template>
  <div>
    <!-- Toggle button + refresh -->
    <div class="flex items-center gap-3 mb-4">
      <button
        class="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
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
      <button
        v-if="isOpen && !loading"
        class="flex items-center gap-1 text-xs text-gray-400 hover:text-emerald-600 transition-colors"
        @click="refreshDashboard"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Actualizar
      </button>
      <span v-if="isOpen && lastRefresh" class="text-[10px] text-gray-300">{{ lastRefreshLabel }}</span>
    </div>

    <Transition name="dashboard-slide">
      <div v-if="isOpen" class="space-y-5 mb-8">
        <!-- Loading -->
        <div v-if="loading" class="text-center py-6 text-gray-400 text-sm">
          Cargando métricas...
        </div>

        <template v-else-if="data">
          <!-- KPI summary cards -->
          <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700">
              <p class="text-xs text-gray-400 uppercase tracking-wider">Total propuestas</p>
              <p class="text-3xl font-light text-gray-900 dark:text-gray-100 mt-1">{{ data.total_proposals }}</p>
            </div>
            <div class="bg-white rounded-xl border border-emerald-100 shadow-sm p-4 dark:bg-gray-800 dark:border-emerald-800">
              <div class="flex items-center gap-1">
                <p class="text-xs text-emerald-600 uppercase tracking-wider">Tasa conversión</p>
                <UiTooltip position="bottom">
                  <template #trigger>
                    <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-emerald-300 hover:text-emerald-500 transition-colors" />
                  </template>
                  {{ tt.conversionRate }}
                </UiTooltip>
              </div>
              <p class="text-3xl font-light text-emerald-700 mt-1">{{ data.conversion_rate }}%</p>
            </div>
            <div class="bg-white rounded-xl border border-blue-100 shadow-sm p-4 dark:bg-gray-800 dark:border-blue-800">
              <div class="flex items-center gap-1">
                <p class="text-xs text-blue-600 uppercase tracking-wider">Tasa revisita</p>
                <UiTooltip position="bottom">
                  <template #trigger>
                    <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-blue-300 hover:text-blue-500 transition-colors" />
                  </template>
                  {{ tt.revisitRate }}
                </UiTooltip>
              </div>
              <p class="text-2xl font-light text-blue-700 mt-1">
                {{ data.pct_revisit != null ? data.pct_revisit + '%' : '—' }}
              </p>
              <p class="text-[10px] text-gray-400 mt-0.5">Clientes que volvieron</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700">
              <div class="flex items-center gap-1">
                <p class="text-xs text-gray-400 uppercase tracking-wider">Avg tiempo 1ra vista</p>
                <UiTooltip position="bottom">
                  <template #trigger>
                    <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-gray-300 hover:text-gray-500 transition-colors" />
                  </template>
                  {{ tt.avgTimeToFirstView }}
                </UiTooltip>
              </div>
              <p class="text-2xl font-light text-gray-900 dark:text-gray-100 mt-1">
                {{ data.avg_time_to_first_view_hours != null ? data.avg_time_to_first_view_hours + 'h' : '—' }}
              </p>
            </div>
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700">
              <div class="flex items-center gap-1">
                <p class="text-xs text-gray-400 uppercase tracking-wider">Avg tiempo respuesta</p>
                <UiTooltip position="bottom">
                  <template #trigger>
                    <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-gray-300 hover:text-gray-500 transition-colors" />
                  </template>
                  {{ tt.avgTimeToResponse }}
                </UiTooltip>
              </div>
              <p class="text-2xl font-light text-gray-900 dark:text-gray-100 mt-1">
                {{ data.avg_time_to_response_hours != null ? data.avg_time_to_response_hours + 'h' : '—' }}
              </p>
            </div>
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700">
              <div class="flex items-center gap-1">
                <p class="text-xs text-gray-400 uppercase tracking-wider">Avg valor aceptadas</p>
                <UiTooltip position="bottom">
                  <template #trigger>
                    <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-gray-300 hover:text-gray-500 transition-colors" />
                  </template>
                  {{ tt.avgAcceptedValue }}
                </UiTooltip>
              </div>
              <p class="text-xl font-light text-gray-900 dark:text-gray-100 mt-1">
                ${{ formatNumber(data.avg_value_by_status?.accepted || 0) }}
              </p>
            </div>
          </div>

          <!-- Status distribution + Rejection reasons side by side -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <!-- Status distribution -->
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700">
              <div class="flex items-center gap-1.5 mb-3">
                <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Distribución por estado</h3>
                <UiTooltip position="right">
                  <template #trigger>
                    <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors" />
                  </template>
                  {{ tt.statusDistribution }}
                </UiTooltip>
              </div>
              <div class="space-y-2">
                <div v-for="(count, statusKey) in data.by_status" :key="statusKey" class="flex items-center gap-3">
                  <span class="text-xs w-16 text-gray-500 dark:text-gray-400 capitalize">{{ statusKey }}</span>
                  <div class="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-3">
                    <div
                      class="h-3 rounded-full transition-all"
                      :class="statusBarColor(statusKey)"
                      :style="{ width: statusPercent(count) + '%' }"
                    />
                  </div>
                  <span class="text-xs text-gray-600 dark:text-gray-300 w-8 text-right font-medium">{{ count }}</span>
                </div>
              </div>
            </div>

            <!-- Top rejection reasons -->
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700">
              <div class="flex items-center gap-1.5 mb-3">
                <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Top motivos de rechazo</h3>
                <UiTooltip position="right">
                  <template #trigger>
                    <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors" />
                  </template>
                  {{ tt.topRejectionReasons }}
                </UiTooltip>
              </div>
              <div v-if="data.top_rejection_reasons?.length" class="space-y-2">
                <div v-for="reason in data.top_rejection_reasons" :key="reason.rejection_reason" class="flex items-center gap-3">
                  <span class="text-xs text-gray-600 dark:text-gray-300 flex-1 truncate">{{ reason.rejection_reason }}</span>
                  <div class="w-20 bg-gray-100 dark:bg-gray-700 rounded-full h-2">
                    <div
                      class="h-2 rounded-full bg-red-400 transition-all"
                      :style="{ width: rejectionPercent(reason.count) + '%' }"
                    />
                  </div>
                  <span class="text-xs text-gray-500 dark:text-gray-400 w-6 text-right">{{ reason.count }}</span>
                </div>
              </div>
              <p v-else class="text-xs text-gray-400">Sin rechazos registrados.</p>
            </div>
          </div>

          <!-- Monthly trend -->
          <div v-if="data.monthly_trend?.length" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700">
            <div class="flex items-center gap-1.5 mb-3">
              <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Tendencia mensual (últimos 6 meses)</h3>
              <UiTooltip position="right">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors" />
                </template>
                {{ tt.monthlyTrend }}
              </UiTooltip>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-left text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    <th class="px-3 py-2">Mes</th>
                    <th class="px-3 py-2 text-center">Creadas</th>
                    <th class="px-3 py-2 text-center">Enviadas</th>
                    <th class="px-3 py-2 text-center">Aceptadas</th>
                    <th class="px-3 py-2 text-center">Rechazadas</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-50 dark:divide-gray-700">
                  <tr v-for="row in data.monthly_trend" :key="row.month" class="hover:bg-gray-50/50 dark:hover:bg-gray-700/50">
                    <td class="px-3 py-2 text-gray-700 dark:text-gray-300">{{ formatMonth(row.month) }}</td>
                    <td class="px-3 py-2 text-center text-gray-600 dark:text-gray-400">{{ row.created }}</td>
                    <td class="px-3 py-2 text-center text-blue-600">{{ row.sent }}</td>
                    <td class="px-3 py-2 text-center text-emerald-600 font-medium">{{ row.accepted }}</td>
                    <td class="px-3 py-2 text-center text-red-500">{{ row.rejected }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Avg value by status -->
          <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700">
            <div class="flex items-center gap-1.5 mb-3">
              <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Valor promedio por estado</h3>
              <UiTooltip position="right">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors" />
                </template>
                {{ tt.avgValueByStatus }}
              </UiTooltip>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div v-for="(val, key) in data.avg_value_by_status" :key="key" class="text-center p-3 rounded-lg bg-gray-50 dark:bg-gray-700">
                <p class="text-xs text-gray-400 uppercase capitalize">{{ key }}</p>
                <p class="text-sm font-medium text-gray-900 dark:text-gray-100 mt-1">${{ formatNumber(val) }}</p>
              </div>
            </div>
          </div>

          <!-- Win rate by project type + market type -->
          <div v-if="data.win_rate_by_project_type?.length || data.win_rate_by_market_type?.length" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div v-if="data.win_rate_by_project_type?.length" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700">
              <div class="flex items-center gap-1.5 mb-3">
                <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Win rate por tipo de proyecto</h3>
                <UiTooltip position="right">
                  <template #trigger>
                    <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors" />
                  </template>
                  {{ tt.winRateByProjectType }}
                </UiTooltip>
              </div>
              <div class="space-y-2">
                <div v-for="item in data.win_rate_by_project_type" :key="item.type" class="flex items-center gap-3">
                  <span class="text-xs w-20 text-gray-500 dark:text-gray-400 capitalize truncate">{{ projectTypeLabel(item.type) }}</span>
                  <div class="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-3">
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
            <div v-if="data.win_rate_by_market_type?.length" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700">
              <div class="flex items-center gap-1.5 mb-3">
                <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Win rate por tipo de mercado</h3>
                <UiTooltip position="right">
                  <template #trigger>
                    <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors" />
                  </template>
                  {{ tt.winRateByMarketType }}
                </UiTooltip>
              </div>
              <div class="space-y-2">
                <div v-for="item in data.win_rate_by_market_type" :key="item.type" class="flex items-center gap-3">
                  <span class="text-xs w-20 text-gray-500 dark:text-gray-400 capitalize truncate">{{ marketTypeLabel(item.type) }}</span>
                  <div class="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-3">
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

          <!-- Win rate by predominant view mode (tracking) -->
          <div
            v-if="data.win_rate_by_view_mode && Object.keys(data.win_rate_by_view_mode).length"
            class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700"
          >
            <div class="flex items-center gap-1.5 mb-1">
              <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Win rate por modo de vista</h3>
              <UiTooltip position="right">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors" />
                </template>
                {{ tt.winRateByViewMode }}
              </UiTooltip>
            </div>
            <p class="text-xs text-gray-400 mb-3">
              Por propuesta cerrada se toma el modo con más eventos de tracking (ejecutiva, completa o técnica).
            </p>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div
                v-for="mode in ['executive', 'detailed', 'technical']"
                :key="mode"
                class="rounded-lg border p-3"
                :class="mode === 'executive'
                  ? 'border-purple-100 bg-purple-50/40 dark:border-purple-900/40 dark:bg-purple-900/15'
                  : mode === 'detailed'
                    ? 'border-blue-100 bg-blue-50/40 dark:border-blue-900/40 dark:bg-blue-900/15'
                    : 'border-teal-100 bg-teal-50/40 dark:border-teal-900/40 dark:bg-teal-900/15'"
              >
                <p class="text-[10px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  {{ viewModeDashboardLabel(mode) }}
                </p>
                <p class="text-2xl font-light text-gray-900 dark:text-gray-100 mt-1">
                  {{ data.win_rate_by_view_mode[mode]?.win_rate != null ? data.win_rate_by_view_mode[mode].win_rate + '%' : '—' }}
                </p>
                <p class="text-[11px] text-gray-500 dark:text-gray-400 mt-1">
                  {{ data.win_rate_by_view_mode[mode]?.accepted ?? 0 }} aceptadas / {{ data.win_rate_by_view_mode[mode]?.total ?? 0 }} cerradas
                </p>
              </div>
            </div>
          </div>

          <!-- Win rate by combination -->
          <div v-if="data.win_rate_by_combination?.length" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700">
            <div class="flex items-center gap-1.5 mb-3">
              <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Mejor combinación proyecto × mercado</h3>
              <UiTooltip position="right">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors" />
                </template>
                {{ tt.bestCombination }}
              </UiTooltip>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-left text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    <th class="px-3 py-2">Proyecto</th>
                    <th class="px-3 py-2">Mercado</th>
                    <th class="px-3 py-2 text-center">Win Rate</th>
                    <th class="px-3 py-2 text-center">Aceptadas / Total</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-50 dark:divide-gray-700">
                  <tr v-for="(row, idx) in data.win_rate_by_combination" :key="idx" class="hover:bg-gray-50/50 dark:hover:bg-gray-700/50">
                    <td class="px-3 py-2 text-gray-700 capitalize">{{ projectTypeLabel(row.project_type) }}</td>
                    <td class="px-3 py-2 text-gray-700 capitalize">{{ marketTypeLabel(row.market_type) }}</td>
                    <td class="px-3 py-2 text-center font-medium" :class="idx === 0 ? 'text-emerald-600' : 'text-gray-600'">{{ row.win_rate }}%</td>
                    <td class="px-3 py-2 text-center text-gray-500">{{ row.accepted }} / {{ row.total }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <!-- Engagement / Value insight + Calculator metrics -->
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div v-if="data.engagement_value_insight" class="bg-white rounded-xl border border-emerald-100 shadow-sm p-4 dark:bg-gray-800 dark:border-emerald-800">
              <div class="flex items-center gap-1.5 mb-2">
                <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Engagement vs Valor de cierre</h3>
                <UiTooltip position="right">
                  <template #trigger>
                    <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors" />
                  </template>
                  {{ tt.engagementVsValue }}
                </UiTooltip>
              </div>
              <div class="space-y-1.5">
                <div class="flex justify-between text-xs">
                  <span class="text-gray-500">Alto engagement ({{ data.engagement_value_insight.high_count }})</span>
                  <span class="font-bold text-emerald-700">${{ formatNumber(data.engagement_value_insight.avg_high_engagement_value) }}</span>
                </div>
                <div class="flex justify-between text-xs">
                  <span class="text-gray-500">Bajo engagement ({{ data.engagement_value_insight.low_count }})</span>
                  <span class="font-medium text-gray-600">${{ formatNumber(data.engagement_value_insight.avg_low_engagement_value) }}</span>
                </div>
                <div v-if="data.engagement_value_insight.difference > 0" class="mt-2 text-[11px] text-emerald-600 font-semibold bg-emerald-50 rounded-lg px-3 py-1.5">
                  Clientes de alto engagement cierran ${{ formatNumber(data.engagement_value_insight.difference) }} más alto en promedio
                </div>
              </div>
            </div>

            <div v-if="data.calc_abandonment_rate != null" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700">
              <div class="flex items-center gap-1.5 mb-2">
                <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Calculadora</h3>
                <UiTooltip position="right">
                  <template #trigger>
                    <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors" />
                  </template>
                  {{ tt.calculator }}
                </UiTooltip>
              </div>
              <div class="flex items-baseline gap-2">
                <span class="text-2xl font-light" :class="data.calc_abandonment_rate > 50 ? 'text-red-600' : 'text-gray-900'">{{ data.calc_abandonment_rate }}%</span>
                <span class="text-xs text-gray-400">abandono</span>
              </div>
              <p class="text-[10px] text-gray-400 mt-1">Abrieron el calculador pero no confirmaron</p>
            </div>

            <div v-if="data.top_dropped_modules?.length" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 dark:bg-gray-800 dark:border-gray-700">
              <div class="flex items-center gap-1.5 mb-2">
                <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Módulos más descartados</h3>
                <UiTooltip position="right">
                  <template #trigger>
                    <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors" />
                  </template>
                  {{ tt.droppedModules }}
                </UiTooltip>
              </div>
              <div class="space-y-1">
                <div v-for="mod in data.top_dropped_modules.slice(0, 5)" :key="mod.module_id" class="flex items-center justify-between text-xs">
                  <span class="text-gray-600 truncate">{{ mod.module_id }}</span>
                  <span class="text-red-500 font-medium">{{ mod.drop_count }}×</span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, ref, watch, onBeforeUnmount } from 'vue';
import { QuestionMarkCircleIcon } from '@heroicons/vue/24/outline';

const { dashboard: tt } = useTooltipTexts();

const AUTO_REFRESH_MS = 60_000;

const proposalStore = useProposalStore();
const isOpen = ref(false);
const loading = ref(false);
const refreshing = ref(false);
const data = ref(null);
const lastRefresh = ref(null);
let fetched = false;
let autoRefreshTimer = null;

const lastRefreshLabel = computed(() => {
  if (!lastRefresh.value) return '';
  const secs = Math.round((Date.now() - lastRefresh.value) / 1000);
  if (secs < 10) return 'justo ahora';
  if (secs < 60) return `hace ${secs}s`;
  return `hace ${Math.round(secs / 60)}m`;
});

async function fetchDashboard() {
  if (fetched) return;
  loading.value = true;
  const result = await proposalStore.fetchProposalDashboard();
  if (result.success) {
    data.value = result.data;
    fetched = true;
    lastRefresh.value = Date.now();
  }
  loading.value = false;
}

async function refreshDashboard() {
  refreshing.value = true;
  const result = await proposalStore.fetchProposalDashboard();
  if (result.success) {
    data.value = result.data;
    lastRefresh.value = Date.now();
  }
  refreshing.value = false;
}

function startAutoRefresh() {
  stopAutoRefresh();
  autoRefreshTimer = setInterval(() => {
    if (isOpen.value && !loading.value && !refreshing.value) {
      refreshDashboard();
    }
  }, AUTO_REFRESH_MS);
}

function stopAutoRefresh() {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer);
    autoRefreshTimer = null;
  }
}

watch(isOpen, (val) => {
  if (val && !fetched) fetchDashboard();
  if (val) startAutoRefresh();
  else stopAutoRefresh();
}, { immediate: true });

onBeforeUnmount(() => stopAutoRefresh());

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

function viewModeDashboardLabel(mode) {
  const map = { executive: 'Ejecutiva', detailed: 'Completa', technical: 'Técnica' };
  return map[mode] || mode;
}

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
