<template>
  <div
    class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3"
    data-testid="stats-summary-strip"
  >
    <div
      v-for="item in items"
      :key="item.label"
      class="bg-surface-raised rounded-xl px-3 py-2.5"
    >
      <p class="text-[10px] text-text-muted uppercase tracking-wider leading-tight">
        {{ item.label }}
      </p>
      <p class="text-sm font-semibold tabular-nums mt-0.5" :class="toneClass(item.tone)">
        {{ item.value }}
      </p>
      <p v-if="item.sub" class="text-[10px] text-text-muted mt-0.5">{{ item.sub }}</p>
    </div>
  </div>
</template>

<script setup>
/**
 * Descriptive-stats strip shown at the top of each stats-modal tab:
 * a compact grid of labeled figures (total, promedio, min, max...).
 * Items: [{ label, value, tone?, sub? }].
 */
defineProps({
  items: { type: Array, default: () => [] },
});

const TONE_CLASSES = {
  default: 'text-text-default',
  success: 'text-success-strong',
  warning: 'text-warning-strong',
  danger: 'text-danger-strong',
  brand: 'text-text-brand',
};

function toneClass(tone) {
  return TONE_CLASSES[tone] || TONE_CLASSES.default;
}
</script>
