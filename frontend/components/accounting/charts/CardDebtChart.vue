<script setup>
import { computed } from 'vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import { useChartTheme } from '~/composables/useChartTheme';
import { cardDebtSeries } from '~/utils/accountingCharts';
import { formatMoney } from '~/utils/formatMoney';

const props = defineProps({
  /** CardBalanceSnapshot rows: { card_name, snapshot_date, debt_amount }. */
  snapshots: { type: Array, default: () => [] },
  monthFrom: { type: Number, default: 1 },
  monthTo: { type: Number, default: 12 },
});

const { palette, baseOptions } = useChartTheme();

const series = computed(() =>
  cardDebtSeries(props.snapshots, {
    fromMonth: props.monthFrom,
    toMonth: props.monthTo,
  }),
);

const isEmpty = computed(() =>
  series.value.every((serie) => serie.data.length === 0),
);

const options = computed(() => ({
  ...baseOptions.value,
  colors: palette.value.categorical,
  xaxis: {
    type: 'datetime',
    labels: { datetimeUTC: false },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    labels: { formatter: (value) => formatMoney(Number(value) || 0, 'COP') },
  },
  tooltip: {
    ...baseOptions.value.tooltip,
    x: { format: 'dd MMM yyyy' },
    y: { formatter: (value) => formatMoney(Number(value) || 0, 'COP') },
  },
  // Snapshots are sparse: always show the data points themselves.
  markers: { size: 4, hover: { size: 6 } },
}));
</script>

<template>
  <div
    class="bg-surface rounded-xl border border-border-muted shadow-sm p-4 sm:p-5"
    data-testid="accounting-card-debt-chart"
  >
    <h3 class="text-sm font-semibold text-text-subtle uppercase tracking-wider mb-2">
      Deuda de tarjetas
    </h3>
    <BaseEmptyState
      v-if="isEmpty"
      title="Sin registros de tarjetas"
      description="Registra snapshots en la sección Tarjetas para ver la evolución de la deuda."
    />
    <ClientOnly v-else>
      <apexchart
        type="line"
        height="300"
        :options="options"
        :series="series"
      />
      <template #fallback>
        <div class="h-72 rounded-xl bg-surface-raised motion-safe:animate-pulse" />
      </template>
    </ClientOnly>
  </div>
</template>
