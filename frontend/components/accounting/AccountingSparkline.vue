<template>
  <svg
    v-if="hasEnoughPoints"
    :viewBox="`0 0 ${width} ${height}`"
    :width="width"
    :height="height"
    :class="strokeClass"
    :role="ariaLabel ? 'img' : undefined"
    :aria-label="ariaLabel || undefined"
    :aria-hidden="ariaLabel ? undefined : 'true'"
    fill="none"
    data-testid="accounting-sparkline"
  >
    <polyline
      :points="polylinePoints"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      vector-effect="non-scaling-stroke"
    />
  </svg>
</template>

<script setup>
import { computed } from 'vue';

/**
 * Minimal single-series SVG sparkline. Pure SVG on purpose: it renders on
 * the server (no ClientOnly/skeleton dance), costs no chart instance, and
 * inherits its color from `strokeClass` via currentColor so it follows the
 * light/dark tokens automatically.
 */
const props = defineProps({
  /** Numeric series in chronological order. Renders nothing below 2 points. */
  points: { type: Array, required: true },
  width: { type: Number, default: 120 },
  height: { type: Number, default: 32 },
  strokeClass: { type: String, default: 'text-text-brand' },
  /** Accessible description; when empty the SVG is marked decorative. */
  ariaLabel: { type: String, default: '' },
});

// Keeps the 2px stroke inside the viewBox at the series extremes.
const PADDING = 2;

const numericPoints = computed(() =>
  props.points.map(Number).filter(Number.isFinite),
);

const hasEnoughPoints = computed(() => numericPoints.value.length >= 2);

function round2(value) {
  return Math.round(value * 100) / 100;
}

const polylinePoints = computed(() => {
  const values = numericPoints.value;
  if (values.length < 2) return '';
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min;
  const innerHeight = props.height - PADDING * 2;
  const stepX = props.width / (values.length - 1);
  return values
    .map((value, index) => {
      // A flat series draws a midline instead of collapsing to an edge.
      const normalized = span === 0 ? 0.5 : (value - min) / span;
      const y = PADDING + (1 - normalized) * innerHeight;
      return `${round2(index * stepX)},${round2(y)}`;
    })
    .join(' ');
});
</script>
