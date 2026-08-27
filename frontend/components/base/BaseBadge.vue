<script setup>
import { computed } from 'vue'
import { oneOf } from './propValidators'

const props = defineProps({
  variant: { type: String, default: 'neutral', validator: oneOf(['neutral', 'success', 'warning', 'danger', 'info', 'accent', 'primary']) },
  size: { type: String, default: 'md', validator: oneOf(['sm', 'md']) },
  /** Statuses and chips are atomic UI text. Only arbitrary prose/data should
   * opt into wrapping explicitly. */
  textPolicy: {
    type: String,
    default: 'atomic',
    validator: oneOf(['atomic', 'wrap']),
  },
})

const variants = {
  neutral: 'bg-surface-raised text-text-muted',
  success: 'bg-success-soft text-success-strong',
  warning: 'bg-warning-soft text-warning-strong',
  danger: 'bg-danger-soft text-danger-strong',
  info: 'bg-info-soft text-info-strong',
  accent: 'bg-accent-soft text-primary-strong',
  // text-text-brand, not text-primary-strong: primary-soft goes translucent
  // dark in dark mode and primary-strong stays near-black — unreadable there.
  primary: 'bg-primary-soft text-text-brand',
}

const sizes = {
  sm: 'px-2 py-0.5 text-[10px]',
  md: 'px-2.5 py-1 text-xs',
}

const classes = computed(() => [
  'inline-flex min-w-0 max-w-full items-center gap-1 rounded-full font-medium',
  props.textPolicy === 'atomic'
    ? 'flex-nowrap whitespace-nowrap'
    : 'flex-wrap whitespace-normal [overflow-wrap:anywhere]',
  variants[props.variant] || variants.neutral,
  sizes[props.size] || sizes.md,
])
</script>

<template>
  <span :class="classes">
    <slot />
  </span>
</template>
