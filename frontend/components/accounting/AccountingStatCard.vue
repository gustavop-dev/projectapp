<template>
  <component
    :is="clickable ? 'button' : 'div'"
    :type="clickable ? 'button' : undefined"
    class="bg-surface rounded-xl border border-border-muted shadow-sm p-4 sm:p-5"
    :class="
      clickable
        ? 'relative block w-full text-left cursor-pointer transition-shadow duration-base motion-reduce:transition-none hover:shadow-raised hover:border-border-default focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring'
        : ''
    "
    :aria-label="clickable ? `Ver estadísticas de ${label}` : undefined"
    @click="clickable && emit('click')"
  >
    <ChartBarIcon
      v-if="clickable"
      class="absolute top-3 right-3 w-4 h-4 text-text-subtle"
      aria-hidden="true"
    />
    <p class="text-xs text-text-muted uppercase tracking-wider leading-tight mb-1">
      {{ label }}
    </p>
    <p class="text-2xl font-semibold" :class="toneClass" data-testid="accounting-stat-value">
      {{ value }}
    </p>
    <p v-if="sub" class="text-xs text-text-muted mt-1">{{ sub }}</p>
  </component>
</template>

<script setup>
import { computed } from 'vue';
import { ChartBarIcon } from '@heroicons/vue/24/outline';

const props = defineProps({
  label: { type: String, required: true },
  value: { type: String, default: '' },
  sub: { type: String, default: '' },
  tone: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'success', 'warning', 'danger', 'brand'].includes(v),
  },
  /** Renders the card as a button with a stats affordance; emits `click`. */
  clickable: { type: Boolean, default: false },
});

const emit = defineEmits(['click']);

const TONE_CLASSES = {
  default: 'text-text-default',
  success: 'text-success-strong',
  warning: 'text-warning-strong',
  danger: 'text-danger-strong',
  brand: 'text-text-brand',
};

const toneClass = computed(() => TONE_CLASSES[props.tone] || TONE_CLASSES.default);
</script>
