<template>
  <a
    :href="previewUrl"
    target="_blank"
    rel="noopener noreferrer"
    class="inline-flex items-center gap-2 px-4 py-2 text-sm text-emerald-600
           hover:text-emerald-700 border border-emerald-200 rounded-xl
           hover:bg-emerald-50 transition-colors"
  >
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
    Preview
  </a>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  uuid: {
    type: String,
    required: true,
  },
});

const previewUrl = computed(() => `/proposal/${props.uuid}`);
</script>
