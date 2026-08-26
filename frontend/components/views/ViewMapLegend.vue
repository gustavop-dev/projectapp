<script setup>
import BaseBadge from '~/components/base/BaseBadge.vue'
import { viewTypeOptions, viewAudienceOptions } from '~/constants/viewMapFilterOptions'
import {
  viewTypeBadgeVariantMap,
  viewAudienceBadgeVariantMap,
} from '~/constants/viewBadgeMaps'
</script>

<template>
  <details class="group mb-6 rounded-xl border border-border-muted bg-surface shadow-sm">
    <summary class="flex cursor-pointer select-none list-none items-center justify-between px-4 py-3 text-sm text-text-muted [&::-webkit-details-marker]:hidden">
      Leyenda de colores
      <BaseActionIcon action="expand" class="text-text-subtle transition-transform duration-300 group-open:rotate-180" />
    </summary>
    <div class="border-t border-border-muted px-4 py-3">
      <p class="mb-2 text-[10px] font-semibold uppercase tracking-widest text-text-subtle">Tipo de vista</p>
      <div class="flex flex-wrap gap-1.5">
        <BaseBadge
          v-for="option in viewTypeOptions"
          :key="option.value"
          :variant="viewTypeBadgeVariantMap[option.value] || 'neutral'"
          size="sm"
        >
          {{ option.label }}
        </BaseBadge>
      </div>
      <p class="mb-2 mt-4 text-[10px] font-semibold uppercase tracking-widest text-text-subtle">Audiencia</p>
      <div class="flex flex-wrap gap-1.5">
        <BaseBadge
          v-for="option in viewAudienceOptions"
          :key="option.value"
          :variant="viewAudienceBadgeVariantMap[option.value] || 'neutral'"
          size="sm"
        >
          {{ option.label }}
        </BaseBadge>
      </div>
    </div>
  </details>
</template>
