<template>
  <div
    class="flex flex-wrap items-center gap-2 mb-4"
    role="tablist"
    aria-label="Módulo de negocio"
  >
    <!-- design-tokens: allow-raw-button -->
    <button
      v-for="module in modules"
      :key="module.id"
      type="button"
      role="tab"
      :aria-selected="module.id === modelValue"
      :data-testid="`clients-module-${module.id}`"
      :class="[
        'px-4 py-2 rounded-xl text-sm font-medium transition-colors',
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
 * It wraps instead of scrolling, so no module is ever cut off (there are seven,
 * all short). The overflow rule matters at level 2, where the set grows.
 */
import { CLIENT_MODULES } from '~/constants/clientFilters';

defineProps({
  modelValue: { type: String, default: 'all' },
  modules: { type: Array, default: () => CLIENT_MODULES },
});

const emit = defineEmits(['update:modelValue']);
</script>
