<script setup>
import { computed } from 'vue'
import { oneOf } from './propValidators'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  size: { type: String, default: 'md', validator: oneOf(['sm', 'md']) },
  disabled: { type: Boolean, default: false },
  ariaLabel: { type: String, default: '' },
  // Color shown when modelValue is true. Defaults to brand primary.
  // Use a semantic class like 'bg-warning-strong' to convey state instead of action.
  onClass: { type: String, default: 'bg-primary' },
  // Color shown when modelValue is false. Defaults to muted raised surface.
  offClass: { type: String, default: 'bg-surface-raised border border-border-default' },
})

const emit = defineEmits(['update:modelValue'])

const sizeMap = {
  sm: { track: 'h-5 w-9', thumb: 'h-3.5 w-3.5', translate: 'translate-x-4' },
  md: { track: 'h-6 w-11', thumb: 'h-4 w-4', translate: 'translate-x-5' },
}
const s = computed(() => sizeMap[props.size] || sizeMap.md)

function toggle() {
  if (props.disabled) return
  emit('update:modelValue', !props.modelValue)
}
</script>

<template>
  <button
    type="button"
    role="switch"
    :aria-checked="modelValue"
    :aria-label="ariaLabel"
    :disabled="disabled"
    class="relative inline-flex flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-focus-ring/40 disabled:opacity-60 disabled:cursor-not-allowed"
    :class="[s.track, modelValue ? onClass : offClass]"
    @click="toggle"
  >
    <span
      class="pointer-events-none inline-block transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
      :class="[s.thumb, modelValue ? s.translate : 'translate-x-0']"
    />
  </button>
</template>
