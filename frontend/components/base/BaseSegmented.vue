<script setup>
import { computed } from 'vue'
import { oneOf } from './propValidators'
import {
  SEGMENTED_WRAPPER,
  SEGMENTED_SIZE,
  SEGMENTED_ITEM_BASE,
  SEGMENTED_ITEM_ON,
  SEGMENTED_ITEM_OFF,
  SEGMENTED_ITEM_DISABLED,
  normalizeSegmentedOptions,
} from './segmentedClasses'

const props = defineProps({
  modelValue: { type: [String, Number, Boolean], default: '' },
  options: {
    type: Array,
    required: true,
    // [{ value, label, testId?, disabled? }] or strings
  },
  size: { type: String, default: 'md', validator: oneOf(['sm', 'md']) },
  fullWidth: { type: Boolean, default: false },
  /** Compatibility prop. Every short segmented label is now atomic; when the
   * complete group does not fit it reflows between options, never inside one. */
  nowrap: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false },
  disabledReason: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const normalized = computed(() => normalizeSegmentedOptions(props.options))

const sizeClass = computed(() => SEGMENTED_SIZE[props.size] || SEGMENTED_SIZE.md)
</script>

<template>
  <div
    :class="[SEGMENTED_WRAPPER, { 'w-full': fullWidth }]"
    role="tablist"
  >
    <button
      v-for="opt in normalized"
      :key="String(opt.value)"
      type="button"
      role="tab"
      :data-testid="opt.testId"
      :aria-selected="modelValue === opt.value"
      :disabled="disabled || opt.disabled"
      :title="(disabled && disabledReason) || opt.disabledReason || undefined"
      :aria-description="(disabled && disabledReason) || opt.disabledReason || undefined"
      :class="[
        SEGMENTED_ITEM_BASE,
        sizeClass,
        modelValue === opt.value ? SEGMENTED_ITEM_ON : SEGMENTED_ITEM_OFF,
        disabled || opt.disabled ? SEGMENTED_ITEM_DISABLED : '',
      ]"
      @click="!(disabled || opt.disabled) && emit('update:modelValue', opt.value)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>
