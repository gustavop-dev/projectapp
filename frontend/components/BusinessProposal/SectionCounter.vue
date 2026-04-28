<template>
  <div
    data-testid="section-counter"
    class="section-counter fixed top-14 sm:top-4 right-4 z-40
           px-3 py-1.5 rounded-full bg-white/80 backdrop-blur-sm
           shadow-md border border-border-muted select-none"
  >
    <span class="text-text-brand font-medium text-sm tabular-nums">
      {{ current }}
    </span>
    <span class="text-text-subtle mx-1 text-sm">/</span>
    <span class="text-text-subtle text-sm tabular-nums">{{ total }}</span>
  </div>
</template>

<script setup>
defineProps({
  current: {
    type: Number,
    default: 1,
  },
  total: {
    type: Number,
    default: 1,
  },
});
</script>
