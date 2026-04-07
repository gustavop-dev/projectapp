<script setup lang="ts">
defineProps<{
  open: boolean
  count: number
}>()
</script>

<template>
  <button
    type="button"
    class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors border"
    :class="open
      ? 'bg-emerald-600 text-white border-emerald-600'
      : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'"
  >
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
    </svg>
    Filtros
    <span
      v-if="count > 0"
      class="inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold"
      :class="open ? 'bg-white text-emerald-600' : 'bg-emerald-600 text-white'"
    >{{ count }}</span>
  </button>
</template>
