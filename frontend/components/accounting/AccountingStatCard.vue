<script setup>
import { computed } from 'vue';
import BaseIndicatorCard from '~/components/base/BaseIndicatorCard.vue';

const props = defineProps({
  label: { type: String, required: true },
  value: { type: String, default: '' },
  sub: { type: String, default: '' },
  tone: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'success', 'warning', 'danger', 'brand'].includes(v),
  },
  /** Compatibility flag for existing consumers. Prefer action + actionLabel. */
  clickable: { type: Boolean, default: false },
  action: { type: String, default: '' },
  actionLabel: { type: String, default: '' },
  helpLabel: { type: String, default: '' },
  helpTestId: { type: String, default: '' },
  helpPosition: { type: String, default: 'left' },
});

const emit = defineEmits(['click']);
const resolvedAction = computed(() => props.action || (props.clickable ? 'stats' : ''));
const resolvedActionLabel = computed(() => (
  props.actionLabel || (props.clickable ? `Ver estadísticas de ${props.label}` : '')
));
</script>

<template>
  <BaseIndicatorCard
    :label="label"
    :value="value"
    :support="sub"
    :tone="tone"
    :action="resolvedAction"
    :action-label="resolvedActionLabel"
    :help-label="helpLabel"
    :help-test-id="helpTestId"
    :help-position="helpPosition"
    @activate="emit('click')"
  >
    <template v-if="$slots.help" #help>
      <slot name="help" />
    </template>
  </BaseIndicatorCard>
</template>
