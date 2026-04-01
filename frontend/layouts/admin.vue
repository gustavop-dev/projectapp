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
        title="Open menu"
        @click="openMobile"
      >
        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <NuxtLink
        :to="localePath('/panel')"
        class="text-base font-bold tracking-tight text-esmerald dark:text-white"
      >
        Project<span class="text-green-light dark:text-lemon">App.</span>
      </NuxtLink>
      <button
        type="button"
        class="flex h-10 w-10 items-center justify-center rounded-full bg-esmerald-light text-esmerald dark:bg-esmerald dark:text-white"
        title="Toggle theme"
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
      <div class="mx-auto max-w-7xl">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup>
import { provide, watch, onMounted, onUnmounted } from 'vue'
import { useDarkMode } from '~/composables/useDarkMode'
import { usePanelSidebar } from '~/composables/usePanelSidebar'
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
</script>
