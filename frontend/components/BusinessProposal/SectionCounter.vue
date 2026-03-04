<template>
  <div
    class="section-counter fixed top-4 right-4 z-40
           px-3 py-1.5 rounded-full bg-white/80 backdrop-blur-sm
           shadow-md border border-gray-100 select-none"
  >
    <span class="text-emerald-600 font-medium text-sm tabular-nums">
      {{ current }}
    </span>
    <span class="text-gray-300 mx-1 text-sm">/</span>
    <span class="text-gray-400 text-sm tabular-nums">{{ total }}</span>
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
