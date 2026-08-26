<script setup>
import { computed } from 'vue'
import { oneOf } from './propValidators'

const props = defineProps({
  variant: { type: String, default: 'neutral', validator: oneOf(['neutral', 'success', 'warning', 'danger', 'info', 'accent', 'primary']) },
  size: { type: String, default: 'md', validator: oneOf(['sm', 'md']) },
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
  'inline-flex min-w-0 max-w-full flex-wrap items-center gap-1 whitespace-normal font-medium rounded-full [overflow-wrap:anywhere]',
  variants[props.variant] || variants.neutral,
  sizes[props.size] || sizes.md,
])
</script>

<template>
  <span :class="classes">
    <slot />
  </span>
</template>
