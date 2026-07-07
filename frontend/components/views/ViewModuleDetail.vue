<script setup>
import { computed, ref } from 'vue'
import BaseBadge from '~/components/base/BaseBadge.vue'
import {
  getViewCopyReference,
  groupSectionViews,
  isOpenableViewUrl,
} from '~/config/viewCatalog'
import { viewTypeLabelMap, viewAudienceLabelMap } from '~/constants/viewMapFilterOptions'
import {
  viewTypeBadgeVariantMap,
  viewAudienceBadgeVariantMap,
  viewModuleIconPathMap,
  viewModuleIconFallbackPath,
} from '~/constants/viewBadgeMaps'

const props = defineProps({
  section: { type: Object, required: true },
})

const emit = defineEmits(['back'])

const iconPath = computed(
  () => viewModuleIconPathMap[props.section.id] || viewModuleIconFallbackPath,
)

const groups = computed(() => groupSectionViews(props.section))

const copiedKey = ref(null)
let copyTimer = null

function copyReference(view) {
  const text = getViewCopyReference(props.section.label, view)
  navigator.clipboard.writeText(text).then(() => {
    clearTimeout(copyTimer)
    copiedKey.value = view.url
    copyTimer = setTimeout(() => { copiedKey.value = null }, 1500)
  })
}
</script>

<template>
  <div data-testid="view-module-detail">
    <nav class="mb-4 flex items-center gap-2 text-sm" aria-label="Breadcrumb">
      <button
        type="button"
        class="flex items-center gap-1.5 text-text-muted transition-colors hover:text-text-brand"
        data-testid="view-module-back"
        @click="emit('back')"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Módulos
      </button>
      <span class="text-text-subtle">/</span>
      <span class="font-medium text-text-default">{{ section.label }}</span>
    </nav>

    <header class="mb-6 flex items-start gap-4 rounded-xl border border-border-muted bg-surface p-5 shadow-sm">
      <span class="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-primary-soft text-text-brand">
        <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" :d="iconPath" />
        </svg>
      </span>
      <div>
        <h2 class="text-lg font-light text-text-default">{{ section.label }}</h2>
        <p class="mt-1 text-sm text-text-muted">{{ section.description }}</p>
        <p class="mt-2 text-xs text-text-subtle">
          {{ section.views.length }} vistas · {{ groups.length }} {{ groups.length === 1 ? 'sub-módulo' : 'sub-módulos' }}
        </p>
      </div>
    </header>

    <div class="grid gap-4 lg:grid-cols-2">
      <section
        v-for="group in groups"
        :key="group.group"
        class="flex flex-col overflow-hidden rounded-xl border border-border-muted bg-surface shadow-sm"
      >
        <h3 class="flex items-center justify-between border-b border-border-muted px-4 py-3 text-sm font-medium text-text-default">
          {{ group.group }}
          <span class="rounded-full bg-primary-soft px-2.5 py-0.5 text-xs font-medium text-text-brand">
            {{ group.views.length }}
          </span>
        </h3>

        <ul class="divide-y divide-border-muted">
          <li
            v-for="view in group.views"
            :key="`${view.url}-${view.file}`"
            class="px-4 py-3"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="text-sm font-medium text-text-default">{{ view.label }}</p>
                <p class="mt-0.5 text-xs text-text-muted">{{ view.reference }}</p>
                <p v-if="view.notes" class="mt-1 text-xs leading-5 text-warning-strong">{{ view.notes }}</p>
              </div>

              <div class="flex flex-shrink-0 items-center gap-0.5">
                <a
                  v-if="isOpenableViewUrl(view.url)"
                  :href="view.url"
                  target="_blank"
                  rel="noopener"
                  class="rounded-lg p-1.5 text-text-subtle transition-colors hover:bg-surface-raised hover:text-text-brand"
                  :title="`Abrir ${view.url} en una nueva pestaña`"
                >
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                  </svg>
                </a>
                <button
                  type="button"
                  class="rounded-lg p-1.5 text-text-subtle transition-colors hover:bg-surface-raised hover:text-text-brand"
                  :title="copiedKey === view.url ? 'Copiado!' : 'Copiar referencia'"
                  @click="copyReference(view)"
                >
                  <svg v-if="copiedKey === view.url" class="h-4 w-4 text-success-strong" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                  </svg>
                </button>
              </div>
            </div>

            <div class="mt-2 flex flex-wrap items-center gap-1.5">
              <BaseBadge :variant="viewTypeBadgeVariantMap[view.viewType] || 'neutral'" size="sm">
                {{ viewTypeLabelMap[view.viewType] || view.viewType }}
              </BaseBadge>
              <BaseBadge :variant="viewAudienceBadgeVariantMap[view.audience] || 'neutral'" size="sm">
                {{ viewAudienceLabelMap[view.audience] || view.audience }}
              </BaseBadge>
              <code class="break-all font-mono text-xs text-text-brand">{{ view.url }}</code>
            </div>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
