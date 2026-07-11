<template>
  <div
    class="h-full flex flex-col bg-surface rounded-xl border border-border-muted shadow-sm p-5 sm:p-6"
    data-testid="accounting-hero-kpi"
  >
    <template v-if="loading">
      <div class="h-3 w-40 rounded bg-surface-raised motion-safe:animate-pulse mb-4" />
      <div class="h-10 w-64 max-w-full rounded bg-surface-raised motion-safe:animate-pulse mb-5" />
      <div class="h-2 w-full rounded-full bg-surface-raised motion-safe:animate-pulse" />
      <div class="h-8 w-full rounded bg-surface-raised motion-safe:animate-pulse mt-auto" />
    </template>
    <template v-else>
      <div class="min-w-0">
        <p class="text-xs text-text-muted uppercase tracking-wider leading-tight mb-1">
          {{ label }}
        </p>
        <p
          class="text-4xl sm:text-5xl font-semibold tabular-nums"
          :class="toneClass"
          data-testid="accounting-hero-value"
        >
          {{ formattedValue }}
        </p>
        <p v-if="sub" class="text-xs text-text-muted mt-2">{{ sub }}</p>
      </div>
      <div v-if="progress !== null" class="mt-5">
        <div
          class="h-2 rounded-full bg-surface-raised overflow-hidden"
          role="progressbar"
          :aria-valuenow="clampedProgress"
          aria-valuemin="0"
          aria-valuemax="100"
          :aria-label="progressLabel || 'Progreso'"
        >
          <div
            class="h-full rounded-full transition-[width] duration-500 motion-reduce:transition-none"
            :class="progressToneClass"
            :style="{ width: `${clampedProgress}%` }"
          />
        </div>
        <p v-if="progressLabel" class="text-xs text-text-muted mt-1.5">{{ progressLabel }}</p>
      </div>
      <div v-if="monthly.length >= 2" class="mt-4 flex-1 min-h-[150px]">
        <AccountingHeroUtilityChart :monthly="monthly" />
      </div>
      <div
        v-if="stats.length"
        class="mt-auto pt-5 border-t border-border-muted grid grid-cols-2 sm:grid-cols-3 gap-3"
        data-testid="accounting-hero-stats"
      >
        <div v-for="stat in stats" :key="stat.label" class="min-w-0">
          <p class="text-[10px] text-text-muted uppercase tracking-wider truncate">
            {{ stat.label }}
          </p>
          <p
            class="text-sm font-semibold tabular-nums"
            :class="statToneClass(stat)"
          >
            {{ stat.value }}
          </p>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, toRef } from 'vue';
import AccountingHeroUtilityChart from '~/components/accounting/charts/AccountingHeroUtilityChart.vue';
import { useAnimatedNumber } from '~/composables/useAnimatedNumber';
import { formatMoney } from '~/utils/formatMoney';

/**
 * Primary dashboard KPI: one large animated money figure with optional
 * progress bar and a full-width "Utilidad por mes" line chart filling
 * the card's free vertical space. The count-up respects
 * prefers-reduced-motion via useAnimatedNumber.
 */
const props = defineProps({
  label: { type: String, required: true },
  value: { type: Number, default: 0 },
  sub: { type: String, default: '' },
  tone: {
    type: String,
    default: 'neutral',
    validator: (v) => ['neutral', 'success', 'danger'].includes(v),
  },
  /** 0-100 (clamped). null hides the progress bar. */
  progress: { type: Number, default: null },
  progressLabel: { type: String, default: '' },
  /** summary.monthly rows for the "Utilidad por mes" chart. */
  monthly: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  /** Mini-stats footer pinned to the card bottom: [{ label, value, tone? }]. */
  stats: { type: Array, default: () => [] },
});

const TONE_CLASSES = {
  neutral: 'text-text-default',
  success: 'text-success-strong',
  danger: 'text-danger-strong',
};

const PROGRESS_TONE_CLASSES = {
  neutral: 'bg-primary',
  success: 'bg-success-strong',
  danger: 'bg-danger-strong',
};

const toneClass = computed(() => TONE_CLASSES[props.tone] || TONE_CLASSES.neutral);
const progressToneClass = computed(
  () => PROGRESS_TONE_CLASSES[props.tone] || PROGRESS_TONE_CLASSES.neutral,
);

const { animated } = useAnimatedNumber(toRef(props, 'value'), 700);
const formattedValue = computed(() => formatMoney(animated.value, 'COP'));

const clampedProgress = computed(() =>
  Math.min(100, Math.max(0, Math.round(Number(props.progress) || 0))),
);

function statToneClass(stat) {
  return TONE_CLASSES[stat.tone] || TONE_CLASSES.neutral;
}
</script>
