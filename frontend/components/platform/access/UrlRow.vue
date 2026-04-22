<template>
  <div class="flex items-center justify-between gap-3">
    <span class="text-xs font-medium text-green-light">{{ label }}</span>
    <a
      v-if="url"
      :href="url"
      target="_blank"
      rel="noopener noreferrer"
      class="inline-flex min-w-0 items-center gap-1 truncate text-xs font-medium text-esmerald transition hover:underline dark:text-lemon"
      :title="url"
    >
      <span class="truncate">{{ displayUrl }}</span>
      <svg class="h-3 w-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3" />
      </svg>
    </a>
    <span v-else class="text-xs italic text-green-light/50">—</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  url: { type: String, default: '' },
})

const displayUrl = computed(() => {
  if (!props.url) return ''
  try {
    return new URL(props.url).host
  } catch {
    return props.url
  }
})
</script>
