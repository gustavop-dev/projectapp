<script setup>
/**
 * El enlace primario de una fila de listado: el título que ES la dirección del
 * detalle.
 *
 * Concentra cuatro cosas que por separado se olvidan:
 *  - `draggable="false"`: un <a> es arrastrable por defecto y su arrastre nativo
 *    (la URL) le gana al `dragstart` de la fila. Sin esto, mover un documento a
 *    otra carpeta agarrándolo del título deja de funcionar.
 *  - `@click.stop`: el atajo de click de la fila no debe volver a navegar cuando
 *    el click ya lo atendió el enlace.
 *  - el anillo de foco: la fila se recorre con Tab y tiene que verse.
 *  - `stretch`: agranda el área sensible a TODA la celda contenedora, que es lo
 *    que hace cómodo el click plano. Se estira contra la celda — que debe llevar
 *    `relative` — y nunca contra el <tr>: sobre la fila entera taparía el
 *    checkbox, el kebab, el select de estado y los tooltips.
 *
 * Sin `to` degrada a <span>: una fila sin destino no finge tener uno.
 */
import { computed } from 'vue'

const props = defineProps({
  /** Destino ya pasado por `useLocalePath()`. `null` ⇒ no hay detalle. */
  to: { type: [String, Object], default: null },
  /**
   * Cubrir toda la celda contenedora, que debe declarar `relative`.
   * No hace nada sin `to`: no se finge un área sensible que no lleva a ningún lado.
   */
  stretch: { type: Boolean, default: false },
})

const classes = computed(() => [
  'rounded outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/40',
  props.stretch && props.to ? "after:content-[''] after:absolute after:inset-0" : '',
])
</script>

<template>
  <component
    :is="to ? 'NuxtLink' : 'span'"
    :to="to || undefined"
    :draggable="to ? 'false' : undefined"
    :class="classes"
    @click.stop
  >
    <slot />
  </component>
</template>
