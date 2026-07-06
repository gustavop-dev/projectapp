<script setup>
/**
 * Animated collapse/accordion body with reduced-motion support.
 *
 * Uses the CSS grid 0fr→1fr technique, so the content height never needs to
 * be measured in JS. The closed body is inert (unreachable by keyboard and
 * assistive tech). The TRIGGER stays in the consumer and must be a real
 * `<button :aria-expanded="open" :aria-controls="id">`.
 *
 * Usage:
 *   <button :aria-expanded="open" aria-controls="sec-1" @click="open = !open">…</button>
 *   <BaseCollapse id="sec-1" :open="open"> …body… </BaseCollapse>
 */
defineProps({
  open: { type: Boolean, default: false },
  id: { type: String, default: '' },
})
</script>

<template>
  <div
    :id="id || undefined"
    class="grid motion-safe:transition-[grid-template-rows] motion-safe:duration-base motion-safe:ease-out-soft"
    :class="open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'"
    :inert="!open || undefined"
    :aria-hidden="!open"
  >
    <div class="min-h-0 overflow-hidden">
      <slot />
    </div>
  </div>
</template>
