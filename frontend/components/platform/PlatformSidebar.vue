<template>
  <aside
    :class="[
      'fixed inset-y-0 left-0 z-30 flex flex-col border-r transition-all duration-300 ease-in-out',
      'border-esmerald/[0.06] bg-white dark:border-white/[0.06] dark:bg-esmerald-dark',
      isCollapsed ? 'w-[64px]' : 'w-[240px]',
    ]"
  >
    <!-- Logo header -->
    <div
      :class="[
        'flex h-16 shrink-0 items-center border-b border-esmerald/[0.06] dark:border-white/[0.06]',
        isCollapsed ? 'justify-center px-2' : 'gap-3 px-5',
      ]"
    >
      <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-esmerald text-xs font-bold text-white dark:bg-lemon dark:text-esmerald-dark">
        PA
      </div>
      <span
        v-if="!isCollapsed"
        class="text-base font-bold tracking-tight text-esmerald dark:text-white"
      >
        Project<span class="text-green-light dark:text-lemon">App.</span>
      </span>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto px-3 py-4">
      <!-- Primary section -->
      <div class="mb-5">
        <p
          v-if="!isCollapsed"
          class="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-green-light/60"
        >
          Principal
        </p>
        <SidebarItem
          v-for="item in primaryItems"
          :key="item.href"
          :item="item"
          :is-collapsed="isCollapsed"
          :is-active="isActive(item.href)"
          :disabled="item.disabled"
        />
      </div>

      <!-- Projects section (placeholder) -->
      <div class="mb-5">
        <p
          v-if="!isCollapsed"
          class="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-green-light/60"
        >
          Proyectos
        </p>
        <SidebarItem
          v-for="item in projectItems"
          :key="item.href"
          :item="item"
          :is-collapsed="isCollapsed"
          :is-active="isActive(item.href)"
          :disabled="item.disabled"
        />
      </div>

      <!-- Admin section -->
      <div v-if="authStore.isAdmin" class="mb-5">
        <p
          v-if="!isCollapsed"
          class="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-green-light/60"
        >
          Administración
        </p>
        <SidebarItem
          v-for="item in adminItems"
          :key="item.href"
          :item="item"
          :is-collapsed="isCollapsed"
          :is-active="isActive(item.href)"
          :disabled="item.disabled"
        />
      </div>
    </nav>

    <!-- User footer -->
    <div class="shrink-0 border-t border-esmerald/[0.06] p-3 dark:border-white/[0.06]">
      <div
        :class="[
          'flex items-center rounded-xl transition',
          isCollapsed ? 'justify-center p-2' : 'gap-3 p-2',
        ]"
      >
        <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-esmerald text-xs font-bold text-white dark:bg-lemon dark:text-esmerald-dark">
          {{ authStore.userInitials }}
        </div>
        <div v-if="!isCollapsed" class="min-w-0 flex-1">
          <p class="truncate text-sm font-medium text-esmerald dark:text-white">{{ authStore.displayName }}</p>
          <p class="truncate text-xs text-green-light">{{ userSubtitle }}</p>
        </div>
      </div>

      <!-- Action buttons -->
      <div
        :class="[
          'mt-2 flex',
          isCollapsed ? 'flex-col items-center gap-1' : 'items-center gap-1',
        ]"
      >
        <NuxtLink
          :to="localePath('/platform/profile')"
          :class="sidebarActionClass"
          :title="isCollapsed ? 'Perfil' : undefined"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
        </NuxtLink>

        <button
          type="button"
          :class="sidebarActionClass"
          :title="isCollapsed ? 'Tema' : undefined"
          @click="toggleTheme"
        >
          <svg v-if="isDark" class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
          <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>
        </button>

        <button
          type="button"
          :class="sidebarActionClass"
          :title="isCollapsed ? 'Salir' : undefined"
          @click="$emit('logout')"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
        </button>

        <button
          type="button"
          :class="[sidebarActionClass, 'ml-auto']"
          :title="isCollapsed ? 'Expandir' : 'Colapsar'"
          @click="toggleSidebar"
        >
          <svg
            class="h-4 w-4 transition-transform duration-300"
            :class="isCollapsed ? 'rotate-180' : ''"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed, inject, onMounted, onUnmounted } from 'vue'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformNotificationsStore } from '~/stores/platform-notifications'
import SidebarItem from '~/components/platform/SidebarItem.vue'

const localePath = useLocalePath()

defineEmits(['logout'])

const props = defineProps({
  isCollapsed: { type: Boolean, default: false },
  isDark: { type: Boolean, default: true },
})

const toggleSidebar = inject('toggleSidebar')
const toggleTheme = inject('toggleTheme')

const route = useRoute()
const authStore = usePlatformAuthStore()
const notifStore = usePlatformNotificationsStore()

onMounted(() => { notifStore.startPolling(30000) })
onUnmounted(() => { notifStore.stopPolling() })

const userSubtitle = computed(() =>
  authStore.user?.company_name || authStore.user?.email || 'Portal ProjectApp',
)

const sidebarActionClass = computed(() => [
  'flex h-8 w-8 items-center justify-center rounded-lg text-green-light transition',
  'hover:bg-esmerald-light hover:text-esmerald',
  'dark:hover:bg-white/[0.06] dark:hover:text-white',
])

const lp = (path) => localePath(path)

const primaryItems = computed(() => [
  {
    label: 'Dashboard',
    href: lp('/platform/dashboard'),
    icon: 'dashboard',
  },
  {
    label: 'Notificaciones',
    href: lp('/platform/notifications'),
    icon: 'bell',
    badge: notifStore.unreadCount,
  },
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

const adminItems = computed(() => [
  { label: 'Clientes', href: lp('/platform/clients'), icon: 'users' },
])

function isActive(href) {
  const cleanPath = route.path.replace(/^\/[a-z]{2}-[a-z]{2}/, '')
  const cleanHref = href.replace(/^\/[a-z]{2}-[a-z]{2}/, '')
  return cleanPath === cleanHref || cleanPath.startsWith(`${cleanHref}/`)
}
</script>
