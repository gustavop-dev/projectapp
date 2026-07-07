<script setup>
import { computed } from 'vue'

const props = defineProps({
  // Boolean model → single toggle. Array model → checkbox group (the item's
  // `value` is added/removed), matching native `v-model` on a checkbox.
  modelValue: { type: [Boolean, Array], default: false },
  value: { type: [String, Number, Boolean, Object], default: undefined },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const isChecked = computed(() =>
  Array.isArray(props.modelValue)
    ? props.modelValue.includes(props.value)
    : !!props.modelValue,
)

function onChange(e) {
  if (Array.isArray(props.modelValue)) {
    const next = props.modelValue.filter((v) => v !== props.value)
    if (e.target.checked) next.push(props.value)
    emit('update:modelValue', next)
  } else {
    emit('update:modelValue', e.target.checked)
  }
}
</script>

<template>
  <label class="inline-flex items-start gap-2 cursor-pointer" :class="{ 'opacity-60 cursor-not-allowed': disabled }">
    <input
      type="checkbox"
      :checked="isChecked"
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
