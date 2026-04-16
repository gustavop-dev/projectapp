<template>
  <span
    class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
    :class="meta.cls"
  >{{ meta.label }}</span>
</template>

<script setup>
import { computed } from 'vue';
import { STATUS_META } from '~/stores/diagnostics_constants';

const props = defineProps({
  status: { type: String, required: true },
});

const FALLBACK = { label: '—', cls: 'bg-gray-100 text-gray-700' };
const meta = computed(() => STATUS_META[props.status] || { ...FALLBACK, label: props.status });
</script>
