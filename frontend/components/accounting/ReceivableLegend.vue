<template>
  <BaseTooltip
    position="bottom"
    floating
    min-width="min-w-[280px] panel-portrait:min-w-[420px]"
    width="max-w-xl"
  >
    <template #trigger="{ tooltipId }">
      <BaseButton
        type="button"
        variant="ghost"
        size="sm"
        icon-only
        aria-label="Explicar estados de cobro"
        :aria-describedby="tooltipId"
        data-testid="receivable-legend-trigger"
      >
        <InformationCircleIcon class="h-5 w-5" aria-hidden="true" />
      </BaseButton>
    </template>
    <div class="space-y-2 text-left">
      <p class="font-semibold">Semáforo de cobro</p>
      <p v-for="status in RECEIVABLE_CONFIDENCE" :key="status.value">
        <span class="font-semibold">{{ status.shortLabel }}:</span>
        {{ status.label }}.
      </p>
      <p>
        “Sin clasificar” mantiene el ingreso seleccionado, pero no suma en la
        tarjeta. Sólo los seleccionados en verde forman el valor de “Pendiente por cobrar”.
      </p>
    </div>
  </BaseTooltip>
</template>

<script setup>
import { InformationCircleIcon } from '@heroicons/vue/24/outline';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseTooltip from '~/components/base/BaseTooltip.vue';
import { RECEIVABLE_CONFIDENCE } from '~/utils/receivables';
</script>
