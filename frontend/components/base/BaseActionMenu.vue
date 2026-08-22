<script setup>
import BaseButton from './BaseButton.vue'
import BaseDropdown from './BaseDropdown.vue'

defineProps({
  items: { type: Array, required: true },
  label: { type: String, default: 'Acciones' },
  disabled: { type: Boolean, default: false },
  testid: { type: String, default: '' },
  placement: { type: String, default: 'bottom' },
  align: { type: String, default: 'right' },
  width: { type: String, default: 'w-56' },
  variant: { type: String, default: 'secondary' },
})
</script>

<template>
  <BaseDropdown
    :items="items"
    :placement="placement"
    :align="align"
    :width="width"
  >
    <template #trigger>
      <BaseButton
        :variant="variant"
        size="sm"
        :disabled="disabled"
        :data-testid="testid || undefined"
        aria-haspopup="menu"
      >
        {{ label }}
        <span aria-hidden="true">▾</span>
      </BaseButton>
    </template>
  </BaseDropdown>
</template>
