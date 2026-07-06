<script setup>
import { computed } from 'vue'
import { groupSectionViews } from '~/config/viewCatalog'
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
  <button
    type="button"
    class="group flex h-full flex-col rounded-xl border border-border-muted bg-surface p-5 text-left shadow-sm outline-none transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md focus-visible:ring-2 focus-visible:ring-focus-ring/50"
    :data-testid="`view-module-card-${section.id}`"
    @click="emit('select', section.id)"
  >
    <div class="flex items-start gap-3">
      <span class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-primary-soft text-text-brand">
        <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" :d="iconPath" />
        </svg>
      </span>
      <div class="min-w-0 flex-1">
        <h3 class="text-sm font-medium text-text-default">{{ section.label }}</h3>
        <p class="mt-1 text-xs leading-5 text-text-muted line-clamp-2">{{ section.description }}</p>
      </div>
      <svg class="h-4 w-4 flex-shrink-0 text-text-subtle opacity-0 transition-opacity group-hover:opacity-100" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
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
  </button>
</template>
