<template>
  <BaseBadge
    :variant="definition.badgeVariant"
    :size="size"
    :data-testid="testId"
  >
    <ReceivableConfidenceDot :confidence="confidence" size="sm" />
    {{ compact ? definition.shortLabel : definition.label }}
  </BaseBadge>
</template>

<script setup>
import { computed } from 'vue';
import BaseBadge from '~/components/base/BaseBadge.vue';
import ReceivableConfidenceDot from '~/components/accounting/ReceivableConfidenceDot.vue';
import { confidenceDefinition } from '~/utils/receivables';

const props = defineProps({
  confidence: { type: String, default: '' },
  compact: { type: Boolean, default: false },
  size: { type: String, default: 'sm' },
  testId: { type: String, default: 'receivable-confidence-badge' },
});

const definition = computed(() => confidenceDefinition(props.confidence));
</script>
