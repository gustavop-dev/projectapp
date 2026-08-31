<template>
  <div class="fixed bottom-6 right-6 z-50">
    <BaseActionButton
      action="refresh"
      variant="primary"
      class="flex h-12 w-12 items-center justify-center rounded-full shadow-lg transition-all hover:scale-105 hover:shadow-xl disabled:opacity-50"
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
