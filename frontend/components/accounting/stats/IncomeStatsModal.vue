<template>
  <StatsModal
    :open="open"
    :title="`Estadísticas de ingresos ${summary?.year || ''}`"
    subtitle="Evolución, nivel de cobro y conceptos que más aportan."
    :tabs="TABS"
    v-model="activeTab"
    :loading="loading"
    @close="emit('close')"
  >
    <template #default="{ activeTab: tab }">
      <div v-if="tab === 'evolution'" class="space-y-5">
        <StatsSummaryStrip :items="evolutionStrip" />
        <StatsLineChart
          :series="evolutionSeries"
          :categories="monthCategories"
          area
          :colors="[palette.measures[0], palette.measures[1]]"
        />
      </div>

      <div v-else-if="tab === 'collection'" class="space-y-5">
        <StatsSummaryStrip :items="collectionStrip" />
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 items-center">
          <StatsRadialChart
            :value="receivedPct"
            label="Recibido del año"
            :tone="receivedPct !== null && receivedPct >= 70 ? 'success' : 'warning'"
          />
          <div class="lg:col-span-2">
            <p class="text-xs text-text-muted mb-2">
              % cobrado por mes (líquido sobre esperado; meses sin proyección no puntúan).
            </p>
            <StatsBarChart
              :series="[{ name: '% cobrado', data: monthlyCollectionPct }]"
              :categories="monthCategories"
              value-format="percent"
              :colors="[palette.measures[1]]"
              :height="230"
            />
          </div>
        </div>
      </div>

      <div v-else-if="tab === 'concepts'" class="space-y-5">
        <StatsSummaryStrip :items="conceptsStrip" />
        <p class="text-xs text-text-muted">
          Conceptos con mayor ingreso líquido del año (top {{ topConcepts.length }}).
        </p>
        <StatsBarChart
          :series="[{ name: 'Ingreso líquido', data: topConcepts.map((row) => Number(row.total)) }]"
          :categories="topConcepts.map((row) => row.concept)"
          horizontal
          :colors="[palette.measures[1]]"
          :height="Math.max(220, topConcepts.length * 44)"
          empty-title="Sin ingresos líquidos este año"
        />
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
import { shortMonthLabels } from '~/utils/accountingCharts';
import { formatMoney } from '~/utils/formatMoney';

/** Income analytics over summary.monthly + accounting/stats/ payload. */
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
  { id: 'collection', label: 'Cobro' },
  { id: 'concepts', label: 'Top conceptos' },
];

const activeTab = ref('evolution');

const { palette } = useChartTheme();

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

const monthCategories = computed(() => shortMonthLabels(props.monthly));

const evolutionSeries = computed(() => [
  { name: 'Esperado', data: props.monthly.map((row) => Number(row.expected) || 0) },
  { name: 'Líquido', data: props.monthly.map((row) => Number(row.liquid) || 0) },
]);

const receivedPct = computed(() => {
  const expected = Number(props.summary?.expected_total);
  if (!expected || expected <= 0) return null;
  const liquid = Number(props.summary?.liquid_total) || 0;
  return Math.round((liquid / expected) * 1000) / 10;
});

const monthlyCollectionPct = computed(() =>
  props.monthly.map((row) => {
    const expected = Number(row.expected) || 0;
    if (expected <= 0) return null;
    return Math.round(((Number(row.liquid) || 0) / expected) * 1000) / 10;
  }),
);

const activeLiquidMonths = computed(() =>
  props.monthly.filter((row) => Number(row.liquid) > 0),
);

const bestMonth = computed(() => {
  if (!activeLiquidMonths.value.length) return null;
  return activeLiquidMonths.value.reduce((best, row) =>
    Number(row.liquid) > Number(best.liquid) ? row : best,
  );
});

const evolutionStrip = computed(() => {
  const items = [
    { label: 'Esperado año', value: money(props.summary?.expected_total) },
    { label: 'Líquido año', value: money(props.summary?.liquid_total), tone: 'success' },
    {
      label: '% recibido',
      value: receivedPct.value === null ? '—' : `${receivedPct.value}%`,
    },
    {
      label: 'Promedio mes activo',
      value: activeLiquidMonths.value.length
        ? money(
            activeLiquidMonths.value.reduce((sum, row) => sum + Number(row.liquid), 0) /
              activeLiquidMonths.value.length,
          )
        : '—',
      sub: `${activeLiquidMonths.value.length} meses con ingreso`,
    },
  ];
  if (bestMonth.value) {
    items.push({
      label: 'Mejor mes',
      value: money(bestMonth.value.liquid),
      sub: bestMonth.value.label,
      tone: 'brand',
    });
  }
  return items;
});

const collectionStrip = computed(() => {
  const expected = Number(props.summary?.expected_total) || 0;
  const liquid = Number(props.summary?.liquid_total) || 0;
  return [
    { label: 'Esperado año', value: money(expected) },
    { label: 'Líquido año', value: money(liquid), tone: 'success' },
    {
      label: 'Pendiente año',
      value: money(Math.max(expected - liquid, 0)),
      tone: 'warning',
    },
    {
      label: 'Perdido',
      value: money(props.stats?.income?.lost_total),
      tone: 'danger',
    },
  ];
});

const topConcepts = computed(() => props.stats?.income?.top_concepts || []);

const conceptsStrip = computed(() => {
  const liquid = props.stats?.income?.liquid || {};
  return [
    { label: 'Registros líquidos', value: String(liquid.count ?? 0) },
    { label: 'Ticket promedio', value: money(liquid.avg) },
    { label: 'Mínimo', value: money(liquid.min) },
    { label: 'Máximo', value: money(liquid.max), tone: 'brand' },
    { label: 'Perdido', value: money(props.stats?.income?.lost_total), tone: 'danger' },
  ];
});
</script>
