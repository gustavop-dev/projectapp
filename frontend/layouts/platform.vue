<template>
  <div
    :class="[
      { dark: isDark },
      hasCover ? 'platform-cover' : '',
      hasCover && isCoverDark ? 'platform-cover-dark' : '',
      hasTheme && !hasCover ? 'platform-color-only' : '',
    ]"
    class="relative min-h-screen"
  >
    <!-- Background: cover image fixed behind everything -->
    <div
      v-if="hasCover"
      class="fixed inset-0 z-0 bg-cover bg-center bg-no-repeat"
      :style="coverBgStyle"
    />
    <!-- Default solid background when no cover -->
    <div v-if="!hasCover && !hasTheme" class="fixed inset-0 z-0 bg-gray-50 dark:bg-esmerald-dark" />

    <!-- Desktop sidebar (hidden on mobile) -->
    <div class="hidden md:block">
      <PlatformSidebar
        :is-collapsed="isCollapsed"
        :is-dark="isDark"
        @logout="handleLogout"
      />
    </div>

    <!-- Mobile top bar -->
    <div
      class="mobile-topbar sticky top-0 z-30 flex h-14 items-center justify-between border-b border-esmerald/[0.06] px-4 md:hidden"
      :class="hasCover ? '' : 'bg-white/80 backdrop-blur-xl dark:bg-esmerald-dark/90'"
    >
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
      <div class="h-8 w-8 shrink-0 overflow-hidden rounded-full">
        <img v-if="authStore.user?.avatar_display_url" :src="authStore.user.avatar_display_url" alt="Avatar" class="h-full w-full object-cover" />
        <div v-else class="flex h-full w-full items-center justify-center bg-esmerald text-xs font-bold text-white dark:bg-lemon dark:text-esmerald-dark">
          {{ authStore.userInitials }}
        </div>
      </div>
    </div>

    <!-- Mobile drawer -->
    <PlatformMobileDrawer
      :is-open="isMobileOpen"
      :is-dark="isDark"
      @close="closeMobile"
      @logout="handleLogout"
      @toggle-theme="toggle"
      @open-theme-picker="showThemePicker = true"
    />

    <!-- Main content -->
    <main
      :class="[
        'relative z-10 transition-all duration-300 ease-in-out',
        'px-4 py-6 sm:px-6 lg:px-8',
        isCollapsed ? 'md:ml-[64px]' : 'md:ml-[240px]',
      ]"
    >
      <div class="mx-auto max-w-6xl">
        <slot />
      </div>
    </main>

    <!-- Theme picker popover -->
    <Teleport to="body">
      <Transition name="theme-popover">
        <div
          v-if="showThemePicker"
          class="fixed inset-0 z-50 flex items-end justify-center bg-black/30 px-4 pb-4 backdrop-blur-sm sm:items-center sm:pb-0"
          @click.self="showThemePicker = false"
        >
          <div class="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-2xl dark:border-white/[0.06] dark:bg-esmerald sm:p-8">
            <div class="mb-5 flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-esmerald dark:text-white">Personalizar interfaz</h3>
                <p class="mt-1 text-xs text-green-light">Escoge un color y una imagen para hacer tuyo este espacio.</p>
              </div>
              <button type="button" class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-green-light transition hover:bg-esmerald-light hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-white" @click="showThemePicker = false">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <ThemePicker />
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { provide, watch, onMounted, onUnmounted, ref, computed } from 'vue'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformTheme } from '~/composables/usePlatformTheme'
import { usePlatformSidebar } from '~/composables/usePlatformSidebar'
import { usePlatformCustomTheme } from '~/composables/usePlatformCustomTheme'
import PlatformSidebar from '~/components/platform/PlatformSidebar.vue'
import PlatformMobileDrawer from '~/components/platform/PlatformMobileDrawer.vue'
import ThemePicker from '~/components/platform/ThemePicker.vue'

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

const {
  themeColor,
  coverImage,
  customCoverImageUrl,
  hasTheme,
  hasCover,
  isCoverDark,
  hydrate: hydrateCustomTheme,
} = usePlatformCustomTheme()

const showThemePicker = ref(false)

const coverBgStyle = computed(() => {
  const url = customCoverImageUrl.value || (coverImage.value ? `/static/cover_gallery/${coverImage.value}` : '')
  return url ? { backgroundImage: `url(${encodeURI(url)})` } : {}
})

authStore.hydrate()

onMounted(() => {
  hydrateTheme()
  hydrateSidebar()
  hydrateCustomTheme()
  setupResizeListener()
})

onUnmounted(() => {
  cleanupResizeListener()
})

provide('toggleSidebar', toggleSidebar)
provide('toggleTheme', toggle)
provide('showThemePicker', showThemePicker)

watch(() => route.fullPath, () => {
  closeMobile()
})

async function handleLogout() {
  authStore.logout()
  await navigateTo(localePath('/platform/login'))
}
</script>

<style scoped>
.theme-popover-enter-active,
.theme-popover-leave-active {
  transition: opacity 0.25s ease;
}
.theme-popover-enter-from,
.theme-popover-leave-to {
  opacity: 0;
}
</style>
