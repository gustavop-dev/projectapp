<script setup>
import ViewModuleCard from '~/components/views/ViewModuleCard.vue'

defineProps({
  sections: { type: Array, required: true },
})

const emit = defineEmits(['select'])
</script>

<template>
  <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" data-testid="view-module-grid">
    <ViewModuleCard
      v-for="section in sections"
      :key="section.id"
      :section="section"
      @select="emit('select', $event)"
    />
  </div>
</template>
