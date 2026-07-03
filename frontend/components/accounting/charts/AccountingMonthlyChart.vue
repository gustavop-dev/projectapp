<script setup>
import { computed } from 'vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import { useChartTheme } from '~/composables/useChartTheme';
import { monthlySeries, sliceMonthly } from '~/utils/accountingCharts';
import { formatMoney } from '~/utils/formatMoney';

const props = defineProps({
  /** summary.monthly rows: { label, expected, liquid, expenses }. */
  monthly: { type: Array, default: () => [] },
  monthFrom: { type: Number, default: 1 },
  monthTo: { type: Number, default: 12 },
});

const { palette, baseOptions } = useChartTheme();

const sliced = computed(() =>
  sliceMonthly(props.monthly, props.monthFrom, props.monthTo),
);

const chartData = computed(() => monthlySeries(sliced.value));

const isEmpty = computed(() =>
  chartData.value.series.every((serie) =>
    serie.data.every((value) => value === 0),
  ),
);

const options = computed(() => ({
  ...baseOptions.value,
  colors: palette.value.measures,
  xaxis: {
    categories: chartData.value.categories,
    labels: { rotate: -35, hideOverlappingLabels: true },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
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
  <div
    class="bg-surface rounded-xl border border-border-muted shadow-sm p-4 sm:p-5"
    data-testid="accounting-monthly-chart"
  >
    <h3 class="text-sm font-semibold text-text-subtle uppercase tracking-wider mb-2">
      Esperado vs líquido vs gastos
    </h3>
    <BaseEmptyState
      v-if="isEmpty"
      title="Sin movimientos en el rango"
      description="No hay ingresos ni gastos de la empresa en los meses seleccionados."
    />
    <ClientOnly v-else>
      <apexchart
        type="line"
        height="300"
        :options="options"
        :series="chartData.series"
      />
      <template #fallback>
        <div class="h-72 rounded-xl bg-surface-raised animate-pulse" />
      </template>
    </ClientOnly>
  </div>
</template>
