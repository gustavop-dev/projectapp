<script setup>
import { computed, useAttrs, watchEffect } from 'vue'
import { oneOf } from './propValidators'

const props = defineProps({
  // One variant per kind of action — see the action→variant table in
  // components/base/README.md. Anything destructive uses danger (confirmed,
  // e.g. a modal footer) or danger-ghost (inline, e.g. a row's trash icon).
  variant: {
    type: String,
    default: 'primary',
    validator: oneOf(['primary', 'secondary', 'ghost', 'danger', 'danger-ghost', 'link', 'accent']),
  },
  size: { type: String, default: 'md', validator: oneOf(['sm', 'md', 'lg']) },
  type: { type: String, default: 'button' },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  iconOnly: { type: Boolean, default: false },    // square padding for icon buttons
  as: { type: String, default: 'button' },        // button | a | NuxtLink
  to: { type: [String, Object], default: null },
})

defineEmits(['click'])

const attrs = useAttrs()

const variants = {
  primary: 'bg-primary text-on-primary hover:bg-primary-strong border border-transparent',
  secondary: 'bg-surface text-text-default border border-border-default hover:bg-surface-raised',
  ghost: 'bg-transparent text-text-default hover:bg-surface-raised border border-transparent',
  danger: 'bg-danger-strong text-on-danger hover:opacity-90 border border-transparent',
  'danger-ghost': 'bg-transparent text-danger-strong hover:bg-danger-soft border border-transparent',
  link: 'bg-transparent text-text-brand hover:underline',
  accent: 'bg-accent text-primary-strong hover:brightness-95 border border-transparent',
}

const sizes = {
  sm: 'px-3 py-1.5 text-xs rounded-lg',
  md: 'px-4 py-2 text-sm rounded-xl',
  lg: 'px-5 py-2.5 text-base rounded-xl',
}

// Icon buttons get square padding so the glyph stays centred instead of
// sitting in a wide pill.
const iconSizes = {
  sm: 'p-1.5 text-xs rounded-lg',
  md: 'p-2 text-sm rounded-lg',
  lg: 'p-2.5 text-base rounded-xl',
}

// `link` renders as inline text: no padding, no radius, just the text size.
const linkSizes = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
}

const sizeClasses = computed(() => {
  if (props.variant === 'link') return linkSizes[props.size] || linkSizes.md
  if (props.iconOnly) return iconSizes[props.size] || iconSizes.md
  return sizes[props.size] || sizes.md
})

const classes = computed(() => [
  'base-button',
  props.iconOnly && 'base-button--icon',
  props.variant === 'link' && 'base-button--link',
  'inline-flex items-center justify-center gap-2 font-medium transition-colors outline-none focus:ring-2 focus:ring-focus-ring/40 disabled:opacity-60 disabled:cursor-not-allowed',
  variants[props.variant] || variants.primary,
  sizeClasses.value,
])

// An icon-only button has no text for a screen reader to announce, so the
// aria-label is the only thing naming it.
if (process.env.NODE_ENV !== 'production') {
  watchEffect(() => {
    if (props.iconOnly && !attrs['aria-label'] && !attrs['aria-labelledby']) {
      console.warn('[BaseButton] iconOnly buttons need an aria-label to be announced by screen readers.')
    }
  })
}
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

<style scoped>
/* The visual size may stay compact with a mouse; coarse pointers still get
 * the canonical 44px hit area without every caller remembering it. */
@media (pointer: coarse) {
  .base-button:not(.base-button--link) {
    min-height: 44px;
  }

  .base-button--icon {
    min-width: 44px;
  }
}
</style>
