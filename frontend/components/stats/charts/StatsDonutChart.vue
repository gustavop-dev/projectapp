<template>
  <div data-testid="stats-donut-chart">
    <BaseEmptyState v-if="isEmpty" :title="emptyTitle" />
    <ClientOnly v-else>
      <apexchart type="donut" :height="height" :options="options" :series="values" />
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
import { formatCompactMoney } from '~/utils/formatMoney';
import { tooltipFormatter } from '~/utils/statsChartFormat';

/** Distribution donut with the total in the center and legend below. */
const props = defineProps({
  labels: { type: Array, default: () => [] },
  values: { type: Array, default: () => [] },
  height: { type: Number, default: 260 },
  valueFormat: {
    type: String,
    default: 'money',
    validator: (v) => ['money', 'number', 'percent'].includes(v),
  },
  /** Override slice colors; defaults to the categorical ramp. */
  colors: { type: Array, default: null },
  emptyTitle: { type: String, default: 'Sin datos para distribuir' },
});

const { palette, baseOptions } = useChartTheme();

const isEmpty = computed(() => props.values.every((value) => !value));

const totalFormatter = computed(() => {
  if (props.valueFormat === 'money') return (total) => formatCompactMoney(total);
  return tooltipFormatter(props.valueFormat);
});

const options = computed(() => ({
  ...baseOptions.value,
  labels: props.labels,
  colors: props.colors || palette.value.categorical,
  legend: { ...baseOptions.value.legend, position: 'bottom', horizontalAlign: 'center' },
  stroke: { width: 0 },
  plotOptions: {
    pie: {
      donut: {
        size: '68%',
        labels: {
          show: true,
          total: {
            show: true,
            label: 'Total',
            formatter: (w) =>
              totalFormatter.value(
                w.globals.seriesTotals.reduce((sum, value) => sum + value, 0),
              ),
          },
          value: { formatter: (value) => totalFormatter.value(Number(value)) },
        },
      },
    },
  },
  tooltip: {
    ...baseOptions.value.tooltip,
    y: { formatter: tooltipFormatter(props.valueFormat) },
  },
}));
</script>
