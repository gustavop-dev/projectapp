<script setup>
import { computed } from 'vue';

/**
 * Inline expiration chip for admin surfaces (list row / editor header).
 * Purely presentational — reads the values the API already computes
 * (`is_expired`, `days_remaining`), so no per-row countdown timer is needed.
 * Renders nothing when the diagnostic has no expiry set.
 */
const props = defineProps({
  expiresAt: { type: String, default: null },
  isExpired: { type: Boolean, default: false },
  daysRemaining: { type: Number, default: null },
});

const state = computed(() => {
  if (!props.expiresAt) return null;
  if (props.isExpired) {
    return { label: 'Expirado', cls: 'bg-danger-soft text-danger-strong' };
  }
  const days = props.daysRemaining;
  if (days === null) return null;
  if (days <= 1) {
    return {
      label: days <= 0 ? 'Vence hoy' : 'Vence mañana',
      cls: 'bg-danger-soft text-danger-strong',
    };
  }
  if (days <= 3) {
    return { label: `Vence en ${days} d`, cls: 'bg-warning-soft text-warning-strong' };
  }
  if (days <= 7) {
    return { label: `Vence en ${days} d`, cls: 'bg-warning-soft text-warning-strong' };
  }
  return { label: `Vence en ${days} d`, cls: 'bg-surface-raised text-text-muted' };
});
</script>

<template>
  <span
    v-if="state"
    class="inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-medium"
    :class="state.cls"
    data-testid="diagnostic-expiration-chip"
  >{{ state.label }}</span>
</template>
