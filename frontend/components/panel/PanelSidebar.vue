<template>
  <aside
    :class="[
      'fixed inset-y-0 left-0 z-30 flex flex-col border-r transition-all duration-300 ease-in-out',
      'border-border-default/[0.06] bg-surface dark:border-white/[0.06] dark:bg-primary-strong',
      isCollapsed ? 'w-[64px]' : 'w-[240px]',
    ]"
  >
    <div
      :class="[
        'flex h-16 shrink-0 items-center border-b border-border-default/[0.06] dark:border-white/[0.06]',
        isCollapsed ? 'justify-center px-2' : 'gap-3 px-5',
      ]"
    >
      <NuxtLink
        :to="localePath('/panel')"
        class="text-xl font-bold tracking-tight text-primary dark:text-white"
        :class="isCollapsed ? 'flex justify-center' : ''"
      >
        <span v-if="!isCollapsed">
          Project<span class="text-primary dark:text-accent">App.</span>
        </span>
        <span v-else class="text-base">
          P<span class="text-primary dark:text-accent">A</span>
        </span>
      </NuxtLink>
    </div>

    <nav class="flex-1 overflow-y-auto px-3 py-4">
      <div
        v-for="section in sections"
        :key="section.id"
        class="mb-5"
      >
        <p
          v-if="!isCollapsed"
          class="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest"
          :class="section.muted ? 'text-green-light/40' : 'text-green-light/60'"
        >
          {{ section.label }}
        </p>
        <div class="flex flex-col gap-0.5">
          <template
            v-for="(item, idx) in section.items"
            :key="item.divider ? `div-${section.id}-${idx}` : item.href + item.label"
          >
            <div
              v-if="item.divider"
              aria-hidden="true"
              :class="[
                'my-2 h-px bg-border-muted',
                isCollapsed ? 'mx-2' : 'mx-3',
              ]"
            />
            <SidebarItem
              v-else
              :item="item"
              :is-collapsed="isCollapsed"
              :is-active="isItemActive(item)"
              :disabled="item.disabled"
            />
          </template>
        </div>
      </div>
    </nav>

    <div class="shrink-0 border-t border-border-default/[0.06] p-3 dark:border-white/[0.06]">
      <!-- Identity chip -->
      <div
        :class="[
          'mb-3 flex items-center',
          isCollapsed ? 'justify-center' : 'gap-2 px-1',
        ]"
        :title="isCollapsed ? 'Internal admin' : undefined"
      >
        <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary dark:bg-surface-raised dark:text-text-subtle">
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
        <span v-if="!isCollapsed" class="truncate text-xs text-green-light">Internal admin</span>
      </div>

      <!-- Plataforma link -->
      <button
        type="button"
        :disabled="isBridging"
        :class="[
          'mb-2 flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm transition',
          'text-green-light hover:bg-primary-soft hover:text-primary',
          'dark:hover:bg-surface-raised dark:hover:text-white',
          isCollapsed ? 'justify-center' : '',
        ]"
        :title="isCollapsed ? 'Plataforma' : undefined"
        @click="goToPlatform('/platform/dashboard')"
      >
        <SidebarIcon name="external" class="h-4 w-4 shrink-0" />
        <span v-if="!isCollapsed" class="truncate">{{ isBridging ? 'Abriendo...' : 'Plataforma' }}</span>
      </button>

      <!-- Theme toggle with label (expanded only) -->
      <button
        v-if="!isCollapsed"
        type="button"
        class="mb-1.5 flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-green-light transition
               hover:bg-primary-soft hover:text-primary dark:hover:bg-surface-raised dark:hover:text-white"
        :aria-label="themeToggleLabel(isDark)"
        @click="$emit('toggle-theme')"
      >
        <svg v-if="isDark" class="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <svg v-else class="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
        <span class="truncate">{{ isDark ? 'Modo claro' : 'Modo oscuro' }}</span>
      </button>

      <!-- Bottom action row -->
      <div
        :class="[
          'flex items-center gap-1',
          isCollapsed ? 'flex-col' : 'justify-end',
        ]"
      >
        <!-- Icon-only theme toggle (collapsed only) -->
        <button
          v-if="isCollapsed"
          type="button"
          :class="sidebarActionClass"
          title="Light / dark mode"
          :aria-label="themeToggleLabel(isDark)"
          @click="$emit('toggle-theme')"
        >
          <svg v-if="isDark" class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
        </button>

        <!-- Collapse toggle -->
        <button
          v-if="toggleSidebar"
          type="button"
          :class="sidebarActionClass"
          :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
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
import { computed, inject } from 'vue'
import { getPanelNavSections } from '~/config/panelNav'
import { isPanelNavItemActive } from '~/utils/panelNavActive'
import { usePanelToPlatformBridge } from '~/composables/usePanelToPlatformBridge'
import { themeToggleLabel } from '~/composables/useDarkMode'
import SidebarIcon from '~/components/platform/SidebarIcon.vue'
import SidebarItem from '~/components/platform/SidebarItem.vue'

defineEmits(['toggle-theme'])

const { goToPlatform, isBridging } = usePanelToPlatformBridge()

const props = defineProps({
  isCollapsed: { type: Boolean, default: false },
  isDark: { type: Boolean, default: false },
})

const localePath = useLocalePath()
const route = useRoute()

const toggleSidebar = inject('togglePanelSidebar', null)

const sections = computed(() => getPanelNavSections(localePath))

function isItemActive(item) {
  return isPanelNavItemActive(route.path, item)
}

const sidebarActionClass = computed(() => [
  'flex h-8 w-8 items-center justify-center rounded-lg text-green-light transition',
  'hover:bg-primary-soft hover:text-primary',
  'dark:hover:bg-surface-raised dark:hover:text-white',
])
</script>
