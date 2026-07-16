<template>
  <component
    :is="rootTag"
    :to="to || undefined"
    class="block bg-surface rounded-xl border border-border-muted shadow-card p-4"
    :class="to
      ? 'transition-shadow duration-base motion-reduce:transition-none hover:shadow-raised hover:border-border-default focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring'
      : ''"
    data-testid="dashboard-stat-tile"
  >
    <p class="text-xs text-text-muted uppercase tracking-wider leading-tight mb-1">
      {{ label }}
    </p>
    <p
      class="text-2xl font-light tabular-nums"
      :class="toneClass"
      data-testid="dashboard-stat-value"
    >
      {{ displayValue }}
    </p>
    <p v-if="sub" class="text-xs text-text-subtle mt-1">{{ sub }}</p>
    <AccountingSparkline
      v-if="sparkline.length >= 2"
      :points="sparkline"
      :width="140"
      :height="28"
      :strokeClass="sparklineStroke"
      :aria-label="sparklineLabel"
      class="mt-2"
    />
  </component>
</template>

<script setup>
import { computed } from 'vue';
import AccountingSparkline from '~/components/accounting/AccountingSparkline.vue';
import { useAnimatedNumber } from '~/composables/useAnimatedNumber';
import { formatMoney } from '~/utils/formatMoney';

/**
 * Generic panel KPI tile. Currency and plain numbers count up via
 * useAnimatedNumber (jumps under reduced motion); percentages render
 * as-is to keep their decimal precision. A null value renders "—".
 */
const props = defineProps({
  label: { type: String, required: true },
  value: { type: Number, default: null },
  format: {
    type: String,
    default: 'number',
    validator: (v) => ['number', 'currency', 'percent'].includes(v),
  },
  sub: { type: String, default: '' },
  tone: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'success', 'warning', 'danger', 'brand'].includes(v),
  },
  /** Route the tile deep-links to; omit for a static tile. */
  to: { type: [String, Object], default: null },
  /** Chronological numeric series; hidden below 2 points. */
  sparkline: { type: Array, default: () => [] },
  sparklineLabel: { type: String, default: '' },
});

const rootTag = computed(() => (props.to ? 'NuxtLink' : 'div'));

const TONE_CLASSES = {
  default: 'text-text-default',
  success: 'text-success-strong',
  warning: 'text-warning-strong',
  danger: 'text-danger-strong',
  brand: 'text-text-brand',
};

const toneClass = computed(() => TONE_CLASSES[props.tone] || TONE_CLASSES.default);

const numericValue = computed(() => {
  const n = Number(props.value);
  return Number.isFinite(n) ? n : 0;
});

const { animated } = useAnimatedNumber(numericValue, 700);

const displayValue = computed(() => {
  if (props.value === null || props.value === undefined) return '—';
  if (props.format === 'percent') {
    return `${Math.round(numericValue.value * 10) / 10}%`;
  }
  if (props.format === 'currency') {
    return formatMoney(animated.value);
  }
  return new Intl.NumberFormat('es-CO').format(animated.value);
});

const sparklineStroke = computed(() =>
  props.tone === 'danger' ? 'text-danger-strong' : 'text-text-brand',
);
</script>
