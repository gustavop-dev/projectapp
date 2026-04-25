<template>
  <div class="admin-layout min-h-screen bg-gray-50 transition-colors duration-200 dark:bg-esmerald-dark">
    <div class="hidden md:block">
      <PanelSidebar
        :is-collapsed="isCollapsed"
        :is-dark="isDark"
        @toggle-theme="toggle"
      />
    </div>

    <div
      class="mobile-topbar sticky top-0 z-30 flex h-14 items-center justify-between border-b border-esmerald/[0.06] px-4 md:hidden"
      :class="isDark ? 'bg-esmerald-dark/95 backdrop-blur-xl' : 'bg-white/90 backdrop-blur-xl'"
    >
      <button
        type="button"
        class="flex h-10 w-10 items-center justify-center rounded-full bg-esmerald-light text-esmerald dark:bg-esmerald dark:text-white"
        aria-label="Abrir menú"
        @click="openMobile"
      >
        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <span v-if="_panelViewLabel && route.path !== localePath('/panel')" class="text-sm font-medium text-esmerald dark:text-white truncate max-w-[180px]">
        {{ _panelViewLabel }}
      </span>
      <NuxtLink
        v-else
        :to="localePath('/panel')"
        class="text-base font-bold tracking-tight text-esmerald dark:text-white"
      >
        Project<span class="text-green-light dark:text-lemon">App.</span>
      </NuxtLink>

      <button
        type="button"
        class="flex h-10 w-10 items-center justify-center rounded-full bg-esmerald-light text-esmerald dark:bg-esmerald dark:text-white"
        :aria-label="isDark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'"
        @click="toggle"
      >
        <svg v-if="isDark" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      </button>
    </div>

    <PanelMobileDrawer
      :is-open="isMobileOpen"
      :is-dark="isDark"
      @close="closeMobile"
      @toggle-theme="toggle"
    />

    <main
      :class="[
        'relative z-10 transition-all duration-300 ease-in-out',
        'px-4 py-6 sm:px-6 lg:px-8',
        isCollapsed ? 'md:ml-[64px]' : 'md:ml-[240px]',
        isDark ? 'text-gray-200' : 'text-gray-900',
      ]"
    >
      <div
        v-if="_panelSectionLabel && _panelViewLabel"
        class="mb-5 flex items-center gap-1.5 text-xs"
        :class="isDark ? 'text-green-light/60' : 'text-green-light'"
      >
        <span>{{ _panelSectionLabel }}</span>
        <span class="text-green-light/40 dark:text-green-light/30">›</span>
        <span :class="isDark ? 'text-gray-400' : 'text-gray-500'">{{ _panelViewLabel }}</span>
      </div>
      <slot />
    </main>
  </div>
</template>

<script setup>
import { provide, watch, computed, onMounted, onUnmounted } from 'vue'
import { useDarkMode } from '~/composables/useDarkMode'
import { usePanelSidebar } from '~/composables/usePanelSidebar'
import { getPanelNavSections } from '~/config/panelNav'
import { isPanelNavItemActive } from '~/utils/panelNavActive'
import PanelSidebar from '~/components/panel/PanelSidebar.vue'
import PanelMobileDrawer from '~/components/panel/PanelMobileDrawer.vue'

const localePath = useLocalePath()
const route = useRoute()
const { isDark, toggle } = useDarkMode()

const {
  isCollapsed,
  isMobileOpen,
  hydrate: hydratePanelSidebar,
  toggle: togglePanelSidebar,
  openMobile,
  closeMobile,
  setupResizeListener,
  cleanupResizeListener,
} = usePanelSidebar()

onMounted(() => {
  hydratePanelSidebar()
  setupResizeListener()
})

onUnmounted(() => {
  cleanupResizeListener()
})

provide('togglePanelSidebar', togglePanelSidebar)

watch(() => route.fullPath, () => {
  closeMobile()
})

const _panelRouteMap = [
  { path: localePath('/panel/proposals/email-deliverability'), label: 'Entregabilidad' },
  { path: localePath('/panel/proposals/email-templates'), label: 'Plantillas' },
  { path: localePath('/panel/proposals/create'), label: 'Nueva prop.' },
  { path: localePath('/panel/proposals/defaults'), label: 'Prop. defaults' },
  { path: localePath('/panel/diagnostics/create'), label: 'Nuevo diag.' },
  { path: localePath('/panel/diagnostics/defaults'), label: 'Diag. defaults' },
  { path: localePath('/panel/blog/calendar'), label: 'Calendario' },
  { path: localePath('/panel/blog/create'), label: 'Nuevo post' },
  { path: localePath('/panel/portfolio/create'), label: 'Nuevo item' },
  { path: localePath('/panel/documents/create'), label: 'Nuevo doc.' },
  { path: localePath('/panel/proposals'), label: 'Propuestas' },
  { path: localePath('/panel/diagnostics'), label: 'Diagnósticos' },
  { path: localePath('/panel/blog'), label: 'Blog' },
  { path: localePath('/panel/portfolio'), label: 'Portfolio' },
  { path: localePath('/panel/documents'), label: 'Documentos' },
  { path: localePath('/panel/clients'), label: 'Clientes' },
  { path: localePath('/panel/defaults'), label: 'Defaults' },
  { path: localePath('/panel/emails'), label: 'Emails' },
  { path: localePath('/panel/views'), label: 'Mapa' },
  { path: localePath('/panel/admins'), label: 'Admins' },
  { path: localePath('/panel/tasks'), label: 'Kanban' },
  { path: localePath('/panel'), label: 'Dashboard', exact: true },
]

const _panelDynamic = [
  { re: /\/panel\/proposals\/[^/]+\/edit/, label: 'Edit. propuesta' },
  { re: /\/panel\/diagnostics\/[^/]+\/edit/, label: 'Edit. diagnóstico' },
  { re: /\/panel\/blog\/[^/]+\/edit/, label: 'Edit. post' },
  { re: /\/panel\/portfolio\/[^/]+\/edit/, label: 'Edit. portfolio' },
  { re: /\/panel\/documents\/[^/]+\/edit/, label: 'Edit. documento' },
]

const _panelDynamicSections = [
  { re: /\/panel\/proposals\/[^/]+\/edit/, label: 'Sales' },
  { re: /\/panel\/diagnostics\/[^/]+\/edit/, label: 'Sales' },
  { re: /\/panel\/blog\/[^/]+\/edit/, label: 'Website content' },
  { re: /\/panel\/portfolio\/[^/]+\/edit/, label: 'Website content' },
  { re: /\/panel\/documents\/[^/]+\/edit/, label: 'Documents' },
]

const _panelViewLabel = computed(() => {
  const p = route.path
  for (const { re, label } of _panelDynamic) {
    if (re.test(p)) return label
  }
  for (const { path, label, exact } of _panelRouteMap) {
    if (exact ? p === path : p === path || p.startsWith(path + '/')) return label
  }
  return null
})

const _panelSectionLabel = computed(() => {
  const p = route.path
  for (const { re, label } of _panelDynamicSections) {
    if (re.test(p)) return label
  }
  const sections = getPanelNavSections(localePath)
  for (const section of sections) {
    for (const item of section.items) {
      if (!item.divider && isPanelNavItemActive(p, item)) {
        return section.label
      }
    }
  }
  return null
})

useHead(() => ({
  title: _panelViewLabel.value ? `Project App (${_panelViewLabel.value})` : 'Project App',
}))
</script>
