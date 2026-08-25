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
    <BaseActionIcon action="filter" />
    Filtros
    <span
      v-if="count > 0"
      class="inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold"
      :class="open ? 'bg-surface text-primary' : 'bg-primary text-white'"
    >{{ count }}</span>
  </button>
</template>
