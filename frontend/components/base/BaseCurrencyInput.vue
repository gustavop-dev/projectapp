<script setup>
import { ref, watch } from 'vue'
import { INPUT_FIELD_BASE, INPUT_FIELD_SIZE, INPUT_FIELD_ERROR } from './inputClasses'
import { oneOf } from './propValidators'

/**
 * Money input that live-formats es-CO thousands separators while typing
 * (1234567 -> "1.234.567") and emits the numeric value (null when empty).
 * With decimals > 0 a single comma is accepted as decimal separator.
 */
const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  decimals: { type: Number, default: 0 },
  size: { type: String, default: 'md', validator: oneOf(['sm', 'md']) },
  error: { type: Boolean, default: false },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const display = ref('')

function sanitize(raw) {
  let clean = String(raw ?? '').replace(/[^\d,]/g, '')
  if (props.decimals === 0) return clean.replace(/,/g, '')
  const firstComma = clean.indexOf(',')
  if (firstComma !== -1) {
    clean =
      clean.slice(0, firstComma + 1) +
      clean.slice(firstComma + 1).replace(/,/g, '').slice(0, props.decimals)
  }
  return clean
}

function toNumber(clean) {
  if (!clean || clean === ',') return null
  const numeric = Number(clean.replace(',', '.'))
  return Number.isFinite(numeric) ? numeric : null
}

function formatDisplay(clean) {
  if (!clean) return ''
  const [intPart, decPart] = clean.split(',')
  const formattedInt = new Intl.NumberFormat('es-CO').format(
    intPart ? parseInt(intPart, 10) : 0,
  )
  return decPart !== undefined ? `${formattedInt},${decPart}` : formattedInt
}

function fromModel(value) {
  if (value === null || value === undefined || value === '') return ''
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return ''
  const fixed = props.decimals > 0 ? String(numeric.toFixed(props.decimals)) : String(Math.round(numeric))
  // Drop trailing zero decimals so "1200.00" prefills as "1.200".
  const clean = fixed.replace('.', ',').replace(/,?0+$/, (m) => (m.startsWith(',') ? '' : m))
  return formatDisplay(sanitize(clean))
}

function restoreCaret(el, previousValue, previousCaret) {
  // Keep the caret after the same count of significant chars (digits/comma).
  const significantLeft = previousValue
    .slice(0, previousCaret)
    .replace(/[^\d,]/g, '').length
  let position = 0
  let seen = 0
  while (position < display.value.length && seen < significantLeft) {
    if (/[\d,]/.test(display.value[position])) seen += 1
    position += 1
  }
  el.setSelectionRange(position, position)
}

function onInput(event) {
  const el = event.target
  const previousValue = el.value
  const previousCaret = el.selectionStart ?? previousValue.length
  const clean = sanitize(previousValue)
  display.value = formatDisplay(clean)
  el.value = display.value
  restoreCaret(el, previousValue, previousCaret)
  emit('update:modelValue', toNumber(clean))
}

watch(
  () => props.modelValue,
  (value) => {
    const currentNumeric = toNumber(sanitize(display.value))
    const incoming = value === null || value === undefined || value === '' ? null : Number(value)
    if (currentNumeric !== incoming) display.value = fromModel(value)
  },
  { immediate: true },
)
</script>

<template>
  <input
    type="text"
    :inputmode="decimals > 0 ? 'decimal' : 'numeric'"
    autocomplete="off"
    :value="display"
    :placeholder="placeholder"
    :disabled="disabled"
    :class="[INPUT_FIELD_BASE, INPUT_FIELD_SIZE[size] || INPUT_FIELD_SIZE.md, error ? INPUT_FIELD_ERROR : '']"
    @input="onInput"
  />
</template>
