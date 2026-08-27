<script setup>
import { computed } from 'vue'
import { groupSectionViews } from '~/config/viewCatalog'
import { findCapabilityNode } from '~/config/viewCapabilityCatalog'
import { viewTypeLabelMap, viewAudienceLabelMap } from '~/constants/viewMapFilterOptions'
import {
  viewTypeBarClassMap,
  viewModuleIconPathMap,
  viewModuleIconFallbackPath,
} from '~/constants/viewBadgeMaps'

const props = defineProps({
  section: { type: Object, required: true },
})

const emit = defineEmits(['select'])

const iconPath = computed(
  () => viewModuleIconPathMap[props.section.id] || viewModuleIconFallbackPath,
)

const groups = computed(() => groupSectionViews(props.section))
const operationalNode = computed(() => findCapabilityNode(props.section.id))

const typeSegments = computed(() => {
  const counts = new Map()
  for (const view of props.section.views) {
    counts.set(view.viewType, (counts.get(view.viewType) || 0) + 1)
  }
  const total = props.section.views.length || 1
  return [...counts.entries()].map(([viewType, count]) => ({
    viewType,
    count,
    label: `${viewTypeLabelMap[viewType] || viewType}: ${count}`,
    barClass: viewTypeBarClassMap[viewType] || 'bg-text-subtle',
    width: `${(count / total) * 100}%`,
  }))
})

const audiences = computed(() => {
  const present = new Set(props.section.views.map((v) => v.audience))
  return [...present].map((a) => viewAudienceLabelMap[a] || a)
})
</script>

<template>
  <BaseButton variant="secondary" size="md" :data-testid="`view-module-card-${section.id}`" @click="emit('select', section.id)">
    <div class="flex items-start gap-3">
      <span class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-primary-soft text-text-brand">
        <!-- panel-action-icons: allow-content-glyph — identifies the module selected by this card. -->
        <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" :d="iconPath" />
        </svg>
      </span>
      <div class="min-w-0 flex-1">
        <p class="text-[10px] font-semibold uppercase tracking-widest text-text-subtle">Módulo</p>
        <h3 class="mt-0.5 text-sm font-medium text-text-default">{{ operationalNode?.label || section.label }}</h3>
        <p class="mt-1 text-xs leading-5 text-text-muted line-clamp-2">{{ operationalNode?.summary || section.description }}</p>
      </div>
      <BaseActionIcon action="forward" class="text-text-subtle opacity-0 transition-opacity group-hover:opacity-100" />
    </div>

    <div class="mt-4 flex items-baseline gap-4">
      <p>
        <strong class="text-2xl font-light text-text-brand">{{ section.views.length }}</strong>
        <span class="ml-1 text-xs text-text-muted">vistas</span>
      </p>
      <p class="text-xs text-text-subtle">
        {{ groups.length }} {{ groups.length === 1 ? 'sub-módulo' : 'sub-módulos' }}
      </p>
    </div>

    <div class="mt-3 flex h-1.5 w-full overflow-hidden rounded-full bg-surface-raised" aria-hidden="true">
      <span
        v-for="segment in typeSegments"
        :key="segment.viewType"
        class="h-full first:rounded-l-full last:rounded-r-full"
        :class="segment.barClass"
        :style="{ width: segment.width }"
        :title="segment.label"
      />
    </div>

    <p class="mt-auto pt-3 text-[11px] text-text-subtle">
      {{ audiences.join(' · ') }}
    </p>
    <p v-if="operationalNode?.value" class="mt-2 border-t border-border-muted pt-2 text-left text-[11px] leading-4 text-text-muted line-clamp-2">
      {{ operationalNode.value }}
    </p>
  </BaseButton>
</template>
