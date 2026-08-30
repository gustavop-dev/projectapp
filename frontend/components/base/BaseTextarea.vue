<script setup>
import { INPUT_FIELD_BASE, INPUT_FIELD_SIZE, INPUT_FIELD_ERROR } from './inputClasses'
import { oneOf } from './propValidators'

defineProps({
  modelValue: { type: String, default: '' },
  rows: { type: [Number, String], default: 3 },
  size: { type: String, default: 'md', validator: oneOf(['sm', 'md']) },
  error: { type: Boolean, default: false },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  disabledReason: { type: String, default: '' },
})
defineEmits(['update:modelValue'])
</script>

<template>
  <textarea
    :value="modelValue"
    :rows="rows"
    :placeholder="placeholder"
    :disabled="disabled"
    :title="disabled && disabledReason ? disabledReason : undefined"
    :aria-invalid="error ? 'true' : undefined"
    :class="['resize-y', INPUT_FIELD_BASE, INPUT_FIELD_SIZE[size] || INPUT_FIELD_SIZE.md, error ? INPUT_FIELD_ERROR : '']"
    @input="$emit('update:modelValue', $event.target.value)"
  />
</template>
