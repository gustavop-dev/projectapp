<template>
  <div
    v-if="folder"
    class="flex flex-wrap items-center justify-between gap-3 mb-4"
    data-testid="folder-header"
  >
    <div class="min-w-0">
      <h2
        class="text-lg font-semibold text-text-default truncate"
        data-testid="folder-header-name"
      >{{ folder.name }}</h2>
      <div
        v-if="folder.client_display_name || folder.project_name"
        class="flex flex-wrap items-center gap-2 mt-1"
      >
        <span
          v-if="folder.client_display_name"
          class="text-xs px-2 py-0.5 rounded-full bg-info-soft text-info-strong font-medium"
          data-testid="folder-header-client"
        >{{ folder.client_display_name }}</span>
        <span
          v-if="folder.project_name"
          class="text-xs px-2 py-0.5 rounded-full bg-surface-raised text-text-muted font-medium"
          data-testid="folder-header-project"
        >{{ folder.project_name }}</span>
      </div>
    </div>

    <BaseButton
      variant="secondary"
      size="sm"
      data-testid="folder-header-edit"
      @click="$emit('edit', folder)"
    >
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
      <span>Editar carpeta</span>
    </BaseButton>
  </div>
</template>

<script setup>
/**
 * La cabecera de la carpeta en la que se está parado.
 *
 * Dice tres cosas que antes no estaban en ningún lado del listado: cómo se
 * llama la carpeta abierta (el breadcrumb la pintaba como un span pelado), de
 * qué cliente y proyecto es, y por dónde se edita — aquí, que es donde uno
 * está cuando surge la necesidad de cambiarle algo.
 *
 * Sin carpeta activa no se renderiza: en la raíz del gestor no hay nada que
 * encabezar.
 */
defineProps({
  folder: { type: Object, default: null },
});

defineEmits(['edit']);
</script>
