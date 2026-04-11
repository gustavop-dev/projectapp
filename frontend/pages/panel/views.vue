<template>
  <div>
    <div class="mb-8 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p class="mb-2 text-xs font-semibold uppercase tracking-widest text-green-light dark:text-green-light/80">
          Reference
        </p>
        <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100">Mapa de vistas</h1>
        <p class="mt-2 max-w-3xl text-sm leading-6 text-gray-500 dark:text-green-light/80">
          Inventario de vistas de la aplicacion, agrupadas por contexto. Las URLs dinamicas usan parametros como <code class="font-mono text-xs text-esmerald dark:text-lemon">:id</code>, <code class="font-mono text-xs text-esmerald dark:text-lemon">:uuid</code> o <code class="font-mono text-xs text-esmerald dark:text-lemon">:slug</code>.
        </p>
      </div>

      <div class="rounded-xl border border-gray-100 bg-white px-4 py-3 text-sm shadow-sm dark:border-white/[0.06] dark:bg-white/[0.04]">
        <span class="block text-xs text-gray-400 dark:text-green-light/70">Total</span>
        <div class="flex items-baseline gap-1">
          <strong class="text-2xl font-light text-esmerald dark:text-lemon">{{ filteredViewCount }}</strong>
          <span v-if="isFiltering" class="text-sm text-gray-400 dark:text-green-light/60">/ {{ totalViews }}</span>
          <span class="ml-1 text-gray-500 dark:text-green-light/80">vistas</span>
        </div>
      </div>
    </div>

    <!-- Filter tabs -->
    <ProposalFilterTabs
      :tabs="savedTabs"
      :active-tab-id="activeTabId"
      :is-tab-limit-reached="isTabLimitReached"
      @select="selectTab"
      @create="saveTab"
      @rename="renameTab"
      @delete="deleteTab"
    />

    <!-- Search bar + filter toggle -->
    <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
      <div class="relative flex-1">
        <svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="search"
          type="text"
          placeholder="Buscar vista por nombre, URL, referencia o archivo..."
          class="w-full rounded-xl border border-gray-200 bg-white py-2.5 pl-10 pr-4 text-sm text-gray-700 outline-none transition-colors placeholder:text-gray-400 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:placeholder:text-gray-500"
        />
        <button
          v-if="search"
          type="button"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 transition-colors hover:text-gray-600 dark:hover:text-gray-300"
          @click="search = ''"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <FilterToggleButton
        :open="isFilterPanelOpen"
        :count="activeFilterCount"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      />
    </div>

    <!-- Filter panel -->
    <ViewMapFilterPanel
      v-model="currentFilters"
      :is-open="isFilterPanelOpen"
      :filter-count="activeFilterCount"
      @reset="resetFilters"
    />

    <!-- Proposal reference guide -->
    <section class="mb-8 rounded-xl border border-emerald-100 bg-emerald-50 p-5 dark:border-white/[0.08] dark:bg-white/[0.04]">
      <h2 class="text-base font-medium text-esmerald dark:text-white">Como referirse a las vistas de propuestas</h2>
      <p class="mt-2 text-sm leading-6 text-emerald-900/70 dark:text-green-light/80">
        Si dices "detalle de propuesta" puede confundirse la pantalla interna del panel con el enlace publico del cliente. Usa el contexto, el tipo de identificador y la URL.
      </p>

      <div class="mt-4 grid gap-3 lg:grid-cols-3">
        <article
          v-for="item in proposalGuide"
          :key="item.url"
          class="rounded-lg border border-emerald-100 bg-white p-4 shadow-sm dark:border-white/[0.06] dark:bg-esmerald-dark/70"
        >
          <p class="text-xs font-semibold uppercase tracking-widest text-green-light">{{ item.label }}</p>
          <h3 class="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">{{ item.recommendedName }}</h3>
          <p class="mt-2 font-mono text-xs text-esmerald dark:text-lemon">{{ item.url }}</p>
          <p class="mt-2 text-xs leading-5 text-gray-500 dark:text-green-light/80">{{ item.description }}</p>
          <p class="mt-2 break-all font-mono text-[11px] text-gray-400 dark:text-green-light/60">{{ item.file }}</p>
        </article>
      </div>
    </section>

    <!-- View catalog -->
    <div v-if="filteredSections.length > 0" class="space-y-6">
      <details
        v-for="section in filteredSections"
        :key="section.id"
        open
        class="group overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm dark:border-white/[0.06] dark:bg-white/[0.04]"
      >
        <summary class="flex items-center justify-between gap-3 border-b border-gray-100 px-5 py-4 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden dark:border-white/[0.06]">
          <div class="flex flex-1 flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 class="text-base font-medium text-gray-900 dark:text-gray-100">{{ section.label }}</h2>
              <p class="mt-1 text-sm text-gray-500 dark:text-green-light/80">{{ section.description }}</p>
            </div>
            <span class="inline-flex w-fit items-center rounded-full bg-esmerald-light px-3 py-1 text-xs font-medium text-esmerald dark:bg-white/[0.06] dark:text-lemon">
              {{ section.views.length }} vistas
            </span>
          </div>
          <svg class="h-4 w-4 flex-shrink-0 text-gray-400 transition-transform duration-300 group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>

        <div class="divide-y divide-gray-100 dark:divide-white/[0.06]">
          <article
            v-for="view in section.views"
            :key="`${section.id}-${view.url}-${view.file}`"
            class="grid gap-3 px-5 py-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)_minmax(0,1.2fr)_2.5rem] lg:items-start"
          >
            <div>
              <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ view.label }}</h3>
              <p class="mt-1 text-xs text-gray-500 dark:text-green-light/80">{{ view.reference }}</p>
              <p v-if="view.notes" class="mt-2 text-xs leading-5 text-amber-700 dark:text-amber-300">{{ view.notes }}</p>
            </div>

            <div>
              <p class="mb-1 text-[10px] font-semibold uppercase tracking-widest text-gray-400 dark:text-green-light/60">URL</p>
              <code class="block break-all font-mono text-xs text-esmerald dark:text-lemon">{{ view.url }}</code>
            </div>

            <div>
              <p class="mb-1 text-[10px] font-semibold uppercase tracking-widest text-gray-400 dark:text-green-light/60">Archivo</p>
              <code class="block break-all font-mono text-[11px] text-gray-500 dark:text-green-light/70">{{ view.file }}</code>
            </div>

            <div class="flex items-start justify-center lg:pt-1">
              <button
                type="button"
                class="rounded-lg p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-lemon"
                :title="copiedKey === `${section.id}-${view.url}` ? 'Copiado!' : 'Copiar referencia'"
                @click="copyReference(section, view)"
              >
                <!-- Checkmark icon when copied -->
                <svg v-if="copiedKey === `${section.id}-${view.url}`" class="h-4 w-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                <!-- Clipboard icon default -->
                <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                </svg>
              </button>
            </div>
          </article>
        </div>
      </details>
    </div>

    <!-- Empty state -->
    <div v-else class="rounded-xl border border-gray-100 bg-white px-6 py-12 text-center shadow-sm dark:border-white/[0.06] dark:bg-white/[0.04]">
      <svg class="mx-auto h-10 w-10 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <p class="mt-3 text-sm text-gray-500 dark:text-gray-400">No se encontraron vistas con los filtros actuales.</p>
      <button
        type="button"
        class="mt-3 text-sm font-medium text-esmerald transition-colors hover:text-emerald-700 dark:text-lemon dark:hover:text-yellow-300"
        @click="clearAll"
      >
        Limpiar filtros y busqueda
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  countCatalogViews,
  getViewCopyReference,
  proposalViewReferenceGuide,
  viewCatalogSections,
} from '~/config/viewCatalog'
import { useViewMapFilters } from '~/composables/useViewMapFilters'
import ViewMapFilterPanel from '~/components/views/ViewMapFilterPanel.vue'
import ProposalFilterTabs from '~/components/proposals/ProposalFilterTabs.vue'
import FilterToggleButton from '~/components/ui/FilterToggleButton.vue'

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] })

const sections = viewCatalogSections
const proposalGuide = proposalViewReferenceGuide
const totalViews = countCatalogViews(sections)

const {
  currentFilters,
  savedTabs,
  activeTabId,
  isFilterPanelOpen,
  activeFilterCount,
  hasActiveFilters,
  isTabLimitReached,
  applyFilters,
  resetFilters,
  selectTab,
  saveTab,
  deleteTab,
  renameTab,
} = useViewMapFilters()

const search = ref('')
const copiedKey = ref(null)

const filteredSections = computed(() => {
  let result = applyFilters(sections)

  const q = search.value.trim().toLowerCase()
  if (q) {
    result = result
      .map((s) => ({
        ...s,
        views: s.views.filter((v) =>
          v.label.toLowerCase().includes(q)
          || v.url.toLowerCase().includes(q)
          || v.reference.toLowerCase().includes(q)
          || v.file.toLowerCase().includes(q),
        ),
      }))
      .filter((s) => s.views.length > 0)
  }

  return result
})

const filteredViewCount = computed(() => countCatalogViews(filteredSections.value))

const isFiltering = computed(() => hasActiveFilters.value || search.value.trim().length > 0)

let copyTimer = null

function copyReference(section, view) {
  const text = getViewCopyReference(section.label, view)
  const key = `${section.id}-${view.url}`
  navigator.clipboard.writeText(text).then(() => {
    clearTimeout(copyTimer)
    copiedKey.value = key
    copyTimer = setTimeout(() => { copiedKey.value = null }, 1500)
  })
}

function clearAll() {
  resetFilters()
  search.value = ''
}
</script>
