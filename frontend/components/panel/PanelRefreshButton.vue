<template>
  <div class="fixed bottom-6 right-6 z-50">
    <BaseActionButton
      action="refresh"
      class="w-12 h-12 rounded-full bg-primary hover:bg-primary text-white shadow-lg transition-all hover:shadow-xl hover:scale-105 disabled:opacity-50 flex items-center justify-center"
      :disabled="loading"
      :loading="loading"
      label="Actualizar datos"
      :status-label="loading ? 'Actualizando datos' : ''"
      @click="$emit('click')"
    />
  </div>
</template>

<script setup>
defineProps({
  loading: { type: Boolean, default: false },
});

defineEmits(['click']);
</script>
