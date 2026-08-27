<template>
  <!--
    Sólo existe por debajo de `landscape` (1024px): el breakpoint vive acá y no en cada
    consumidor, que es lo que mantiene a las tres superficies (navegación del
    contable, BaseTabs y la tira de filtros guardados) colapsando en el mismo
    punto sin tener que acordarse de repetirlo.
  -->
  <div class="panel-landscape:hidden">
    <select
      :value="modelValue"
      :aria-label="ariaLabel"
      :data-testid="testId"
      class="min-h-11 w-full px-4 py-2.5 rounded-xl text-sm font-medium border
             appearance-none cursor-pointer outline-none
             focus:ring-2 focus:ring-focus-ring/30"
      :class="variant === 'nav'
        ? 'bg-primary text-white border-primary'
        : 'bg-input-bg text-input-text border-input-border focus:border-focus-ring'"
      :style="variant === 'nav' ? SELECT_ARROW_STYLE_INVERTED : SELECT_ARROW_STYLE"
      @change="$emit('update:modelValue', $event.target.value)"
    >
      <!--
        Color y fondo explícitos por opción, no heredados. En la variante `nav`
        el control es blanco sobre `bg-primary`, pero varios navegadores pintan
        la lista desplegada con el fondo del sistema y sí heredan el color del
        texto: sin esto, las opciones quedan blanco sobre blanco.
      -->
      <option
        v-for="option in options"
        :key="String(option.value)"
        :value="option.value"
        :disabled="option.disabled === true"
        :title="option.disabled === true ? option.disabledReason : undefined"
        class="bg-surface text-text-default"
      >
        {{ option.label }}
      </option>
    </select>
  </div>
</template>

<script setup>
/**
 * El `<select>` nativo con el que los controles de pestañas colapsan en móvil.
 *
 * Nativo y no un desplegable propio a propósito: resuelve gratis dos cosas que
 * un menú a mano tendría que reimplementar y mantener — marca la opción activa
 * al abrirse (por `:value`) y se cierra sin elegir nada con Escape o tocando
 * afuera, sin disparar `change`.
 *
 * Las dos variantes existen para separar dos controles que quedan contiguos y
 * hacen cosas distintas: `nav` cambia de sección (sólido, el mismo tratamiento
 * que lleva la pestaña activa en escritorio) y `filter` aplica un filtro
 * guardado (neutro, como cualquier campo de formulario). La distinción es de
 * peso visual porque un rótulo encima gastaría el alto que este control existe
 * para recuperar.
 */
import { SELECT_ARROW_STYLE, SELECT_ARROW_STYLE_INVERTED } from '~/utils/selectArrowStyle';
import { oneOf } from './propValidators';

defineProps({
  modelValue: { type: [String, Number], default: '' },
  // [{ value, label, disabled? }]
  options: { type: Array, required: true },
  // Obligatorio: es lo único que distingue los dos selectores contiguos para
  // quien no ve la diferencia de color.
  ariaLabel: { type: String, required: true },
  testId: { type: String, default: undefined },
  variant: { type: String, default: 'filter', validator: oneOf(['nav', 'filter']) },
});

defineEmits(['update:modelValue']);
</script>
