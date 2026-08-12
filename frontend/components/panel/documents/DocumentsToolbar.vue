<script setup>
import DocumentSearchInput from '~/components/panel/documents/DocumentSearchInput.vue'

defineProps({
  search: { type: String, default: '' },
  viewMode: { type: String, default: 'list' },
  scope: { type: String, default: 'active' },
  // La búsqueda recorre los dos estados a propósito, así que el control queda
  // inerte mientras hay consulta: dejarlo activo sería ofrecer un filtro que
  // no filtra.
  scopeLocked: { type: Boolean, default: false },
})

const emit = defineEmits(['update:search', 'update:viewMode', 'update:scope'])

const VIEW_OPTIONS = [
  { value: 'list', label: 'Lista', testId: 'doc-view-list' },
  { value: 'grid', label: 'Galería', testId: 'doc-view-grid' },
]

const SCOPE_OPTIONS = [
  { value: 'all', label: 'Todos', testId: 'doc-state-all' },
  { value: 'active', label: 'Solo activos', testId: 'doc-state-active' },
  { value: 'archived', label: 'Solo archivados', testId: 'doc-state-archived' },
]
</script>

<template>
  <div class="flex flex-wrap items-center gap-3">
    <DocumentSearchInput
      :model-value="search"
      class="flex-1 min-w-[12rem]"
      @update:model-value="emit('update:search', $event)"
    />
    <!-- Visible también en móvil, al revés que el toggle de vista: cambia QUÉ
         se ve, no CÓMO. -->
    <BaseSegmented
      :model-value="scope"
      :options="SCOPE_OPTIONS"
      size="sm"
      class="flex-shrink-0"
      data-testid="doc-state-filter"
      aria-label="Estado de los documentos"
      :disabled="scopeLocked"
      :title="scopeLocked ? 'La búsqueda recorre activos y archivados' : undefined"
      @update:model-value="emit('update:scope', $event)"
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
