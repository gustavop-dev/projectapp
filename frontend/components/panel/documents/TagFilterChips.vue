<template>
  <div v-if="tags.length" class="flex flex-wrap items-center gap-2">
    <span class="text-xs font-medium text-text-muted mr-1">Etiquetas:</span>
    <button
      v-for="tag in tags"
      :key="tag.id"
      type="button"
      class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors"
      :class="chipClass(tag)"
      @click="$emit('toggle', tag.id)"
    >
      <span class="w-2 h-2 rounded-full" :class="tagDotClass(tag.color)"></span>
      {{ tag.name }}
    </button>
    <button
      v-if="activeIds.length"
      type="button"
      class="text-xs text-text-muted hover:text-text-default underline ml-1"
      @click="$emit('clear')"
    >
      Limpiar
    </button>
    <button
      type="button"
      class="ml-auto text-xs font-medium text-text-brand hover:text-text-brand"
      @click="$emit('manage')"
    >
      Gestionar etiquetas
    </button>
  </div>
  <div v-else class="flex items-center justify-between text-xs text-text-muted">
    <span>Aún no has creado etiquetas.</span>
    <button
      type="button"
      class="font-medium text-text-brand hover:text-text-brand"
      @click="$emit('manage')"
    >
      Crear la primera →
    </button>
  </div>
</template>

<script setup>
import { tagActiveClass, tagDotClass, TAG_IDLE_CHIP_CLASS } from '~/utils/documentTagColors.js';

const props = defineProps({
  tags: { type: Array, default: () => [] },
  activeIds: { type: Array, default: () => [] },
});
defineEmits(['toggle', 'clear', 'manage']);

function chipClass(tag) {
  return props.activeIds.includes(tag.id) ? tagActiveClass(tag.color) : TAG_IDLE_CHIP_CLASS;
}
</script>
