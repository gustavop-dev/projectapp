<script setup>
import { computed } from 'vue';
import { useChartTheme } from '~/composables/useChartTheme';
import { formatMoney } from '~/utils/formatMoney';

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

const categories = computed(() => props.monthly.map((month) => month.label));

const series = computed(() => [
  {
    name: 'Utilidad',
    data: props.monthly.map((month) => Number(month.utility) || 0),
  },
]);

const options = computed(() => ({
  ...baseOptions.value,
  colors: [palette.value.measures[0]],
  legend: { show: false },
  xaxis: {
    categories: categories.value,
    labels: { rotate: -35, hideOverlappingLabels: true },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    tickAmount: 3,
    labels: { formatter: (value) => formatMoney(Number(value) || 0, 'COP') },
  },
  tooltip: {
    ...baseOptions.value.tooltip,
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
