<template>
  <StatsModal
    :open="open"
    :title="`Estadísticas financieras ${finance?.year || ''}`"
    subtitle="Evolución del año, utilidad mensual y compromisos."
    :tabs="TABS"
    v-model="activeTab"
    @close="emit('close')"
  >
    <template #default="{ activeTab: tab }">
      <div v-if="tab === 'evolution'" class="space-y-5">
        <StatsSummaryStrip :items="evolutionStrip" />
        <StatsLineChart
          :series="evolution.series"
          :categories="evolution.categories"
          area
        />
      </div>

      <div v-else-if="tab === 'utility'" class="space-y-5">
        <StatsSummaryStrip :items="utilityStrip" />
        <StatsBarChart
          :series="[{ name: 'Utilidad líquida', data: monthlyUtility }]"
          :categories="evolution.categories"
          :colors="[palette.measures[1]]"
        />
      </div>

      <div v-else-if="tab === 'debt'" class="space-y-5">
        <StatsSummaryStrip :items="debtStrip" />
        <div class="max-w-xs mx-auto">
          <StatsRadialChart
            :value="utilizationPct"
            label="Cupo utilizado"
            :tone="usageTone"
            empty-title="Registra el cupo de las tarjetas para medir el uso"
          />
        </div>
      </div>
    </template>
  </StatsModal>
</template>

<script setup>
import { computed, ref } from 'vue';
import StatsModal from '~/components/stats/StatsModal.vue';
import StatsSummaryStrip from '~/components/stats/StatsSummaryStrip.vue';
import StatsLineChart from '~/components/stats/charts/StatsLineChart.vue';
import StatsBarChart from '~/components/stats/charts/StatsBarChart.vue';
import StatsRadialChart from '~/components/stats/charts/StatsRadialChart.vue';
import { useChartTheme } from '~/composables/useChartTheme';
import { monthlySeries } from '~/utils/accountingCharts';
import { formatMoney } from '~/utils/formatMoney';

/** Finance deep-dive over the panel dashboard finance block (superuser). */
const props = defineProps({
  open: { type: Boolean, default: false },
  finance: { type: Object, default: null },
});

const emit = defineEmits(['close']);

const TABS = [
  { id: 'evolution', label: 'Evolución' },
  { id: 'utility', label: 'Utilidad' },
  { id: 'debt', label: 'Deuda y compromisos' },
];

const activeTab = ref('evolution');

const { palette } = useChartTheme();

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

function toneBySign(value) {
  return Number(value) < 0 ? 'danger' : 'success';
}

const monthly = computed(() => props.finance?.monthly || []);

const evolution = computed(() => monthlySeries(monthly.value));

const monthlyUtility = computed(() =>
  monthly.value.map((row) => Number(row.utility) || 0),
);

const evolutionStrip = computed(() => [
  { label: 'Esperado año', value: money(props.finance?.expected_total) },
  { label: 'Líquido año', value: money(props.finance?.liquid_total), tone: 'success' },
  { label: 'Gastos año', value: money(props.finance?.expenses_total), tone: 'danger' },
]);

const marginPct = computed(() => {
  const liquid = Number(props.finance?.liquid_total);
  if (!liquid || liquid <= 0) return null;
  return Math.round((Number(props.finance?.liquid_utility) / liquid) * 1000) / 10;
});

const utilityStrip = computed(() => [
  {
    label: 'Utilidad líquida',
    value: money(props.finance?.liquid_utility),
    tone: toneBySign(props.finance?.liquid_utility),
  },
  {
    label: 'Utilidad esperada',
    value: money(props.finance?.expected_utility),
    tone: toneBySign(props.finance?.expected_utility),
  },
  {
    label: 'Margen líquido',
    value: marginPct.value === null ? '—' : `${marginPct.value}%`,
    tone: marginPct.value !== null && marginPct.value < 0 ? 'danger' : 'success',
  },
]);

const utilizationPct = computed(() => {
  const pct = props.finance?.card_debt?.utilization_pct;
  return pct === null || pct === undefined ? null : Number(pct);
});

const usageTone = computed(() => {
  if (utilizationPct.value === null) return 'brand';
  if (utilizationPct.value >= 85) return 'danger';
  if (utilizationPct.value >= 60) return 'warning';
  return 'success';
});

const debtStrip = computed(() => [
  {
    label: 'Deuda tarjetas',
    value: money(props.finance?.card_debt?.total),
    tone: 'danger',
  },
  { label: 'Cupo total', value: money(props.finance?.card_debt?.credit_limit_total) },
  {
    label: 'Por cobrar este mes',
    value: money(props.finance?.expected_current_month?.total),
    sub: props.finance?.expected_current_month?.label || '',
    tone: 'warning',
  },
  { label: 'Recurrentes/mes', value: money(props.finance?.recurring_monthly_cost) },
  {
    label: 'Bolsillo',
    value: money(props.finance?.pocket_balance),
    tone: 'brand',
  },
]);
</script>
