<script setup>
import BaseActionButton from '~/components/base/BaseActionButton.vue'
import BaseButton from '~/components/base/BaseButton.vue'

defineProps({
  spaceLabel: { type: String, required: true },
  stepIndex: { type: Number, required: true },
  stepCount: { type: Number, required: true },
  hasPrevious: { type: Boolean, default: false },
  hasNext: { type: Boolean, default: false },
})

defineEmits(['previous', 'next', 'stop'])
</script>

<template>
  <section
    class="rounded-2xl border border-primary/20 bg-primary-soft p-4"
    aria-label="Recorrido guiado"
    data-testid="view-explorer-tour-controls"
  >
    <div class="flex flex-col gap-3 panel-portrait:flex-row panel-portrait:items-center panel-portrait:justify-between">
      <div>
        <p class="text-[10px] font-semibold uppercase tracking-widest text-text-brand">Recorrido guiado</p>
        <p class="mt-1 text-sm font-medium text-text-default">{{ spaceLabel }}</p>
        <p class="mt-1 text-xs text-text-muted">Paso {{ stepIndex + 1 }} de {{ stepCount }}</p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <BaseActionButton
          v-if="hasPrevious"
          action="previous"
          label="Paso anterior"
          data-testid="view-explorer-tour-previous"
          @click="$emit('previous')"
        />
        <BaseButton
          v-if="hasNext"
          variant="primary"
          size="sm"
          data-testid="view-explorer-tour-next"
          @click="$emit('next')"
        >
          Siguiente
        </BaseButton>
        <BaseButton
          v-else
          variant="primary"
          size="sm"
          data-testid="view-explorer-tour-finish"
          @click="$emit('stop')"
        >
          Terminar recorrido
        </BaseButton>
        <BaseButton variant="ghost" size="sm" data-testid="view-explorer-tour-stop" @click="$emit('stop')">
          Salir
        </BaseButton>
      </div>
    </div>

    <div class="mt-3 h-1.5 overflow-hidden rounded-full bg-surface" aria-hidden="true">
      <div
        class="h-full rounded-full bg-primary transition-[width] duration-300 motion-reduce:transition-none"
        :style="{ width: `${((stepIndex + 1) / stepCount) * 100}%` }"
      />
    </div>
    <p class="sr-only" role="status" aria-live="polite">
      {{ spaceLabel }}. Paso {{ stepIndex + 1 }} de {{ stepCount }}.
    </p>
  </section>
</template>
