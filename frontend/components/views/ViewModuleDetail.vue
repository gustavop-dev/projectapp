<script setup>
import { computed } from 'vue'
import BaseBadge from '~/components/base/BaseBadge.vue'
import {
  getViewCopyReference,
  groupSectionViews,
  isOpenableViewUrl,
} from '~/config/viewCatalog'
import { findCapabilityNode } from '~/config/viewCapabilityCatalog'
import { viewTypeLabelMap, viewAudienceLabelMap } from '~/constants/viewMapFilterOptions'
import { useClipboardFeedback } from '~/composables/useClipboardFeedback'
import { usePanelNotify } from '~/composables/usePanelNotify'
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
const operationalNode = computed(() => findCapabilityNode(props.section.id))

const notify = usePanelNotify()
const clipboardFeedback = useClipboardFeedback()

async function copyReference(view) {
  const text = getViewCopyReference(props.section.label, view)
  await clipboardFeedback.copyText({
    key: view.url,
    text,
    successLabel: 'Copiado: referencia',
    errorLabel: 'No se pudo copiar la referencia',
    onError: () => notify.error({
      title: 'No se pudo copiar la referencia',
      detail: 'Tu navegador bloqueó el acceso al portapapeles.',
    }),
  })
}

function copyFeedback(view) {
  return clipboardFeedback.feedbackFor(view.url)
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
        <BaseActionIcon action="back" />
        Módulos
      </button>
      <span class="text-text-subtle">/</span>
      <span class="font-medium text-text-default">{{ operationalNode?.label || section.label }}</span>
    </nav>

    <header class="mb-6 flex items-start gap-4 rounded-xl border border-border-muted bg-surface p-5 shadow-sm">
      <span class="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-primary-soft text-text-brand">
        <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" :d="iconPath" />
        </svg>
      </span>
      <div>
        <p class="text-[10px] font-semibold uppercase tracking-widest text-text-subtle">Módulo</p>
        <h2 class="mt-1 text-lg font-light text-text-default">{{ operationalNode?.label || section.label }}</h2>
        <p class="mt-1 text-sm text-text-muted">{{ operationalNode?.summary || section.description }}</p>
        <p v-if="operationalNode?.value" class="mt-2 max-w-3xl text-sm leading-6 text-text-default">
          {{ operationalNode.value }}
        </p>
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
                <BaseActionButton
                  v-if="isOpenableViewUrl(view.url)"
                  action="open-external"
                  :label="`Abrir ${view.url} en una nueva pestaña`"
                  as="a"
                  :to="view.url"
                  target="_blank"
                  rel="noopener"
                  class="text-text-subtle hover:text-text-brand"
                />
                <BaseActionButton
                  action="copy"
                  :label="copyFeedback(view).label || 'Copiar referencia'"
                  :status-label="copyFeedback(view).label"
                  :status-tone="copyFeedback(view).tone"
                  class="text-text-subtle hover:text-text-brand"
                  @click="copyReference(view)"
                />
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
