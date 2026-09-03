<template>
  <BaseBadge
    :variant="definition.badgeVariant"
    :size="size"
    :data-testid="testId"
  >
    <span
      class="h-2 w-2 shrink-0 rounded-full"
      :class="dotClass"
      aria-hidden="true"
    />
    {{ compact ? definition.shortLabel : definition.label }}
  </BaseBadge>
</template>

<script setup>
import { computed } from 'vue';
import BaseBadge from '~/components/base/BaseBadge.vue';
import { confidenceDefinition } from '~/utils/receivables';

const props = defineProps({
  confidence: { type: String, default: '' },
  compact: { type: Boolean, default: false },
  size: { type: String, default: 'sm' },
  testId: { type: String, default: 'receivable-confidence-badge' },
});

const definition = computed(() => confidenceDefinition(props.confidence));
const dotClass = computed(() => ({
  high: 'bg-success-strong',
  medium: 'bg-warning-strong',
  low: 'bg-danger-strong',
}[props.confidence] || 'bg-text-subtle'));
</script>
