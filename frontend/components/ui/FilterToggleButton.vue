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
      ? 'bg-primary text-white border-primary'
      : 'bg-surface text-text-muted border-border-default hover:border-text-muted'"
  >
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
    </svg>
    Filtros
    <span
      v-if="count > 0"
      class="inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold"
      :class="open ? 'bg-surface text-primary' : 'bg-primary text-white'"
    >{{ count }}</span>
  </button>
</template>
