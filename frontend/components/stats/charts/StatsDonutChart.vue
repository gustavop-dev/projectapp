<template>
  <div data-testid="stats-donut-chart">
    <BaseEmptyState v-if="isEmpty" :title="emptyTitle" />
    <ClientOnly v-else>
      <LazyApexChart
        type="donut"
        :height="height"
        :options="options"
        :series="values"
        @data-point-selection="onDataPointSelection"
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
  /**
   * Caption above the figure in the center. Says WHICH total that figure is,
   * which stops meaning "everything" as soon as the consumer filters the set.
   * Keep it short: Apex does not wrap the center label.
   */
  totalLabel: { type: String, default: 'Total' },
  /** Replaces the tooltip's value line when the default figure is not enough. */
  tooltipValueFormatter: { type: Function, default: null },
  /** Apex chart id, required only to drive `ApexCharts.exec` (image export). */
  chartId: { type: String, default: '' },
  /**
   * Off when the consumer renders its own legend. Apex's names the slices but
   * carries no value or share, so pairing it with a richer legend just prints
   * the same list twice.
   */
  showLegend: { type: Boolean, default: true },
});

/** `select` carries the index into `labels`/`values`, for drill-down. */
const emit = defineEmits(['select']);

const { palette, baseOptions } = useChartTheme();

function onDataPointSelection(_event, _context, config) {
  emit('select', config?.dataPointIndex);
}

const isEmpty = computed(() => props.values.every((value) => !value));

const totalFormatter = computed(() => {
  if (props.valueFormat === 'money') return (total) => formatCompactMoney(total);
  return tooltipFormatter(props.valueFormat);
});

const options = computed(() => ({
  ...baseOptions.value,
  chart: {
    ...baseOptions.value.chart,
    ...(props.chartId ? { id: props.chartId } : {}),
  },
  labels: props.labels,
  colors: props.colors || palette.value.categorical,
  legend: {
    ...baseOptions.value.legend,
    position: 'bottom',
    horizontalAlign: 'center',
    show: props.showLegend,
  },
  stroke: { width: 0 },
  plotOptions: {
    pie: {
      donut: {
        size: '68%',
        labels: {
          show: true,
          total: {
            show: true,
            label: props.totalLabel,
            color: palette.value.text,
            formatter: (w) =>
              totalFormatter.value(
                w.globals.seriesTotals.reduce((sum, value) => sum + value, 0),
              ),
          },
          name: { color: palette.value.text },
          value: {
            color: palette.value.text,
            formatter: (value) => totalFormatter.value(Number(value)),
          },
        },
      },
    },
  },
  tooltip: {
    ...baseOptions.value.tooltip,
    y: { formatter: props.tooltipValueFormatter || tooltipFormatter(props.valueFormat) },
  },
}));
</script>
