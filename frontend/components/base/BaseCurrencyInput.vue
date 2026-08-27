<script setup>
import { computed, ref, watch } from 'vue'
import { INPUT_FIELD_BASE, INPUT_FIELD_SIZE, INPUT_FIELD_ERROR } from './inputClasses'
import { oneOf } from './propValidators'

/**
 * Money input that live-formats es-CO thousands separators while typing
 * (1234567 -> "1.234.567") and emits the numeric value (null when empty).
 * With decimals > 0 a single comma is accepted as decimal separator.
 * With `allowNegative` a leading minus survives sanitising, so refunds and
 * chargebacks keep their sign instead of being silently flipped positive.
 * With `suggestion` an empty field shows the amount as its placeholder and
 * adopts it (selected, so typing replaces) on click or tab focus.
 */
const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  decimals: { type: Number, default: 0 },
  size: { type: String, default: 'md', validator: oneOf(['sm', 'md']) },
  error: { type: Boolean, default: false },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  disabledReason: { type: String, default: '' },
  /** Keep a leading "-" so negative amounts can be typed and edited. */
  allowNegative: { type: Boolean, default: false },
  /** Amount offered while empty; a zero suggests without auto-filling. */
  suggestion: { type: Number, default: null },
})

const emit = defineEmits(['update:modelValue'])

const display = ref('')

function sanitize(raw) {
  const text = String(raw ?? '')
  // Only a minus in the first position counts — "1-2" is a typo, not a sign.
  const negative = props.allowNegative && text.trimStart().startsWith('-')
  let clean = text.replace(/[^\d,]/g, '')
  if (props.decimals === 0) {
    clean = clean.replace(/,/g, '')
  } else {
    const firstComma = clean.indexOf(',')
    if (firstComma !== -1) {
      clean =
        clean.slice(0, firstComma + 1) +
        clean.slice(firstComma + 1).replace(/,/g, '').slice(0, props.decimals)
    }
  }
  // A bare "-" is kept so the sign can be typed before the digits.
  return negative ? `-${clean}` : clean
}

function toNumber(clean) {
  if (!clean || clean === ',' || clean === '-' || clean === '-,') return null
  const numeric = Number(clean.replace(',', '.'))
  return Number.isFinite(numeric) ? numeric : null
}

function formatDisplay(clean) {
  if (!clean) return ''
  const negative = clean.startsWith('-')
  const body = negative ? clean.slice(1) : clean
  if (!body) return negative ? '-' : ''
  const [intPart, decPart] = body.split(',')
  const formattedInt = new Intl.NumberFormat('es-CO').format(
    intPart ? parseInt(intPart, 10) : 0,
  )
  const formatted = decPart !== undefined ? `${formattedInt},${decPart}` : formattedInt
  return negative ? `-${formatted}` : formatted
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
  // Keep the caret after the same count of significant chars (digits/comma/sign).
  const significantLeft = previousValue
    .slice(0, previousCaret)
    .replace(/[^\d,-]/g, '').length
  let position = 0
  let seen = 0
  while (position < display.value.length && seen < significantLeft) {
    if (/[\d,-]/.test(display.value[position])) seen += 1
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

const effectivePlaceholder = computed(() =>
  (props.suggestion == null ? props.placeholder : fromModel(props.suggestion) || '0'),
)

// One-shot flag: the mouseup that follows a click-focus would collapse the
// select-all done in onFocus; it is swallowed exactly once.
const justAdopted = ref(false)

function onFocus(event) {
  if (display.value || !(Number(props.suggestion) > 0)) return
  const el = event.target
  const clean = sanitize(fromModel(props.suggestion))
  display.value = formatDisplay(clean)
  // Write the DOM value synchronously — the :value binding lands next tick,
  // too late for select() to grab the adopted text.
  el.value = display.value
  el.select()
  justAdopted.value = true
  emit('update:modelValue', toNumber(clean))
}

function onMouseup(event) {
  if (!justAdopted.value) return
  justAdopted.value = false
  event.preventDefault()
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
    :placeholder="effectivePlaceholder"
    :disabled="disabled"
    :title="disabled && disabledReason ? disabledReason : undefined"
    :class="[INPUT_FIELD_BASE, INPUT_FIELD_SIZE[size] || INPUT_FIELD_SIZE.md, error ? INPUT_FIELD_ERROR : '']"
    @input="onInput"
    @focus="onFocus"
    @mouseup="onMouseup"
    @blur="justAdopted = false"
  />
</template>
