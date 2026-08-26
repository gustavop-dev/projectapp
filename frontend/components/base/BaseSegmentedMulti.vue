<script setup>
/**
 * Checkable sibling of BaseSegmented, for filter dimensions where several
 * values can be marked at once ("Cobro: sin pagos + parcial").
 *
 * It is a separate component rather than a `multiple` prop on BaseSegmented
 * because the two need different accessibility trees, not different behavior:
 * single choice is a `tablist` of mutually exclusive `tab`s, while a checkable
 * group is `role="group"` with `aria-pressed` toggles. A tablist reporting two
 * selected tabs lies to a screen reader, and BaseSegmented is used by ~20 form
 * modals where single choice is the correct semantics.
 *
 * `clearValue` (the "Todos" option) is an ACTION, not a value: it empties the
 * dimension and is never stored in the array. That is what keeps "Todos"
 * meaning "no cut" instead of becoming a fourth thing a saved tab could hold.
 */
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
  modelValue: { type: Array, default: () => [] },
  options: {
    type: Array,
    required: true,
    // [{ value, label, testId?, disabled? }] or strings
  },
  size: { type: String, default: 'md', validator: oneOf(['sm', 'md']) },
  fullWidth: { type: Boolean, default: false },
  nowrap: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  disabledReason: { type: String, default: '' },
  /** Accessible name of the group; the panel also renders a visible label. */
  label: { type: String, default: null },
  /** The option token that means "no cut" — clicking it clears the dimension. */
  clearValue: { type: [String, Number], default: '' },
  /** Emits `${testIdPrefix}-${value}`, and `${testIdPrefix}-all` for clear. */
  testIdPrefix: { type: String, default: null },
})

const emit = defineEmits(['update:modelValue'])

const normalized = computed(() => normalizeSegmentedOptions(props.options))

const sizeClass = computed(() => SEGMENTED_SIZE[props.size] || SEGMENTED_SIZE.md)

const selected = computed(() => (Array.isArray(props.modelValue) ? props.modelValue : []))

function isClearOption(opt) {
  return opt.value === props.clearValue
}

function isOn(opt) {
  return isClearOption(opt) ? selected.value.length === 0 : selected.value.includes(opt.value)
}

function testIdFor(opt) {
  if (opt.testId) return opt.testId
  if (!props.testIdPrefix) return undefined
  return `${props.testIdPrefix}-${isClearOption(opt) ? 'all' : opt.value}`
}

/**
 * Emitted arrays follow the OPTIONS order, never the click order. Two tabs
 * holding the same values in a different sequence would otherwise compare as
 * different (`sameFilters` is a deep equal, and arrays are order-sensitive),
 * so a tab would show the drift dot purely because of how it was clicked.
 */
function toggle(opt) {
  if (props.disabled || opt.disabled) return
  if (isClearOption(opt)) {
    if (selected.value.length) emit('update:modelValue', [])
    return
  }
  const next = new Set(selected.value)
  if (next.has(opt.value)) next.delete(opt.value)
  else next.add(opt.value)
  emit(
    'update:modelValue',
    normalized.value
      .filter((o) => !isClearOption(o) && next.has(o.value))
      .map((o) => o.value),
  )
}
</script>

<template>
  <div
    :class="[SEGMENTED_WRAPPER, { 'w-full': fullWidth }, nowrap ? 'max-w-full flex-wrap' : '']"
    role="group"
    :aria-label="label || undefined"
  >
    <button
      v-for="opt in normalized"
      :key="String(opt.value)"
      type="button"
      :data-testid="testIdFor(opt)"
      :aria-pressed="isOn(opt)"
      :disabled="disabled || opt.disabled"
      :title="(disabled && disabledReason) || opt.disabledReason || undefined"
      :aria-label="(disabled || opt.disabled) && ((disabled && disabledReason) || opt.disabledReason)
        ? `${opt.label}: ${(disabled && disabledReason) || opt.disabledReason}`
        : undefined"
      :class="[
        SEGMENTED_ITEM_BASE,
        sizeClass,
        nowrap ? 'whitespace-nowrap' : '',
        isOn(opt) ? SEGMENTED_ITEM_ON : SEGMENTED_ITEM_OFF,
        disabled || opt.disabled ? SEGMENTED_ITEM_DISABLED : '',
      ]"
      @click="toggle(opt)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>
