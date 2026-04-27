<script setup>
defineProps({
  modelValue: { type: [Boolean, Array], default: false },
  value: { type: [String, Number, Boolean, Object], default: undefined },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

function onChange(e) {
  emit('update:modelValue', e.target.checked)
}
</script>

<template>
  <label class="inline-flex items-start gap-2 cursor-pointer" :class="{ 'opacity-60 cursor-not-allowed': disabled }">
    <input
      type="checkbox"
      :checked="!!modelValue"
      :value="value"
      :disabled="disabled"
      class="mt-0.5 rounded border-input-border bg-input-bg text-primary focus:ring-2 focus:ring-focus-ring/40"
      @change="onChange"
    />
    <span v-if="$slots.default" class="text-sm text-text-default">
      <slot />
    </span>
  </label>
</template>
