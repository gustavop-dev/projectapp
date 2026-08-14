<script setup>
import { computed, inject, unref } from 'vue'
import { FIELD_ALIGNED, FIELD_CELL, FORM_ROW_ALIGN } from './formRowClasses'

const props = defineProps({
  label: { type: String, default: '' },
  hint: { type: String, default: '' },
  error: { type: String, default: '' },
  required: { type: Boolean, default: false },
  for: { type: String, default: '' },
  size: { type: String, default: 'md' }, // sm | md
  /** Ignore the surrounding `BaseFormRow` and stack on its own. For a field
   *  that is inside a row without being one of its direct children: it would
   *  pick up the marker but is not a grid item, so there is no row to inherit. */
  standalone: { type: Boolean, default: false },
})

const rowAlign = inject(FORM_ROW_ALIGN, null)

/** The breakpoint at which this field joins the row's shared bands, if any. */
const alignAt = computed(() => (props.standalone ? null : unref(rowAlign)))

const rootClass = computed(() => (alignAt.value ? FIELD_ALIGNED[alignAt.value] : ''))

/**
 * Outside a row the wrappers are `contents`, which keeps them out of the box
 * tree — the field renders exactly as it did before the bands existed.
 */
const cellClass = computed(() => (alignAt.value ? FIELD_CELL[alignAt.value] : 'contents'))
</script>

<template>
  <div :class="rootClass">
    <div :class="cellClass">
      <label
        v-if="label"
        :for="$props.for"
        class="block font-medium text-text-default mb-1"
        :class="size === 'sm' ? 'text-xs' : 'text-sm'"
      >
        {{ label }}
        <span v-if="required" class="text-danger-strong">*</span>
      </label>
    </div>
    <div :class="cellClass">
      <slot />
    </div>
    <div :class="cellClass">
      <p
        v-if="error"
        class="text-xs text-danger-strong mt-1"
      >
        {{ error }}
      </p>
      <p
        v-else-if="hint"
        class="text-xs text-text-muted mt-1"
      >
        {{ hint }}
      </p>
    </div>
  </div>
</template>
