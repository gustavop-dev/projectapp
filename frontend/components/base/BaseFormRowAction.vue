<script setup>
/**
 * Compact action that accompanies a field inside `BaseFormRow`.
 *
 * It inherits the same label/control/error bands as a field but only paints in
 * the control band. The action therefore follows the input, never the combined
 * height of its label and group help. Outside an aligned row it falls back to a
 * normal block so responsive stacking keeps the reading order.
 */
import { computed, inject, unref } from 'vue'
import { FIELD_ALIGNED, FIELD_CELL, FORM_ROW_ALIGN } from './formRowClasses'
import { oneOf } from './propValidators'

const props = defineProps({
  standalone: { type: Boolean, default: false },
  align: {
    type: String,
    default: 'center',
    validator: oneOf(['start', 'center', 'end']),
  },
})

const rowAlign = inject(FORM_ROW_ALIGN, null)
const alignAt = computed(() => (props.standalone ? null : unref(rowAlign)))
const rootClass = computed(() => (alignAt.value ? FIELD_ALIGNED[alignAt.value] : ''))
const cellClass = computed(() => (alignAt.value ? FIELD_CELL[alignAt.value] : 'contents'))

// A field cell becomes `block` at the row breakpoint. This cell must instead
// become flex at that same breakpoint; adding an unprefixed `flex` is not
// enough because the responsive `block` utility wins in the generated CSS.
const ACTION_CELL = {
  sm: 'contents sm:flex',
  md: 'contents md:flex',
  portrait: 'contents panel-portrait:flex',
  landscape: 'contents panel-landscape:flex',
}
const actionCellClass = computed(() => (
  alignAt.value ? ACTION_CELL[alignAt.value] : 'contents'
))

const actionClass = computed(() => ({
  start: 'self-stretch items-start',
  center: 'self-stretch items-center',
  end: 'self-stretch items-end',
}[props.align]))
</script>

<template>
  <div :class="rootClass">
    <span aria-hidden="true" :class="cellClass" />
    <div :class="[actionCellClass, actionClass]">
      <slot />
    </div>
    <span aria-hidden="true" :class="cellClass" />
  </div>
</template>
