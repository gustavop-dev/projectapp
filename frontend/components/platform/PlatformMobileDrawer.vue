<template>
  <Teleport to="body">
    <Transition name="drawer-overlay">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm md:hidden"
        @click="$emit('close')"
      />
    </Transition>
    <Transition name="drawer-slide">
      <aside
        v-if="isOpen"
        :class="[
          'fixed inset-y-0 left-0 z-50 flex w-[280px] flex-col border-r md:hidden',
          'border-esmerald/[0.06] bg-white dark:border-white/[0.06] dark:bg-esmerald-dark',
        ]"
      >
        <!-- Header -->
        <div class="flex h-16 shrink-0 items-center justify-between border-b border-esmerald/[0.06] px-5 dark:border-white/[0.06]">
          <div class="flex items-center gap-3">
            <span class="text-xl font-bold tracking-tight text-esmerald dark:text-white">
              Project<span class="text-esmerald dark:text-lemon">App.</span>
            </span>
          </div>
          <button
            type="button"
            class="flex h-9 w-9 items-center justify-center rounded-full text-green-light transition hover:bg-esmerald-light hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-white"
            @click="$emit('close')"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Navigation (reuse sidebar items) -->
        <nav class="flex-1 overflow-y-auto px-3 py-4">
          <div class="mb-5">
            <p class="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-green-light/60">Principal</p>
            <SidebarItem
              v-for="item in primaryItems"
              :key="item.href"
              :item="item"
              :is-collapsed="false"
              :is-active="isActive(item.href)"
              :disabled="item.disabled"
              @click="$emit('close')"
            />
          </div>

          <div class="mb-5">
            <p class="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-green-light/60">Proyectos</p>
            <SidebarItem
              v-for="item in projectItems"
              :key="item.href"
              :item="item"
              :is-collapsed="false"
              :is-active="isActive(item.href)"
              :disabled="item.disabled"
              @click="$emit('close')"
            />
          </div>

          <div class="mb-5">
            <p class="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-green-light/60">Cuenta</p>
            <SidebarItem
              v-for="item in accountItems"
              :key="item.href"
              :item="item"
              :is-collapsed="false"
              :is-active="isActive(item.href)"
              :disabled="item.disabled"
              @click="$emit('close')"
            />
          </div>

          <div v-if="authStore.isAdmin" class="mb-5">
            <p class="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-green-light/60">Administración</p>
            <SidebarItem
              v-for="item in adminItems"
              :key="item.href"
              :item="item"
              :is-collapsed="false"
              :is-active="isActive(item.href)"
              :disabled="item.disabled"
              @click="$emit('close')"
            />
          </div>
        </nav>

        <!-- User footer -->
        <div class="shrink-0 border-t border-esmerald/[0.06] p-4 dark:border-white/[0.06]">
          <div class="flex items-center gap-3 rounded-xl p-2">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-esmerald text-xs font-bold text-white dark:bg-lemon dark:text-esmerald-dark">
              {{ authStore.userInitials }}
            </div>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-esmerald dark:text-white">{{ authStore.displayName }}</p>
              <p class="truncate text-xs text-green-light">{{ userSubtitle }}</p>
            </div>
          </div>

          <div class="mt-2 flex items-center gap-1">
            <button
              type="button"
              class="flex h-9 w-9 items-center justify-center rounded-lg text-green-light transition hover:bg-esmerald-light hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-white"
              @click="$emit('toggleTheme')"
            >
              <svg v-if="isDark" class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
              <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>
            </button>

            <button
              type="button"
              class="ml-auto rounded-full border border-esmerald/10 px-4 py-2 text-sm text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white"
              @click="$emit('logout')"
            >
              Salir
            </button>
          </div>
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformNotificationsStore } from '~/stores/platform-notifications'
import SidebarItem from '~/components/platform/SidebarItem.vue'

const localePath = useLocalePath()
const lp = (path) => localePath(path)

defineEmits(['close', 'logout', 'toggleTheme'])

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  isDark: { type: Boolean, default: true },
})

const route = useRoute()
const authStore = usePlatformAuthStore()
const notifStore = usePlatformNotificationsStore()

const userSubtitle = computed(() =>
  authStore.user?.company_name || authStore.user?.email || 'Portal ProjectApp',
)

const primaryItems = computed(() => [
  { label: 'Dashboard', href: lp('/platform/dashboard'), icon: 'dashboard' },
  { label: 'Notificaciones', href: lp('/platform/notifications'), icon: 'bell', badge: notifStore.unreadCount },
])

const projectItems = computed(() => {
  if (authStore.isAdmin) {
    return [
      { label: 'Proyectos', href: lp('/platform/projects'), icon: 'folder' },
      { label: 'Tablero', href: lp('/platform/board'), icon: 'board' },
      { label: 'Solicitudes', href: lp('/platform/changes'), icon: 'refresh' },
      { label: 'Bugs', href: lp('/platform/bugs'), icon: 'bug' },
      { label: 'Entregables', href: lp('/platform/deliverables'), icon: 'file' },
      { label: 'Pagos', href: lp('/platform/payments'), icon: 'credit-card' },
    ]
  }
  return [
    { label: 'Mis proyectos', href: lp('/platform/projects'), icon: 'folder' },
    { label: 'Tablero', href: lp('/platform/board'), icon: 'board' },
    { label: 'Solicitudes', href: lp('/platform/changes'), icon: 'refresh' },
    { label: 'Bugs', href: lp('/platform/bugs'), icon: 'bug' },
    { label: 'Entregables', href: lp('/platform/deliverables'), icon: 'file' },
    { label: 'Pagos', href: lp('/platform/payments'), icon: 'credit-card' },
  ]
})

const accountItems = computed(() => [
  { label: 'Configuración', href: lp('/platform/profile'), icon: 'settings' },
])

const adminItems = computed(() => [
  { label: 'Clientes', href: lp('/platform/clients'), icon: 'users' },
])

const projectSubModules = {
  board: '/platform/board',
  changes: '/platform/changes',
  bugs: '/platform/bugs',
  deliverables: '/platform/deliverables',
  payments: '/platform/payments',
}

function isActive(href) {
  const cleanPath = route.path.replace(/^\/[a-z]{2}-[a-z]{2}/, '')
  const cleanHref = href.replace(/^\/[a-z]{2}-[a-z]{2}/, '')

  const projectSubMatch = cleanPath.match(/^\/platform\/projects\/\d+\/(\w+)/)
  if (projectSubMatch) {
    const subSection = projectSubMatch[1]
    const mappedModule = projectSubModules[subSection]
    if (mappedModule) {
      return cleanHref === mappedModule
    }
  }

  return cleanPath === cleanHref || cleanPath.startsWith(`${cleanHref}/`)
}
</script>

<style scoped>
.drawer-overlay-enter-active,
.drawer-overlay-leave-active {
  transition: opacity 0.25s ease;
}
.drawer-overlay-enter-from,
.drawer-overlay-leave-to {
  opacity: 0;
}

.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.drawer-slide-enter-from,
.drawer-slide-leave-to {
  transform: translateX(-100%);
}
</style>
