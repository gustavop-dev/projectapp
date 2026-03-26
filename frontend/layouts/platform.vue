<template>
  <div :class="{ dark: isDark }" class="min-h-screen bg-gray-50 dark:bg-esmerald-dark">
    <!-- Desktop sidebar (hidden on mobile) -->
    <div class="hidden md:block">
      <PlatformSidebar
        :is-collapsed="isCollapsed"
        :is-dark="isDark"
        @logout="handleLogout"
      />
    </div>

    <!-- Mobile top bar -->
    <div class="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-esmerald/[0.06] bg-white/80 px-4 backdrop-blur-xl dark:border-white/[0.06] dark:bg-esmerald-dark/90 md:hidden">
      <button
        type="button"
        class="flex h-10 w-10 items-center justify-center rounded-full bg-esmerald-light text-esmerald dark:bg-esmerald dark:text-white"
        @click="openMobile"
      >
        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <NuxtLink :to="localePath('/platform/dashboard')" class="text-base font-bold tracking-tight text-esmerald dark:text-white">
        Project<span class="text-green-light dark:text-lemon">App.</span>
      </NuxtLink>

      <div class="flex h-8 w-8 items-center justify-center rounded-full bg-esmerald text-xs font-bold text-white dark:bg-lemon dark:text-esmerald-dark">
        {{ authStore.userInitials }}
      </div>
    </div>

    <!-- Mobile drawer -->
    <PlatformMobileDrawer
      :is-open="isMobileOpen"
      :is-dark="isDark"
      @close="closeMobile"
      @logout="handleLogout"
      @toggle-theme="toggle"
    />

    <!-- Main content -->
    <main
      :class="[
        'relative transition-all duration-300 ease-in-out',
        'px-4 py-6 sm:px-6 lg:px-8',
        'md:ml-[240px]',
        isCollapsed ? 'md:ml-[64px]' : 'md:ml-[240px]',
      ]"
    >
      <div class="mx-auto max-w-6xl">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup>
import { provide, watch, onMounted, onUnmounted } from 'vue'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformTheme } from '~/composables/usePlatformTheme'
import { usePlatformSidebar } from '~/composables/usePlatformSidebar'
import PlatformSidebar from '~/components/platform/PlatformSidebar.vue'
import PlatformMobileDrawer from '~/components/platform/PlatformMobileDrawer.vue'

const route = useRoute()
const localePath = useLocalePath()
const authStore = usePlatformAuthStore()
const { isDark, toggle, hydrate: hydrateTheme } = usePlatformTheme()
const {
  isCollapsed,
  isMobileOpen,
  hydrate: hydrateSidebar,
  toggle: toggleSidebar,
  openMobile,
  closeMobile,
  setupResizeListener,
  cleanupResizeListener,
} = usePlatformSidebar()

authStore.hydrate()

onMounted(() => {
  hydrateTheme()
  hydrateSidebar()
  setupResizeListener()
})

onUnmounted(() => {
  cleanupResizeListener()
})

provide('toggleSidebar', toggleSidebar)
provide('toggleTheme', toggle)

watch(() => route.fullPath, () => {
  closeMobile()
})

async function handleLogout() {
  authStore.logout()
  await navigateTo(localePath('/platform/login'))
}
</script>
