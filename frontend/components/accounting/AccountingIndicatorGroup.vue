<script setup>
import { computed, ref, useId } from 'vue'

const props = defineProps({
  /** Number of columns used once the complete indicator set is visible. */
  columns: {
    type: Number,
    default: 3,
    validator: (value) => [1, 2, 3, 4, 5, 6, 7].includes(value),
  },
  /** Keeps the disclosure out of the accessibility tree when there is no remainder. */
  secondaryCount: { type: Number, default: 0 },
})

const isExpanded = ref(false)
const disclosureId = `${useId()}-secondary-indicators`

const landscapeColumns = {
  1: 'panel-landscape:grid-cols-1',
  2: 'panel-landscape:grid-cols-2',
  3: 'panel-landscape:grid-cols-3',
  4: 'panel-landscape:grid-cols-4',
  5: 'panel-landscape:grid-cols-5',
  6: 'panel-landscape:grid-cols-6',
  7: 'panel-landscape:grid-cols-7',
}

const gridClass = computed(() => landscapeColumns[props.columns] || landscapeColumns[3])
const secondaryClass = computed(() => (
  isExpanded.value ? 'contents' : 'hidden panel-landscape:contents'
))
</script>

<template>
  <section class="mb-6" aria-label="Indicadores contables">
    <div
      class="grid grid-cols-1 gap-3 panel-portrait:grid-cols-2"
      :class="gridClass"
      data-testid="accounting-indicator-group"
    >
      <slot name="primary" />
      <div
        v-if="secondaryCount > 0"
        :id="disclosureId"
        :class="secondaryClass"
        data-testid="accounting-secondary-indicators"
      >
        <slot name="secondary" />
      </div>
    </div>

    <BaseButton
      v-if="secondaryCount > 0"
      variant="ghost"
      size="sm"
      class="mt-3 w-full panel-landscape:hidden"
      :aria-expanded="isExpanded ? 'true' : 'false'"
      :aria-controls="disclosureId"
      data-testid="accounting-indicators-toggle"
      @click="isExpanded = !isExpanded"
    >
      {{ isExpanded ? 'Ocultar indicadores' : `Ver todos los indicadores (${secondaryCount})` }}
      <BaseActionIcon :action="isExpanded ? 'collapse' : 'expand'" />
    </BaseButton>
  </section>
</template>
