<template>
  <div data-testid="stats-line-chart">
    <BaseEmptyState v-if="isEmpty" :title="emptyTitle" />
    <ClientOnly v-else>
      <apexchart
        :type="area ? 'area' : 'line'"
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

<script setup>
import { computed } from 'vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import { useChartTheme } from '~/composables/useChartTheme';
import { axisFormatter, tooltipFormatter } from '~/utils/statsChartFormat';

/** Evolution line/area chart over category ticks (usually months). */
const props = defineProps({
  /** Apex series: [{ name, data }]; null data points break the line. */
  series: { type: Array, default: () => [] },
  categories: { type: Array, default: () => [] },
  height: { type: Number, default: 260 },
  area: { type: Boolean, default: false },
  valueFormat: {
    type: String,
    default: 'money',
    validator: (v) => ['money', 'number', 'percent'].includes(v),
  },
  /** Override series colors; defaults to the measures ramp. */
  colors: { type: Array, default: null },
  emptyTitle: { type: String, default: 'Sin datos en el período' },
});

const { palette, baseOptions } = useChartTheme();

const isEmpty = computed(
  () =>
    props.series.length === 0 ||
    props.series.every((serie) => (serie.data || []).every((value) => !value)),
);

const options = computed(() => ({
  ...baseOptions.value,
  colors: props.colors || palette.value.measures,
  ...(props.area
    ? { fill: { type: 'gradient', gradient: { opacityFrom: 0.3, opacityTo: 0.04 } } }
    : {}),
  xaxis: {
    type: 'category',
    categories: props.categories,
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: { labels: { formatter: axisFormatter(props.valueFormat) } },
  tooltip: {
    ...baseOptions.value.tooltip,
    y: { formatter: tooltipFormatter(props.valueFormat) },
  },
}));
</script>
