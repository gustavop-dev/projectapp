<template>
  <button
    type="button"
    class="fixed bottom-6 right-6 z-50 w-12 h-12 rounded-full bg-primary hover:bg-primary text-white shadow-lg transition-all hover:shadow-xl hover:scale-105 disabled:opacity-50 flex items-center justify-center"
    :disabled="loading"
    :title="loading ? 'Actualizando...' : 'Actualizar datos'"
    :aria-label="loading ? 'Actualizando datos' : 'Actualizar datos'"
    @click="$emit('click')"
  >
    <svg class="w-5 h-5" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  </button>
</template>

<script setup>
defineProps({
  loading: { type: Boolean, default: false },
});

defineEmits(['click']);
</script>
