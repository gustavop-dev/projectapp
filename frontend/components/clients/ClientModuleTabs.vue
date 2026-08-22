<template>
  <div
    class="flex flex-wrap items-center gap-2 mb-4"
    role="tablist"
    aria-label="Módulo de negocio"
  >
    <!--
      Móvil: los siete módulos colapsan en un selector, el mismo control con el
      que colapsa la navegación del contable. Envolviendo ocupaban tres filas de
      pastillas antes de que empezara el contenido.

      El selector y las pastillas viven en el MISMO contenedor plano, no en dos
      bloques hermanos, para que el botón de `trailing` se renderice una sola vez
      y siga visible en las dos anchuras: duplicarlo repetiría su data-testid y
      rompería el modo estricto de Playwright.
    -->
    <BaseMobileTabSelect
      class="flex-1"
      variant="nav"
      test-id="clients-module-select"
      aria-label="Módulo de negocio"
      :model-value="modelValue"
      :options="selectOptions"
      @update:model-value="emit('update:modelValue', $event)"
    />

    <!-- design-tokens: allow-raw-button -->
    <button
      v-for="module in modules"
      :key="module.id"
      type="button"
      role="tab"
      :aria-selected="module.id === modelValue"
      :data-testid="`clients-module-${module.id}`"
      :class="[
        'hidden panel-landscape:inline-flex px-4 py-2 rounded-xl text-sm font-medium transition-colors',
        module.id === modelValue
          ? 'bg-primary text-white'
          : 'bg-surface-raised text-text-muted hover:bg-border-muted',
      ]"
      @click="emit('update:modelValue', module.id)"
    >
      {{ module.name }}
    </button>

    <slot name="trailing" />
  </div>
</template>

<script setup>
/**
 * Level 1 of the /panel/clients filters: the business module.
 *
 * Picking one does not narrow the list — it decides which subfilters level 2
 * offers, which is what lets a module hold both a cut and its complement ("Con
 * hosting cobrado" next to "Sin hosting").
 *
 * That is also why these carry no match count: with no narrowing of their own,
 * every one would show the same total and the number would be noise. The counts
 * live where a cut actually happens — the subfilters and the status selector.
 *
 * Solid pills against the underlined tabs of level 2: the two rows must read as
 * a hierarchy, not as two lists of the same rank.
 *
 * On desktop it wraps instead of scrolling, so no module is ever cut off (there
 * are seven, all short). The overflow rule matters at level 2, where the set
 * grows. Below `md` seven pills still cost three rows of chrome before any
 * content, so there they collapse into a selector instead.
 */
import { computed } from 'vue';
import { CLIENT_MODULES } from '~/constants/clientFilters';

const props = defineProps({
  modelValue: { type: String, default: 'all' },
  modules: { type: Array, default: () => CLIENT_MODULES },
});

const emit = defineEmits(['update:modelValue']);

// Una sola lista leída dos veces: el orden no puede divergir entre el
// desplegable de móvil y las pastillas de escritorio.
const selectOptions = computed(() =>
  props.modules.map((module) => ({ value: module.id, label: module.name })),
);
</script>
