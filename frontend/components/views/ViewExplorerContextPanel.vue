<script setup>
import { computed } from 'vue'
import BaseActionButton from '~/components/base/BaseActionButton.vue'
import BaseActionIcon from '~/components/base/BaseActionIcon.vue'
import BaseBadge from '~/components/base/BaseBadge.vue'
import BaseButton from '~/components/base/BaseButton.vue'
import SidebarIcon from '~/components/platform/SidebarIcon.vue'
import { isOpenableViewUrl } from '~/config/viewCatalog'
import { capitalizeFirst, joinEs } from '~/utils/spanishList'

const props = defineProps({
  node: { type: Object, required: true },
  technicalViews: { type: Array, default: () => [] },
  relatedViewCount: { type: Number, default: 0 },
  isPreviewing: { type: Boolean, default: false },
  isTourActive: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'start-tour'])

const actorNames = Object.freeze({
  team: 'equipo',
  client: 'cliente',
  visitor: 'visitante',
  prospect: 'prospecto',
})

const actorLabel = computed(() => {
  const labels = (props.node.actors || []).map((actor) => actorNames[actor] || actor)
  return capitalizeFirst(joinEs(labels))
})

const primaryChildren = computed(() => (props.node.children || []).filter((child) => !child.secondary))
const secondaryChildren = computed(() => (props.node.children || []).filter((child) => child.secondary))
const primaryChildrenLabel = computed(() => {
  if (props.node.kind === 'root') return 'Espacios principales'
  if (props.node.kind === 'space') return 'Módulos principales'
  return 'Submódulos representativos'
})
</script>

<template>
  <article
    class="rounded-2xl border border-border-muted bg-surface p-5 shadow-sm"
    data-testid="view-explorer-detail"
  >
    <div class="flex items-start justify-between gap-4">
      <div class="flex min-w-0 items-center gap-3">
        <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary-soft text-text-brand">
          <SidebarIcon :name="node.icon" class="h-5 w-5" aria-hidden="true" />
        </span>
        <div class="min-w-0">
          <p class="text-[10px] font-semibold uppercase tracking-widest text-text-subtle">
            {{ isPreviewing ? 'Vista previa' : 'Contexto del módulo' }}
          </p>
          <h3 class="mt-1 text-lg font-medium text-text-default [overflow-wrap:anywhere]">
            {{ node.label }}
          </h3>
        </div>
      </div>
      <span class="shrink-0 rounded-full bg-surface-raised px-2.5 py-1 text-xs text-text-muted">
        {{ relatedViewCount }} {{ relatedViewCount === 1 ? 'vista' : 'vistas' }}
      </span>
    </div>

    <div class="mt-4 flex flex-wrap items-center gap-2">
      <BaseBadge v-if="node.stage" variant="info" size="sm">{{ node.stage }}</BaseBadge>
      <BaseBadge v-if="actorLabel" variant="neutral" size="sm">{{ actorLabel }}</BaseBadge>
      <BaseBadge v-if="node.kind === 'space'" variant="success" size="sm">Recorrido completo</BaseBadge>
    </div>

    <p class="mt-4 text-sm leading-6 text-text-muted">{{ node.summary }}</p>
    <div class="mt-4 rounded-xl border border-primary/20 bg-primary-soft p-4">
      <p class="text-xs font-semibold uppercase tracking-wide text-text-brand">Valor operativo</p>
      <p class="mt-1 text-sm leading-6 text-text-default">{{ node.value }}</p>
    </div>

    <BaseButton
      v-if="node.kind === 'space' && !isPreviewing && !isTourActive"
      variant="primary"
      size="sm"
      class="mt-5"
      data-testid="view-explorer-start-tour"
      @click="emit('start-tour', node.id)"
    >
      Iniciar recorrido por {{ node.label }}
    </BaseButton>

    <div v-if="primaryChildren.length" class="mt-5">
      <p class="mb-2 text-xs font-semibold text-text-default">
        {{ primaryChildrenLabel }}
      </p>
      <div class="flex flex-wrap gap-2">
        <!-- panel-action-icons: allow-navigation-icon — the icon identifies a product module, not an action -->
        <BaseButton
          v-for="child in primaryChildren"
          :key="child.id"
          variant="secondary"
          size="sm"
          textPolicy="wrap"
          :data-testid="`view-explorer-context-child-${child.id}`"
          @click="emit('select', child.id)"
        >
          <SidebarIcon :name="child.icon" class="h-4 w-4 shrink-0" aria-hidden="true" />
          {{ child.label }}
        </BaseButton>
      </div>
    </div>

    <details v-if="secondaryChildren.length" class="group mt-5 rounded-xl border border-border-muted">
      <summary class="flex cursor-pointer list-none items-center justify-between px-4 py-3 text-sm font-medium text-text-muted [&::-webkit-details-marker]:hidden">
        Referencias complementarias
        <BaseActionIcon action="expand" class="transition-transform group-open:rotate-180" />
      </summary>
      <div class="flex flex-wrap gap-2 border-t border-border-muted p-3">
        <!-- panel-action-icons: allow-navigation-icon — the label identifies the complementary module -->
        <BaseButton
          v-for="child in secondaryChildren"
          :key="child.id"
          variant="ghost"
          size="sm"
          textPolicy="wrap"
          @click="emit('select', child.id)"
        >
          {{ child.label }}
        </BaseButton>
      </div>
    </details>

    <details v-if="technicalViews.length" class="group mt-5 rounded-xl border border-border-muted">
      <summary class="flex cursor-pointer list-none items-center justify-between px-4 py-3 text-sm font-medium text-text-muted [&::-webkit-details-marker]:hidden">
        Referencia técnica secundaria
        <BaseActionIcon action="expand" class="transition-transform group-open:rotate-180" />
      </summary>
      <ul class="divide-y divide-border-muted border-t border-border-muted">
        <li v-for="view in technicalViews" :key="view.url" class="flex items-start justify-between gap-3 px-4 py-3">
          <div class="min-w-0">
            <p class="text-sm font-medium text-text-default">{{ view.label }}</p>
            <code class="mt-1 block break-all text-xs text-text-brand">{{ view.url }}</code>
            <code class="mt-1 block break-all text-[11px] text-text-subtle">{{ view.file }}</code>
          </div>
          <BaseActionButton
            v-if="isOpenableViewUrl(view.url)"
            action="open-external"
            :label="`Abrir ${view.label}`"
            as="a"
            :to="view.url"
            target="_blank"
            rel="noopener"
          />
        </li>
      </ul>
    </details>
  </article>
</template>
