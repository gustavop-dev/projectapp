<template>
  <div class="flex items-baseline gap-3 mb-3">
    <span v-if="index" class="text-sm font-mono text-emerald-600">{{ index }}</span>
    <h2 class="m-0 text-2xl font-semibold text-gray-900">{{ title || fallback }}</h2>
  </div>
</template>

<script setup>
defineProps({
  index: { type: String, default: '' },
  title: { type: String, default: '' },
  fallback: { type: String, default: '' },
});
</script>
