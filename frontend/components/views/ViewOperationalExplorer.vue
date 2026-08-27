<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import BaseBadge from '~/components/base/BaseBadge.vue'
import BaseButton from '~/components/base/BaseButton.vue'
import BaseActionButton from '~/components/base/BaseActionButton.vue'
import { usePanelViewportProfile } from '~/composables/usePanelViewportProfile'
import { orbitalPosition, useOrbitalExplorer } from '~/composables/useOrbitalExplorer'
import {
  capabilityNodePath,
  capabilityViewRecords,
  findCapabilityNode,
  flattenCapabilityCatalog,
  viewCapabilityCatalog,
} from '~/config/viewCapabilityCatalog'
import {
  isOpenableViewUrl,
  viewCatalogSections,
} from '~/config/viewCatalog'

const props = defineProps({
  selectedNodeId: { type: String, default: null },
  showRelations: { type: Boolean, default: true },
})

const emit = defineEmits(['select', 'update:showRelations', 'open-map'])

const { profile } = usePanelViewportProfile()
const {
  angle,
  zoom,
  isManuallyPaused,
  isAutoRotating,
  prefersReducedMotion,
  rotateBy,
  zoomIn,
  zoomOut,
  resetOrbit,
  togglePause,
  startDrag,
  moveDrag,
  endDrag,
  consumeDrag,
  setHovering,
  setFocusWithin,
} = useOrbitalExplorer()

const search = ref('')
const activeNodeId = ref(null)
const stageRef = ref(null)

const allNodes = flattenCapabilityCatalog()
const currentNode = computed(() => (
  findCapabilityNode(props.selectedNodeId) || viewCapabilityCatalog
))
const currentPath = computed(() => capabilityNodePath(currentNode.value.id))
const orbitNodes = computed(() => currentNode.value.children || [])

const nodePositions = computed(() => orbitNodes.value.map((node, index) => ({
  node,
  ...orbitalPosition(
    index,
    orbitNodes.value.length,
    angle.value,
    profile.value,
    zoom.value,
  ),
})))

const positionsById = computed(() => new Map(
  nodePositions.value.map((position) => [position.node.id, position]),
))

const visibleRelations = computed(() => {
  if (!props.showRelations) return []
  return (currentNode.value.relations || [])
    .map((relation) => ({
      ...relation,
      fromPosition: positionsById.value.get(relation.from),
      toPosition: positionsById.value.get(relation.to),
    }))
    .filter((relation) => relation.fromPosition && relation.toPosition)
})

const currentSection = computed(() => (
  currentNode.value.sectionId
    ? viewCatalogSections.find((section) => section.id === currentNode.value.sectionId) || null
    : null
))

const technicalViews = computed(() => capabilityViewRecords(currentNode.value))

function descendantViewUrls(node) {
  return [
    ...(node.viewUrls || []),
    ...(node.children || []).flatMap((child) => descendantViewUrls(child)),
  ]
}

const currentViewCount = computed(() => {
  if (currentNode.value.id === viewCapabilityCatalog.id) {
    return viewCatalogSections.reduce((total, section) => total + section.views.length, 0)
  }
  if (currentSection.value) return currentSection.value.views.length
  return new Set(descendantViewUrls(currentNode.value)).size
})

const searchResults = computed(() => {
  const query = search.value.trim().toLocaleLowerCase('es')
  if (!query) return []
  return allNodes
    .filter((node) => node.id !== viewCapabilityCatalog.id)
    .filter((node) => [node.label, node.summary, node.value, node.stage]
      .filter(Boolean)
      .some((value) => value.toLocaleLowerCase('es').includes(query)))
    .slice(0, 8)
})

const relationSummary = computed(() => {
  if (!activeNodeId.value) return currentNode.value.relations || []
  return (currentNode.value.relations || []).filter((relation) => (
    relation.from === activeNodeId.value || relation.to === activeNodeId.value
  ))
})

const actorLabel = computed(() => {
  const actors = currentNode.value.actors || []
  if (actors.length === 0) return null
  if (actors.length > 1) return 'Cliente y equipo'
  return actors[0] === 'team' ? 'Equipo' : 'Cliente'
})

const canGoBack = computed(() => currentPath.value.length > 1)

watch(() => props.selectedNodeId, (nodeId) => {
  if (nodeId && !findCapabilityNode(nodeId)) emit('select', null)
}, { immediate: true })

function selectNode(nodeId) {
  if (consumeDrag()) return
  search.value = ''
  emit('select', nodeId)
  nextTick(() => stageRef.value?.focus())
}

function goBack() {
  if (!canGoBack.value) return
  const parent = currentPath.value.at(-2)
  emit('select', parent.id === viewCapabilityCatalog.id ? null : parent.id)
}

function handleStageKeydown(event) {
  if (event.target !== event.currentTarget) return
  if (event.key === 'ArrowLeft') {
    event.preventDefault()
    rotateBy(-15)
  }
  if (event.key === 'ArrowRight') {
    event.preventDefault()
    rotateBy(15)
  }
  if (event.key === 'Escape') {
    event.preventDefault()
    goBack()
  }
}

function nodeStyle(position) {
  return {
    left: `${position.x}%`,
    top: `${position.y}%`,
    transform: `translate(-50%, -50%) scale(${position.scale})`,
    zIndex: position.zIndex,
  }
}

function relationIsActive(relation) {
  return activeNodeId.value
    && (relation.from === activeNodeId.value || relation.to === activeNodeId.value)
}

function nodeIsDimmed(nodeId) {
  if (!activeNodeId.value || activeNodeId.value === nodeId) return false
  const connected = (currentNode.value.relations || []).some((relation) => (
    (relation.from === activeNodeId.value && relation.to === nodeId)
    || (relation.to === activeNodeId.value && relation.from === nodeId)
  ))
  return !connected
}
</script>

<template>
  <section class="space-y-5" data-testid="view-operational-explorer">
    <div class="rounded-2xl border border-border-muted bg-surface p-4 shadow-sm">
      <div class="flex flex-col gap-3 panel-landscape:flex-row panel-landscape:items-center panel-landscape:justify-between">
        <nav class="flex min-w-0 flex-wrap items-center gap-1.5 text-sm" aria-label="Ruta del explorador">
          <template v-for="(node, index) in currentPath" :key="node.id">
            <span v-if="index > 0" class="text-text-subtle" aria-hidden="true">/</span>
            <BaseButton
              variant="link"
              size="sm"
              class="max-w-full text-left text-text-muted"
              :class="index === currentPath.length - 1 ? 'font-medium text-text-default' : ''"
              :aria-current="index === currentPath.length - 1 ? 'page' : undefined"
              @click="selectNode(node.id === viewCapabilityCatalog.id ? null : node.id)"
            >
              {{ node.label }}
            </BaseButton>
          </template>
        </nav>

        <div class="relative w-full panel-landscape:max-w-md">
          <label for="view-explorer-search" class="sr-only">Buscar una capacidad</label>
          <input
            id="view-explorer-search"
            v-model="search"
            type="search"
            autocomplete="off"
            placeholder="Buscar una capacidad o beneficio..."
            class="w-full rounded-xl border border-input-border bg-input-bg px-4 py-2.5 text-sm text-input-text outline-none placeholder:text-text-subtle focus:border-focus-ring focus:ring-1 focus:ring-focus-ring/30"
          />
          <div
            v-if="search.trim()"
            class="absolute inset-x-0 top-full z-40 mt-2 overflow-hidden rounded-xl border border-border-default bg-surface shadow-lg"
            data-testid="view-explorer-search-results"
          >
            <!-- design-tokens: allow-raw-button — searchable capability option -->
            <button
              v-for="result in searchResults"
              :key="result.id"
              type="button"
              class="block w-full border-b border-border-muted px-4 py-3 text-left last:border-b-0 hover:bg-surface-raised focus:bg-surface-raised focus:outline-none"
              @click="selectNode(result.id)"
            >
              <span class="block text-sm font-medium text-text-default">{{ result.label }}</span>
              <span class="mt-0.5 block text-xs text-text-muted">{{ result.summary }}</span>
            </button>
            <p v-if="searchResults.length === 0" class="px-4 py-5 text-center text-sm text-text-muted">
              No encontramos una capacidad con ese término.
            </p>
          </div>
        </div>
      </div>
    </div>

    <div class="rounded-3xl border border-border-muted bg-surface shadow-sm">
      <div class="flex flex-col gap-3 border-b border-border-muted p-4 panel-portrait:flex-row panel-portrait:items-center panel-portrait:justify-between">
        <div class="flex flex-wrap items-center gap-2">
          <BaseActionButton
            v-if="canGoBack"
            action="back"
            label="Volver al nivel anterior"
            data-testid="view-explorer-back"
            @click="goBack"
          />
          <span class="text-xs text-text-muted">
            Arrastra para girar · usa las flechas para ajustar
          </span>
        </div>

        <div class="flex flex-wrap items-center gap-1" aria-label="Controles del explorador">
          <BaseActionButton action="previous" label="Girar a la izquierda" @click="rotateBy(-15)" />
          <BaseActionButton action="next" label="Girar a la derecha" @click="rotateBy(15)" />
          <BaseActionButton action="zoom-out" label="Alejar" @click="zoomOut" />
          <BaseActionButton action="zoom-in" label="Acercar" @click="zoomIn" />
          <BaseActionButton action="refresh" label="Centrar la órbita" @click="resetOrbit" />
          <BaseActionButton
            :action="isManuallyPaused ? 'activate' : 'deactivate'"
            :label="isManuallyPaused ? 'Reanudar giro suave' : 'Pausar giro suave'"
            data-testid="view-explorer-motion-toggle"
            @click="togglePause"
          />
          <BaseActionButton
            v-if="currentNode.relations?.length"
            :action="showRelations ? 'unlink' : 'link'"
            :label="showRelations ? 'Ocultar relaciones operativas' : 'Mostrar relaciones operativas'"
            data-testid="view-explorer-relations-toggle"
            @click="emit('update:showRelations', !showRelations)"
          />
        </div>
      </div>

      <div
        ref="stageRef"
        tabindex="0"
        class="relative touch-none overflow-hidden rounded-b-3xl bg-surface-raised outline-none focus:ring-2 focus:ring-inset focus:ring-focus-ring/40"
        :class="orbitNodes.length
          ? 'min-h-[38rem] panel-portrait:min-h-[42rem] panel-landscape:min-h-[46rem]'
          : 'min-h-[26rem] panel-portrait:min-h-[30rem] panel-landscape:min-h-[32rem]'"
        aria-label="Constelación de capacidades. Usa Tab para recorrer nodos, las flechas para girar y Escape para volver."
        data-testid="view-explorer-stage"
        @keydown="handleStageKeydown"
        @pointerdown.self="startDrag"
        @pointermove="moveDrag"
        @pointerup="endDrag"
        @pointercancel="endDrag"
        @mouseenter="setHovering(true)"
        @mouseleave="setHovering(false)"
        @focusin="setFocusWithin(true)"
        @focusout="setFocusWithin(false)"
      >
        <div class="pointer-events-none absolute inset-0 opacity-70" aria-hidden="true">
          <div class="absolute left-1/2 top-1/2 h-3/4 w-3/4 -translate-x-1/2 -translate-y-1/2 rounded-full border border-border-muted" />
          <div class="absolute left-1/2 top-1/2 h-1/2 w-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border border-primary/20" />
        </div>

        <svg
          class="pointer-events-none absolute inset-0 h-full w-full"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <line
            v-for="position in nodePositions"
            :key="`hierarchy-${position.node.id}`"
            x1="50"
            y1="50"
            :x2="position.x"
            :y2="position.y"
            vector-effect="non-scaling-stroke"
            class="stroke-border-default"
            stroke-width="1"
            opacity="0.7"
          />
          <line
            v-for="relation in visibleRelations"
            :key="`relation-${relation.from}-${relation.to}`"
            :x1="relation.fromPosition.x"
            :y1="relation.fromPosition.y"
            :x2="relation.toPosition.x"
            :y2="relation.toPosition.y"
            vector-effect="non-scaling-stroke"
            :class="relationIsActive(relation) ? 'stroke-accent' : 'stroke-text-subtle'"
            stroke-width="1.5"
            stroke-dasharray="5 4"
            :opacity="activeNodeId && !relationIsActive(relation) ? 0.2 : 0.75"
            data-testid="view-explorer-relation"
          />
        </svg>

        <article
          class="absolute left-1/2 top-1/2 z-30 flex w-40 -translate-x-1/2 -translate-y-1/2 flex-col items-center rounded-3xl border border-primary/30 bg-surface px-4 py-5 text-center shadow-lg panel-portrait:w-52 panel-portrait:px-5 panel-portrait:py-6"
          data-testid="view-explorer-center"
        >
          <span class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-sm font-semibold text-on-primary shadow-sm">
            PA
          </span>
          <p class="text-[10px] font-semibold uppercase tracking-widest text-text-subtle">
            {{ currentNode.kind === 'root' ? 'Ecosistema' : currentNode.stage || 'Capacidad' }}
          </p>
          <h2 class="mt-1 text-base font-medium text-text-default">{{ currentNode.label }}</h2>
          <p class="mt-2 hidden text-xs leading-5 text-text-muted panel-portrait:line-clamp-4">{{ currentNode.summary }}</p>
          <span class="mt-3 rounded-full bg-primary-soft px-2.5 py-1 text-[11px] font-medium text-text-brand">
            {{ currentViewCount }} {{ currentViewCount === 1 ? 'vista relacionada' : 'vistas relacionadas' }}
          </span>
        </article>

        <BaseButton
          v-for="(position, index) in nodePositions"
          :key="position.node.id"
          variant="secondary"
          size="sm"
          class="absolute flex min-h-20 w-20 flex-col gap-1 rounded-2xl px-1.5 py-2 text-center shadow-sm transition-[opacity,box-shadow,transform] duration-300 motion-reduce:transition-none panel-portrait:w-32 panel-portrait:px-2 panel-portrait:py-3"
          :class="[
            activeNodeId === position.node.id ? 'border-primary shadow-md' : '',
            nodeIsDimmed(position.node.id) ? 'opacity-40' : 'opacity-100',
          ]"
          :style="nodeStyle(position)"
          :data-testid="`view-explorer-node-${position.node.id}`"
          :aria-label="`${position.node.label}. ${position.node.summary}`"
          @mouseenter="activeNodeId = position.node.id"
          @mouseleave="activeNodeId = null"
          @focus="activeNodeId = position.node.id"
          @blur="activeNodeId = null"
          @click="selectNode(position.node.id)"
        >
          <span class="text-[10px] font-semibold uppercase tracking-widest text-text-subtle">
            {{ String(index + 1).padStart(2, '0') }}
          </span>
          <span class="line-clamp-2 text-[11px] font-medium leading-4 text-text-default panel-portrait:text-sm">
            {{ position.node.label }}
          </span>
          <span v-if="position.node.children?.length" class="text-[10px] text-text-muted">
            {{ position.node.children.length }} capacidades
          </span>
        </BaseButton>

        <p class="sr-only" role="status" aria-live="polite">
          {{ currentNode.label }}. {{ orbitNodes.length }} nodos disponibles.
          {{ isAutoRotating ? 'Giro suave activo.' : 'Giro suave pausado.' }}
        </p>
      </div>
    </div>

    <div class="grid gap-4 panel-landscape:grid-cols-[minmax(0,1.25fr)_minmax(18rem,0.75fr)]">
      <article class="rounded-2xl border border-border-muted bg-surface p-5 shadow-sm" data-testid="view-explorer-detail">
        <div class="flex flex-wrap items-center gap-2">
          <BaseBadge v-if="currentNode.stage" variant="info" size="sm">{{ currentNode.stage }}</BaseBadge>
          <BaseBadge v-if="actorLabel" variant="neutral" size="sm">{{ actorLabel }}</BaseBadge>
          <BaseBadge v-if="currentNode.isDeep" variant="success" size="sm">Exploración completa</BaseBadge>
        </div>
        <p class="mt-4 text-[10px] font-semibold uppercase tracking-widest text-text-subtle">Qué permite hacer</p>
        <h3 class="mt-1 text-lg font-medium text-text-default">{{ currentNode.label }}</h3>
        <p class="mt-2 text-sm leading-6 text-text-muted">{{ currentNode.summary }}</p>
        <div class="mt-4 rounded-xl border border-primary/20 bg-primary-soft p-4">
          <p class="text-xs font-semibold uppercase tracking-wide text-text-brand">Valor operativo</p>
          <p class="mt-1 text-sm leading-6 text-text-default">{{ currentNode.value }}</p>
        </div>

        <div v-if="currentNode.children?.length" class="mt-5">
          <p class="mb-2 text-xs font-semibold text-text-default">Capacidades disponibles</p>
          <div class="flex flex-wrap gap-2">
            <BaseButton
              v-for="child in currentNode.children"
              :key="child.id"
              variant="secondary"
              size="sm"
              @click="selectNode(child.id)"
            >
              {{ child.label }}
            </BaseButton>
          </div>
        </div>

        <div v-if="currentSection && !currentNode.isDeep" class="mt-5 flex flex-wrap items-center gap-3">
          <BaseButton variant="primary" size="sm" @click="emit('open-map', currentSection.id)">
            Ver {{ currentSection.views.length }} vistas en el modo Mapa
          </BaseButton>
          <span class="text-xs text-text-muted">La exploración comercial profunda se ampliará por fases.</span>
        </div>

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

      <aside class="rounded-2xl border border-border-muted bg-surface p-5 shadow-sm">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-[10px] font-semibold uppercase tracking-widest text-text-subtle">Conexiones</p>
            <h3 class="mt-1 text-sm font-medium text-text-default">Recorrido operativo</h3>
          </div>
          <span class="rounded-full bg-surface-raised px-2.5 py-1 text-xs text-text-muted">
            {{ relationSummary.length }}
          </span>
        </div>
        <div class="mt-4 flex items-center gap-4 text-xs text-text-muted">
          <span class="flex items-center gap-2"><span class="h-px w-7 bg-border-default" /> Jerarquía</span>
          <span class="flex items-center gap-2"><span class="w-7 border-t border-dashed border-text-subtle" /> Conexión operativa</span>
        </div>
        <ul v-if="relationSummary.length" class="mt-4 space-y-2">
          <li
            v-for="relation in relationSummary"
            :key="`${relation.from}-${relation.to}`"
            class="rounded-xl border border-border-muted bg-surface-raised px-3 py-2.5 text-xs leading-5 text-text-muted"
          >
            <strong class="font-medium text-text-default">{{ findCapabilityNode(relation.from)?.label }}</strong>
            <span class="mx-1 text-text-subtle">→</span>
            {{ relation.label }}
            <span class="mx-1 text-text-subtle">→</span>
            <strong class="font-medium text-text-default">{{ findCapabilityNode(relation.to)?.label }}</strong>
          </li>
        </ul>
        <p v-else class="mt-4 text-sm leading-6 text-text-muted">
          En este nivel mostramos la jerarquía. Las relaciones funcionales aparecen al entrar a Plataforma.
        </p>
        <p v-if="prefersReducedMotion" class="mt-4 rounded-lg bg-info-soft px-3 py-2 text-xs text-info-strong">
          El giro automático está desactivado por tu preferencia de movimiento reducido.
        </p>
      </aside>
    </div>
  </section>
</template>
