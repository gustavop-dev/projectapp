<template>
  <div data-testid="stats-radial-chart">
    <BaseEmptyState v-if="isEmpty" :title="emptyTitle" />
    <ClientOnly v-else>
      <apexchart
        type="radialBar"
        :height="height"
        :options="options"
        :series="[displayValue]"
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

/**
 * Single-value progress gauge (0-100). Values above 100 (e.g. card debt
 * over the credit limit) render a full ring but keep the real figure in
 * the center label.
 */
const props = defineProps({
  /** Percentage 0-100; null renders the empty state. */
  value: { type: Number, default: null },
  label: { type: String, default: '' },
  height: { type: Number, default: 220 },
  tone: {
    type: String,
    default: 'brand',
    validator: (v) => ['brand', 'success', 'warning', 'danger'].includes(v),
  },
  emptyTitle: { type: String, default: 'Sin datos suficientes' },
});

const { palette, baseOptions } = useChartTheme();

const isEmpty = computed(
  () => props.value === null || props.value === undefined || Number.isNaN(props.value),
);

const displayValue = computed(() => Math.min(100, Math.max(0, Number(props.value) || 0)));

const toneColor = computed(() => {
  const ramp = palette.value;
  const map = {
    brand: ramp.measures[0],
    success: ramp.measures[1],
    danger: ramp.measures[2],
    warning: ramp.categorical[1],
  };
  return map[props.tone] || ramp.measures[0];
});

const options = computed(() => ({
  ...baseOptions.value,
  colors: [toneColor.value],
  plotOptions: {
    radialBar: {
      hollow: { size: '58%' },
      track: { background: palette.value.grid },
      dataLabels: {
        name: {
          show: Boolean(props.label),
          fontSize: '12px',
          color: palette.value.text,
          offsetY: 24,
        },
        value: {
          fontSize: '26px',
          fontWeight: 600,
          color: palette.value.text,
          offsetY: props.label ? -12 : 4,
          formatter: () => `${Math.round(Number(props.value) * 10) / 10}%`,
        },
      },
    },
  },
  labels: props.label ? [props.label] : [],
}));
</script>
