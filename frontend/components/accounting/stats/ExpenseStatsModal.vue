<template>
  <StatsModal
    :open="open"
    :title="`Estadísticas de gastos ${summary?.year || ''}`"
    subtitle="Evolución, distribución y peso de los pagos recurrentes."
    :tabs="TABS"
    v-model="activeTab"
    :loading="loading"
    @close="emit('close')"
  >
    <template #default="{ activeTab: tab }">
      <div v-if="tab === 'evolution'" class="space-y-5">
        <StatsSummaryStrip :items="evolutionStrip" />
        <StatsBarChart
          :series="[{ name: 'Gastos', data: monthlyExpenses }]"
          :categories="monthCategories"
          :colors="[palette.measures[2]]"
          :annotation-y="monthlyAverage"
          annotation-label="Promedio"
        />
      </div>

      <div v-else-if="tab === 'category'" class="space-y-5">
        <StatsSummaryStrip :items="categoryStrip" />
        <div class="max-w-md mx-auto">
          <StatsDonutChart
            :labels="byCategory.map((row) => row.label)"
            :values="byCategory.map((row) => Number(row.total))"
            :colors="[palette.measures[0], palette.categorical[1]]"
            :height="280"
            empty-title="Sin gastos registrados este año"
          />
        </div>
      </div>

      <div v-else-if="tab === 'recurring'" class="space-y-5">
        <StatsSummaryStrip :items="recurringStrip" />
        <p class="text-xs text-text-muted">
          Compara el costo recurrente activo (catálogo de pagos recurrentes, valor
          actual constante) contra el gasto real registrado cada mes.
        </p>
        <StatsBarChart
          :series="[
            { name: 'Recurrente/mes', data: recurringFlatSeries },
            { name: 'Gasto real', data: monthlyExpenses },
          ]"
          :categories="monthCategories"
          :colors="[palette.categorical[1], palette.measures[2]]"
        />
      </div>

      <div v-else-if="tab === 'concepts'" class="space-y-5">
        <StatsSummaryStrip :items="conceptsStrip" />
        <p class="text-xs text-text-muted">
          Conceptos con mayor gasto del año (top {{ topConcepts.length }}).
        </p>
        <StatsBarChart
          :series="[{ name: 'Gasto', data: topConcepts.map((row) => Number(row.total)) }]"
          :categories="topConcepts.map((row) => row.concept)"
          horizontal
          :colors="[palette.measures[2]]"
          :height="Math.max(220, topConcepts.length * 44)"
          empty-title="Sin gastos registrados este año"
        />
      </div>
    </template>
  </StatsModal>
</template>

<script setup>
import { computed, ref } from 'vue';
import StatsModal from '~/components/stats/StatsModal.vue';
import StatsSummaryStrip from '~/components/stats/StatsSummaryStrip.vue';
import StatsBarChart from '~/components/stats/charts/StatsBarChart.vue';
import StatsDonutChart from '~/components/stats/charts/StatsDonutChart.vue';
import { useChartTheme } from '~/composables/useChartTheme';
import { shortMonthLabels } from '~/utils/accountingCharts';
import { formatMoney } from '~/utils/formatMoney';

/** Expense analytics over summary.monthly + accounting/stats/ payload. */
const props = defineProps({
  open: { type: Boolean, default: false },
  monthly: { type: Array, default: () => [] },
  summary: { type: Object, default: null },
  stats: { type: Object, default: null },
  loading: { type: Boolean, default: false },
});

const emit = defineEmits(['close']);

const TABS = [
  { id: 'evolution', label: 'Evolución' },
  { id: 'category', label: 'Distribución' },
  { id: 'recurring', label: 'Recurrente vs variable' },
  { id: 'concepts', label: 'Top conceptos' },
];

const activeTab = ref('evolution');

const { palette } = useChartTheme();

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

const monthCategories = computed(() => shortMonthLabels(props.monthly));

const monthlyExpenses = computed(() =>
  props.monthly.map((row) => Number(row.expenses) || 0),
);

const activeMonths = computed(() =>
  props.monthly.filter((row) => Number(row.expenses) > 0),
);

const monthlyAverage = computed(() => {
  if (!activeMonths.value.length) return null;
  const total = activeMonths.value.reduce((sum, row) => sum + Number(row.expenses), 0);
  return Math.round(total / activeMonths.value.length);
});

const highestMonth = computed(() => {
  if (!activeMonths.value.length) return null;
  return activeMonths.value.reduce((worst, row) =>
    Number(row.expenses) > Number(worst.expenses) ? row : worst,
  );
});

const lowestMonth = computed(() => {
  if (!activeMonths.value.length) return null;
  return activeMonths.value.reduce((best, row) =>
    Number(row.expenses) < Number(best.expenses) ? row : best,
  );
});

const evolutionStrip = computed(() => {
  const items = [
    { label: 'Total año', value: money(props.summary?.expenses_total), tone: 'danger' },
    {
      label: 'Promedio mes activo',
      value: monthlyAverage.value === null ? '—' : money(monthlyAverage.value),
      sub: `${activeMonths.value.length} meses con gasto`,
    },
    { label: 'Registros', value: String(props.stats?.expenses?.summary?.count ?? 0) },
  ];
  if (highestMonth.value) {
    items.push({
      label: 'Mes más alto',
      value: money(highestMonth.value.expenses),
      sub: highestMonth.value.label,
      tone: 'danger',
    });
  }
  if (lowestMonth.value && lowestMonth.value !== highestMonth.value) {
    items.push({
      label: 'Mes más bajo',
      value: money(lowestMonth.value.expenses),
      sub: lowestMonth.value.label,
      tone: 'success',
    });
  }
  return items;
});

const byCategory = computed(() => props.stats?.expenses?.by_category || []);

const categoryStrip = computed(() => {
  const summaryStats = props.stats?.expenses?.summary || {};
  const items = byCategory.value.map((row) => ({
    label: row.label,
    value: money(row.total),
    sub: `${row.count} registro${row.count === 1 ? '' : 's'}`,
  }));
  items.push({ label: 'Ticket promedio', value: money(summaryStats.avg) });
  items.push({ label: 'Máximo', value: money(summaryStats.max), tone: 'danger' });
  return items;
});

const recurringMonthly = computed(() =>
  Number(props.stats?.expenses?.recurring_monthly_cost ?? props.summary?.recurring_monthly_cost) || 0,
);

const recurringFlatSeries = computed(() =>
  props.monthly.map(() => recurringMonthly.value),
);

const recurringStrip = computed(() => {
  const average = monthlyAverage.value || 0;
  return [
    { label: 'Recurrente/mes', value: money(recurringMonthly.value), tone: 'warning' },
    { label: 'Gasto promedio/mes', value: money(average) },
    {
      label: 'Variable estimado/mes',
      value: money(Math.max(average - recurringMonthly.value, 0)),
      sub: 'promedio menos recurrente',
    },
  ];
});

const topConcepts = computed(() => props.stats?.expenses?.top_concepts || []);

const conceptsStrip = computed(() => {
  const summaryStats = props.stats?.expenses?.summary || {};
  return [
    { label: 'Registros', value: String(summaryStats.count ?? 0) },
    { label: 'Ticket promedio', value: money(summaryStats.avg) },
    { label: 'Mínimo', value: money(summaryStats.min) },
    { label: 'Máximo', value: money(summaryStats.max), tone: 'danger' },
    { label: 'Total año', value: money(summaryStats.total) },
  ];
});
</script>
