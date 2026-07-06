<template>
  <div class="admin-layout min-h-screen bg-gray-50 transition-colors duration-200 dark:bg-primary-strong">
    <div class="hidden md:block">
      <PanelSidebar
        :is-collapsed="isCollapsed"
        :is-dark="isDark"
        @toggle-theme="toggle"
      />
    </div>

    <div
      class="mobile-topbar sticky top-0 z-30 flex h-14 items-center justify-between border-b border-input-border/[0.06] px-4 md:hidden"
      :class="isDark ? 'bg-primary-strong/95 backdrop-blur-xl' : 'bg-surface/90 backdrop-blur-xl'"
    >
      <button
        type="button"
        class="flex h-10 w-10 items-center justify-center rounded-full bg-primary-soft text-text-brand dark:bg-primary dark:text-white"
        aria-label="Abrir menú"
        @click="openMobile"
      >
        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <span v-if="_panelViewLabel && route.path !== localePath('/panel')" class="text-sm font-medium text-text-brand dark:text-white truncate max-w-[180px]">
        {{ _panelViewLabel }}
      </span>
      <NuxtLink
        v-else
        :to="localePath('/panel')"
        class="text-base font-bold tracking-tight text-text-brand dark:text-white"
      >
        Project<span class="text-green-light dark:text-accent">App.</span>
      </NuxtLink>

      <button
        type="button"
        class="flex h-10 w-10 items-center justify-center rounded-full bg-primary-soft text-text-brand dark:bg-primary dark:text-white"
        :aria-label="themeToggleLabel(isDark)"
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
        isDark ? 'text-gray-200' : 'text-text-default',
      ]"
    >
      <div
        v-if="_panelSectionLabel && _panelViewLabel"
        class="mb-5 flex items-center gap-1.5 text-xs"
        :class="isDark ? 'text-green-light/60' : 'text-green-light'"
      >
        <span>{{ _panelSectionLabel }}</span>
        <span class="text-green-light/40 dark:text-green-light/30">›</span>
        <span class="text-text-muted">{{ _panelViewLabel }}</span>
      </div>
      <slot />
    </main>

    <PanelRefreshButton
      v-if="refreshStore.hasHandler"
      :loading="refreshStore.isRefreshing"
      @click="refreshStore.trigger()"
    />

    <PanelNotificationHost />
  </div>
</template>

<script setup>
import { provide, watch, computed, onMounted, onUnmounted } from 'vue'
import { useDarkMode, themeToggleLabel } from '~/composables/useDarkMode'
import { usePanelSidebar } from '~/composables/usePanelSidebar'
import { getPanelNavSections } from '~/config/panelNav'
import { resolvePanelBreadcrumb } from '~/utils/panelBreadcrumbs'
import { usePanelRefreshStore } from '~/stores/panel_refresh'
import PanelSidebar from '~/components/panel/PanelSidebar.vue'
import PanelMobileDrawer from '~/components/panel/PanelMobileDrawer.vue'
import PanelRefreshButton from '~/components/panel/PanelRefreshButton.vue'
import PanelNotificationHost from '~/components/panel/PanelNotificationHost.vue'

const refreshStore = usePanelRefreshStore()

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

const _panelBreadcrumb = computed(() =>
  resolvePanelBreadcrumb(route.path, getPanelNavSections(localePath)),
)
const _panelViewLabel = computed(() => _panelBreadcrumb.value?.label ?? null)
const _panelSectionLabel = computed(() => _panelBreadcrumb.value?.section ?? null)

useHead(() => ({
  title: _panelViewLabel.value ? `Project App (${_panelViewLabel.value})` : 'Project App',
}))
</script>
