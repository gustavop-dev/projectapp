<script setup>
/**
 * Insignia de «esta carpeta guarda archivados».
 *
 * Restaurar un elemento reabre sólo la cadena de carpetas que lo contiene, así
 * que una carpeta puede quedar con contenido activo y archivado a la vez. Sin
 * esta señal ese contenido es invisible: no está en la lista de la carpeta ni
 * cuenta en su contador.
 *
 * Un solo componente para las tres superficies (panel lateral, fila de tabla y
 * tarjeta del grid) para que el indicador no se bifurque.
 *
 * `BaseTooltip` llega por el auto-import de Nuxt, igual que en el resto del
 * módulo: importarlo a mano gana contra los stubs de los specs.
 */
defineProps({
  count: { type: Number, required: true },
  folderName: { type: String, default: '' },
})

const emit = defineEmits(['view'])
</script>

<template>
  <!-- El tooltip por defecto mide 260px+, inservible en el panel lateral. -->
  <BaseTooltip position="top" width="max-w-xs" min-width="min-w-0">
    <template #trigger>
      <!-- design-tokens: allow-raw-button — insignia inline, no una acción de formulario -->
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-full bg-surface-raised px-1.5 py-0.5
               text-2xs font-medium text-text-muted hover:text-text-default
               outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/40"
        data-testid="folder-archived-badge"
        :aria-label="`Ver ${count} elemento(s) archivado(s) de ${folderName}`"
        @click.stop="emit('view')"
      >
        <svg class="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
        </svg>
        {{ count }}
      </button>
    </template>
    Contiene {{ count }} elemento(s) archivado(s). Clic para verlos.
  </BaseTooltip>
</template>
