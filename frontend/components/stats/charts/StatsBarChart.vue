<template>
  <div data-testid="stats-bar-chart">
    <BaseEmptyState v-if="isEmpty" :title="emptyTitle" />
    <ClientOnly v-else>
      <apexchart type="bar" :height="height" :options="options" :series="series" />
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

/** Bar chart (vertical, horizontal, grouped or stacked). */
const props = defineProps({
  /** Apex series: [{ name, data }]. */
  series: { type: Array, default: () => [] },
  categories: { type: Array, default: () => [] },
  height: { type: Number, default: 260 },
  horizontal: { type: Boolean, default: false },
  stacked: { type: Boolean, default: false },
  valueFormat: {
    type: String,
    default: 'money',
    validator: (v) => ['money', 'number', 'percent'].includes(v),
  },
  /** Override series colors; defaults to the measures ramp. */
  colors: { type: Array, default: null },
  /** Optional reference line (e.g. the yearly average). */
  annotationY: { type: Number, default: null },
  annotationLabel: { type: String, default: '' },
  emptyTitle: { type: String, default: 'Sin datos en el período' },
});

const { palette, baseOptions } = useChartTheme();

const isEmpty = computed(
  () =>
    props.series.length === 0 ||
    props.series.every((serie) => (serie.data || []).every((value) => !value)),
);

const valueFormatterMap = computed(() => ({
  values: axisFormatter(props.valueFormat),
  tooltip: tooltipFormatter(props.valueFormat),
}));

const options = computed(() => ({
  ...baseOptions.value,
  chart: { ...baseOptions.value.chart, stacked: props.stacked },
  colors: props.colors || palette.value.measures,
  plotOptions: {
    bar: {
      horizontal: props.horizontal,
      borderRadius: 3,
      columnWidth: '55%',
      barHeight: '65%',
    },
  },
  stroke: { width: 0 },
  xaxis: {
    type: 'category',
    categories: props.categories,
    axisBorder: { show: false },
    axisTicks: { show: false },
    ...(props.horizontal
      ? { labels: { formatter: valueFormatterMap.value.values } }
      : {}),
  },
  yaxis: props.horizontal
    ? { labels: { maxWidth: 220 } }
    : { labels: { formatter: valueFormatterMap.value.values } },
  tooltip: {
    ...baseOptions.value.tooltip,
    y: { formatter: valueFormatterMap.value.tooltip },
  },
  ...(props.annotationY !== null
    ? {
        annotations: {
          yaxis: [
            {
              y: props.annotationY,
              borderColor: palette.value.text,
              strokeDashArray: 4,
              label: {
                text: props.annotationLabel || undefined,
                style: { background: 'transparent', color: palette.value.text },
              },
            },
          ],
        },
      }
    : {}),
}));
</script>
