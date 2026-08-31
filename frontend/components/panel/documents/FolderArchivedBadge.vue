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
  <!-- El tooltip por defecto mide 260px+, inservible en el panel lateral. Al
       bajar el piso a min-w-0 hay que reponer w-max: el trigger es una pastilla
       de ~40px y, sin ancho máximo de contenido ni `floating`, el panel absoluto
       encoge contra ese ancestro y el texto se parte letra por letra. `floating`
       lo saca a <body>, donde el clamping al viewport de BaseTooltip lo acota. -->
  <BaseTooltip
    position="top"
    width="w-max max-w-xs"
    min-width="min-w-0"
    content-class="whitespace-normal [overflow-wrap:normal]"
    floating
  >
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
        <BaseActionIcon action="archive" />
        {{ count }}
      </button>
    </template>
    Contiene {{ count }} elemento(s) archivado(s). Clic para verlos.
  </BaseTooltip>
</template>
