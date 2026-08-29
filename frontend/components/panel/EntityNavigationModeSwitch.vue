<template>
  <BaseSegmented
    full-width
    size="sm"
    :model-value="modelValue"
    :options="options"
    :aria-label="ariaLabel"
    :disabled="disabled"
    disabled-reason="Guardando la preferencia de navegación."
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
import { computed } from 'vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';

const props = defineProps({
  modelValue: { type: String, default: 'project' },
  ariaLabel: { type: String, default: 'Agrupar por proyecto o cliente' },
  testIdPrefix: { type: String, default: 'entity-mode' },
  disabled: { type: Boolean, default: false },
});

defineEmits(['update:modelValue']);

const options = computed(() => [
  {
    value: 'project',
    label: 'Proyectos',
    testId: `${props.testIdPrefix}-project`,
  },
  {
    value: 'client',
    label: 'Clientes',
    testId: `${props.testIdPrefix}-client`,
  },
]);
</script>
