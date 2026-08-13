<script setup>
import { computed } from 'vue'
import { oneOf } from './propValidators'

const props = defineProps({
  modelValue: { type: [String, Number, Boolean], default: '' },
  options: {
    type: Array,
    required: true,
    // [{ value, label, testId?, disabled? }] or strings
  },
  size: { type: String, default: 'md', validator: oneOf(['sm', 'md']) },
  fullWidth: { type: Boolean, default: false },
  // Options whose labels must stay on one line (e.g. "Colombia (COP)"), at the
  // cost of an internal horizontal scroll when the control cannot fit.
  nowrap: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const normalized = computed(() =>
  props.options.map((opt) =>
    typeof opt === 'object' && opt !== null
      ? {
          value: opt.value,
          label: opt.label ?? String(opt.value),
          testId: opt.testId,
          // Per-option lock, on top of the control-wide `disabled`: a filter can
          // have one choice that does not apply yet while the rest stay live.
          disabled: opt.disabled === true,
        }
      : { value: opt, label: String(opt), disabled: false },
  ),
)

const sizeClass = computed(() =>
  props.size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3 py-2 text-sm',
)
</script>

<template>
  <div
    class="inline-flex gap-1 bg-surface-raised rounded-xl p-1"
    :class="[{ 'w-full': fullWidth }, nowrap ? 'max-w-full overflow-x-auto' : '']"
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
      :class="[
        'flex-1 rounded-lg transition-all outline-none focus:ring-2 focus:ring-focus-ring/40',
        sizeClass,
        nowrap ? 'whitespace-nowrap' : '',
        modelValue === opt.value
          ? 'bg-surface shadow-sm font-medium text-text-default'
          : 'text-text-muted hover:text-text-default',
        disabled || opt.disabled ? 'opacity-60 cursor-not-allowed' : '',
      ]"
      @click="!(disabled || opt.disabled) && emit('update:modelValue', opt.value)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>
