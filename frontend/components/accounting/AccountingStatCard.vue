<template>
  <div class="bg-surface rounded-xl border border-border-muted shadow-sm p-4 sm:p-5">
    <p class="text-xs text-text-muted uppercase tracking-wider leading-tight mb-1">
      {{ label }}
    </p>
    <p class="text-2xl font-semibold" :class="toneClass" data-testid="accounting-stat-value">
      {{ value }}
    </p>
    <p v-if="sub" class="text-xs text-text-muted mt-1">{{ sub }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  label: { type: String, required: true },
  value: { type: String, default: '' },
  sub: { type: String, default: '' },
  tone: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'success', 'warning', 'danger', 'brand'].includes(v),
  },
});

const TONE_CLASSES = {
  default: 'text-text-default',
  success: 'text-success-strong',
  warning: 'text-warning-strong',
  danger: 'text-danger-strong',
  brand: 'text-text-brand',
};

const toneClass = computed(() => TONE_CLASSES[props.tone] || TONE_CLASSES.default);
</script>
