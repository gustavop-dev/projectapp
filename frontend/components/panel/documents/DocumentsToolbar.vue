<script setup>
import DocumentSearchInput from '~/components/panel/documents/DocumentSearchInput.vue'

defineProps({
  search: { type: String, default: '' },
  viewMode: { type: String, default: 'list' },
})

const emit = defineEmits(['update:search', 'update:viewMode'])

const VIEW_OPTIONS = [
  { value: 'list', label: 'Lista', testId: 'doc-view-list' },
  { value: 'grid', label: 'Galería', testId: 'doc-view-grid' },
]
</script>

<template>
  <div class="flex items-center gap-3">
    <DocumentSearchInput
      :model-value="search"
      class="flex-1 min-w-0"
      @update:model-value="emit('update:search', $event)"
    />
    <BaseSegmented
      :model-value="viewMode"
      :options="VIEW_OPTIONS"
      size="sm"
      class="hidden sm:inline-flex flex-shrink-0"
      aria-label="Modo de vista"
      @update:model-value="emit('update:viewMode', $event)"
    />
    <slot name="actions" />
  </div>
</template>
