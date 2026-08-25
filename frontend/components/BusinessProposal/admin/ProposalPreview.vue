<template>
  <a
    :href="previewUrl"
    target="_blank"
    rel="noopener noreferrer"
    class="inline-flex items-center gap-2 px-4 py-2 text-sm text-text-brand
           hover:text-text-brand border border-emerald-200 rounded-xl
           hover:bg-primary-soft transition-colors"
  >
    <BaseActionIcon action="view" />
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
