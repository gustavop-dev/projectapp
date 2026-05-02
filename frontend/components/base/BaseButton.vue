<script setup>
import { computed } from 'vue'
import { oneOf } from './propValidators'

const props = defineProps({
  variant: { type: String, default: 'primary', validator: oneOf(['primary', 'secondary', 'ghost', 'danger', 'accent']) },
  size: { type: String, default: 'md', validator: oneOf(['sm', 'md', 'lg']) },
  type: { type: String, default: 'button' },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  as: { type: String, default: 'button' },        // button | a | NuxtLink
  to: { type: [String, Object], default: null },
})

defineEmits(['click'])

const variants = {
  primary: 'bg-primary text-white hover:bg-primary-strong border border-transparent',
  secondary: 'bg-surface text-text-default border border-border-default hover:bg-surface-raised',
  ghost: 'bg-transparent text-text-default hover:bg-surface-raised border border-transparent',
  danger: 'bg-danger-strong text-white hover:opacity-90 border border-transparent',
  accent: 'bg-accent text-primary-strong hover:brightness-95 border border-transparent',
}

const sizes = {
  sm: 'px-3 py-1.5 text-xs rounded-lg',
  md: 'px-4 py-2 text-sm rounded-xl',
  lg: 'px-5 py-2.5 text-base rounded-xl',
}

const classes = computed(() => [
  'inline-flex items-center justify-center gap-2 font-medium transition-colors outline-none focus:ring-2 focus:ring-focus-ring/40 disabled:opacity-60 disabled:cursor-not-allowed',
  variants[props.variant] || variants.primary,
  sizes[props.size] || sizes.md,
])
</script>

<template>
  <NuxtLink
    v-if="as === 'NuxtLink'"
    :to="to"
    :class="classes"
    @click="$emit('click', $event)"
  >
    <svg
      v-if="loading"
      class="animate-spin h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
    <slot />
  </NuxtLink>
  <a
    v-else-if="as === 'a'"
    :href="typeof to === 'string' ? to : undefined"
    :class="classes"
    @click="$emit('click', $event)"
  >
    <svg
      v-if="loading"
      class="animate-spin h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
    <slot />
  </a>
  <button
    v-else
    :type="type"
    :disabled="disabled || loading"
    :class="classes"
    @click="$emit('click', $event)"
  >
    <svg
      v-if="loading"
      class="animate-spin h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
    <slot />
  </button>
</template>
