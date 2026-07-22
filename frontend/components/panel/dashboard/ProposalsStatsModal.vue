<template>
  <StatsModal
    :open="open"
    title="Estadísticas de propuestas"
    subtitle="Tendencia, embudo comercial, valor por etapa y conversión."
    :tabs="TABS"
    v-model="activeTab"
    :loading="loading"
    @close="emit('close')"
  >
    <template #default="{ activeTab: tab }">
      <div v-if="tab === 'trend'" class="space-y-5">
        <StatsSummaryStrip :items="overviewStrip" />
        <DashboardTrendChart :trend="dashboard?.monthly_trend || []" />
      </div>

      <div v-else-if="tab === 'funnel'" class="space-y-5">
        <StatsSummaryStrip :items="overviewStrip" />
        <p class="text-xs text-text-muted">
          Propuestas por estado a lo largo del ciclo comercial.
        </p>
        <StatsBarChart
          :series="[{ name: 'Propuestas', data: funnel.map((row) => row.count) }]"
          :categories="funnel.map((row) => row.label)"
          horizontal
          value-format="number"
          :colors="[palette.measures[0]]"
          :height="Math.max(240, funnel.length * 40)"
          empty-title="Sin propuestas registradas"
        />
      </div>

      <div v-else-if="tab === 'value'" class="space-y-5">
        <StatsSummaryStrip :items="valueStrip" />
        <p class="text-xs text-text-muted">
          Valor promedio de la propuesta según la etapa que alcanzó.
        </p>
        <StatsBarChart
          :series="[{ name: 'Valor promedio', data: valueByStage.map((row) => row.value) }]"
          :categories="valueByStage.map((row) => row.label)"
          horizontal
          :colors="[palette.measures[1]]"
          :height="Math.max(220, valueByStage.length * 44)"
          empty-title="Sin valores registrados por etapa"
        />
      </div>

      <div v-else-if="tab === 'conversion'" class="space-y-5">
        <StatsSummaryStrip :items="overviewStrip" />
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 items-center">
          <StatsRadialChart
            :value="conversionRate"
            label="Tasa de cierre"
            :tone="conversionRate !== null && conversionRate >= 50 ? 'success' : 'warning'"
          />
          <div class="lg:col-span-2">
            <p class="text-xs text-text-muted mb-2">
              Conversión mensual (aceptadas sobre terminales del mes; meses sin
              cierres no puntúan).
            </p>
            <StatsLineChart
              :series="[{ name: '% conversión', data: monthlyConversion }]"
              :categories="trendCategories"
              value-format="percent"
              :colors="[palette.measures[1]]"
              :height="230"
              empty-title="Sin cierres en los últimos meses"
            />
          </div>
        </div>
      </div>
    </template>
  </StatsModal>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import StatsModal from '~/components/stats/StatsModal.vue';
import StatsSummaryStrip from '~/components/stats/StatsSummaryStrip.vue';
import StatsBarChart from '~/components/stats/charts/StatsBarChart.vue';
import StatsLineChart from '~/components/stats/charts/StatsLineChart.vue';
import StatsRadialChart from '~/components/stats/charts/StatsRadialChart.vue';
import DashboardTrendChart from '~/components/panel/dashboard/DashboardTrendChart.vue';
import { useChartTheme } from '~/composables/useChartTheme';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useProposalStore } from '~/stores/proposals';
import { formatMoney } from '~/utils/formatMoney';
import { FUNNEL_ORDER, statusLabel } from '~/utils/proposalStatus';

/**
 * Proposals deep-dive over GET proposals/dashboard/. The endpoint is
 * heavy (per-proposal loops), so it is fetched once per modal lifetime
 * on the first open and cached locally — never on dashboard load.
 */
const props = defineProps({
  open: { type: Boolean, default: false },
});

const emit = defineEmits(['close']);

const TABS = [
  { id: 'trend', label: 'Tendencia' },
  { id: 'funnel', label: 'Embudo' },
  { id: 'value', label: 'Valor por etapa' },
  { id: 'conversion', label: 'Conversión' },
];

const activeTab = ref('trend');

const { palette } = useChartTheme();
const proposalStore = useProposalStore();
const notify = usePanelNotify();

const dashboard = ref(null);
const loading = ref(false);

watch(
  () => props.open,
  async (open) => {
    if (!open || dashboard.value || loading.value) return;
    loading.value = true;
    const result = await proposalStore.fetchProposalDashboard();
    loading.value = false;
    if (result.success) {
      dashboard.value = result.data;
    } else {
      notify.error({ title: 'No se pudieron cargar las estadísticas de propuestas' });
    }
  },
  { immediate: true },
);

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

const conversionRate = computed(() => {
  const rate = dashboard.value?.conversion_rate;
  return rate === null || rate === undefined ? null : Number(rate);
});

const overviewStrip = computed(() => [
  { label: 'Total propuestas', value: String(dashboard.value?.total_proposals ?? 0) },
  {
    label: 'Pipeline activo',
    value: money(dashboard.value?.pipeline_value),
    sub: `${dashboard.value?.pipeline_count ?? 0} en curso`,
    tone: 'brand',
  },
  {
    label: 'Tasa de cierre',
    value: conversionRate.value === null ? '—' : `${conversionRate.value}%`,
    tone: conversionRate.value !== null && conversionRate.value >= 50 ? 'success' : 'warning',
  },
]);

const funnel = computed(() => {
  const byStatus = dashboard.value?.by_status || {};
  return FUNNEL_ORDER.map((status) => ({
    status,
    label: statusLabel(status),
    count: Number(byStatus[status]) || 0,
  }));
});

const valueByStage = computed(() => {
  const byStage = dashboard.value?.avg_value_by_status || {};
  return Object.entries(byStage)
    .map(([status, value]) => ({
      status,
      label: statusLabel(status),
      value: Number(value) || 0,
    }))
    .filter((row) => row.value > 0)
    .sort((a, b) => b.value - a.value);
});

const valueStrip = computed(() => [
  ...overviewStrip.value,
  {
    label: 'Mejor etapa',
    value: valueByStage.value.length ? money(valueByStage.value[0].value) : '—',
    sub: valueByStage.value[0]?.label || '',
  },
]);

const trendCategories = computed(() =>
  (dashboard.value?.monthly_trend || []).map((row) => {
    if (!row.month) return '';
    const parsed = new Date(row.month);
    return Number.isNaN(parsed.getTime())
      ? ''
      : parsed.toLocaleDateString('es-CO', { month: 'short' });
  }),
);

const monthlyConversion = computed(() =>
  (dashboard.value?.monthly_trend || []).map((row) => {
    const terminal = (Number(row.accepted) || 0) + (Number(row.rejected) || 0);
    if (terminal <= 0) return null;
    return Math.round(((Number(row.accepted) || 0) / terminal) * 1000) / 10;
  }),
);
</script>
