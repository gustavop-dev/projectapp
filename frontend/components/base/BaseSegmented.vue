<script setup>
import { computed } from 'vue'
import { oneOf } from './propValidators'

const props = defineProps({
  modelValue: { type: [String, Number, Boolean], default: '' },
  options: {
    type: Array,
    required: true,
    // [{ value, label, testId? }] or strings
  },
  size: { type: String, default: 'md', validator: oneOf(['sm', 'md']) },
  fullWidth: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const normalized = computed(() =>
  props.options.map((opt) =>
    typeof opt === 'object' && opt !== null
      ? { value: opt.value, label: opt.label ?? String(opt.value), testId: opt.testId }
      : { value: opt, label: String(opt) },
  ),
)

const sizeClass = computed(() =>
  props.size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3 py-2 text-sm',
)
</script>

<template>
  <div
    class="inline-flex gap-1 bg-surface-raised rounded-xl p-1"
    :class="{ 'w-full': fullWidth }"
    role="tablist"
  >
    <button
      v-for="opt in normalized"
      :key="String(opt.value)"
      type="button"
      role="tab"
      :data-testid="opt.testId"
      :aria-selected="modelValue === opt.value"
      :class="[
        'flex-1 rounded-lg transition-all outline-none focus:ring-2 focus:ring-focus-ring/40',
        sizeClass,
        modelValue === opt.value
          ? 'bg-surface shadow-sm font-medium text-text-default'
          : 'text-text-muted hover:text-text-default',
      ]"
      @click="emit('update:modelValue', opt.value)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>
