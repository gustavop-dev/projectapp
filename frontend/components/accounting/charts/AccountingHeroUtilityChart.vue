<script setup>
import { computed } from 'vue';
import { useChartTheme } from '~/composables/useChartTheme';
import { shortMonthLabels } from '~/utils/accountingCharts';
import { formatCompactMoney, formatMoney } from '~/utils/formatMoney';

/**
 * Compact "Utilidad por mes" line for the hero KPI card. No card chrome:
 * it renders inside AccountingHeroKpi, filling the card's free vertical
 * space. Single series, so identity lives in the caption (no legend).
 */
const props = defineProps({
  /** summary.monthly rows: { label, utility, ... }. */
  monthly: { type: Array, default: () => [] },
  height: { type: Number, default: 150 },
});

const { palette, baseOptions } = useChartTheme();

const categories = computed(() => shortMonthLabels(props.monthly));

const series = computed(() => [
  {
    name: 'Utilidad',
    data: props.monthly.map((month) => Number(month.utility) || 0),
  },
]);

/** Tooltips keep the full "Enero 2026" title even though ticks are short. */
function monthLabelAt(index) {
  return props.monthly[index]?.label || '';
}

const options = computed(() => ({
  ...baseOptions.value,
  colors: [palette.value.measures[0]],
  legend: { show: false },
  xaxis: {
    type: 'category',
    categories: categories.value,
    tickPlacement: 'on',
    labels: {
      rotate: 0,
      trim: false,
      hideOverlappingLabels: true,
      style: { fontSize: '10px' },
    },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    tickAmount: 3,
    labels: { formatter: (value) => formatCompactMoney(Number(value) || 0) },
  },
  tooltip: {
    ...baseOptions.value.tooltip,
    x: { formatter: (_value, { dataPointIndex }) => monthLabelAt(dataPointIndex) },
    y: { formatter: (value) => formatMoney(Number(value) || 0, 'COP') },
  },
  markers: { size: 0, hover: { size: 5 } },
}));
</script>

<template>
  <div data-testid="accounting-hero-utility-chart">
    <p class="text-[10px] text-text-subtle uppercase tracking-wider mb-1">
      Utilidad por mes
    </p>
    <ClientOnly>
      <apexchart
        type="line"
        :height="height"
        :options="options"
        :series="series"
      />
      <template #fallback>
        <div
          class="rounded-xl bg-surface-raised motion-safe:animate-pulse"
          :style="{ height: `${height}px` }"
        />
      </template>
    </ClientOnly>
  </div>
</template>
