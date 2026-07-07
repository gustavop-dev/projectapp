<script setup>
import { oneOf } from './propValidators'

/**
 * Loading placeholder that mirrors the shape of the content it replaces.
 * Pulse pauses under prefers-reduced-motion (motion-safe:animate-pulse,
 * same pattern as the accounting table skeletons).
 *
 * variant: line → text row; card → block/panel; circle → avatar/icon dot.
 * Size with normal utility classes (w-*, h-*) on the component.
 */
defineProps({
  variant: { type: String, default: 'line', validator: oneOf(['line', 'card', 'circle']) },
})

const shapes = {
  line: 'h-3 rounded',
  card: 'h-24 rounded-xl',
  circle: 'h-8 w-8 rounded-full',
}
</script>

<template>
  <div
    class="bg-surface-raised motion-safe:animate-pulse"
    :class="shapes[variant] || shapes.line"
    aria-hidden="true"
  />
</template>
