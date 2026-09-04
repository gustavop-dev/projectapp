<template>
  <span
    class="inline-block shrink-0 rounded-full shadow-sm ring-2"
    :class="[sizeClass, toneClass]"
    :data-testid="testId"
    aria-hidden="true"
  />
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  confidence: { type: String, default: '' },
  size: { type: String, default: 'md' },
  testId: { type: String, default: 'receivable-confidence-dot' },
});

const sizeClass = computed(() => (
  props.size === 'sm' ? 'h-2.5 w-2.5' : 'h-3 w-3'
));

const toneClass = computed(() => ({
  high: 'bg-success-strong ring-success-soft',
  medium: 'bg-warning-strong ring-warning-soft',
  low: 'bg-danger-strong ring-danger-soft',
}[props.confidence] || 'bg-text-subtle ring-surface-raised'));
</script>
