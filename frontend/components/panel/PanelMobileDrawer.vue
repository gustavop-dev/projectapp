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
        <div class="flex h-16 shrink-0 items-center justify-between border-b border-esmerald/[0.06] px-5 dark:border-white/[0.06]">
          <span class="text-xl font-bold tracking-tight text-esmerald dark:text-white">
            Project<span class="text-esmerald dark:text-lemon">App.</span>
          </span>
          <button
            type="button"
            class="flex h-9 w-9 items-center justify-center rounded-full text-green-light transition hover:bg-esmerald-light hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-white"
            @click="$emit('close')"
          >
            <span class="sr-only">Close menu</span>
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <nav class="flex-1 overflow-y-auto px-3 py-4">
          <div
            v-for="section in sections"
            :key="section.id"
            class="mb-5"
          >
            <p
              class="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest"
              :class="section.muted ? 'text-green-light/40' : 'text-green-light/60'"
            >
              {{ section.label }}
            </p>
            <SidebarItem
              v-for="item in section.items"
              :key="item.href + item.label"
              :item="item"
              :is-collapsed="false"
              :is-active="isItemActive(item)"
              :disabled="item.disabled"
            />
          </div>
        </nav>

        <div class="shrink-0 border-t border-esmerald/[0.06] p-4 dark:border-white/[0.06]">
          <p class="truncate text-xs text-green-light">Internal admin</p>

          <button
            type="button"
            :disabled="isBridging"
            class="mt-2 flex h-9 w-full items-center justify-center gap-2 rounded-lg text-sm font-medium text-green-light transition hover:bg-esmerald-light hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-white"
            @click="goToPlatform('/platform/dashboard')"
          >
            <SidebarIcon name="external" class="h-4 w-4 shrink-0" />
            {{ isBridging ? 'Abriendo...' : 'Plataforma' }}
          </button>

          <button
            type="button"
            class="mt-2 flex h-9 w-full items-center justify-center rounded-lg text-sm font-medium text-green-light transition hover:bg-esmerald-light hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-white"
            @click="$emit('close'); $emit('toggle-theme')"
          >
            Toggle theme
          </button>
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { getPanelNavSections } from '~/config/panelNav'
import { isPanelNavItemActive } from '~/utils/panelNavActive'
import { usePanelToPlatformBridge } from '~/composables/usePanelToPlatformBridge'
import SidebarIcon from '~/components/platform/SidebarIcon.vue'
import SidebarItem from '~/components/platform/SidebarItem.vue'

defineEmits(['close', 'toggle-theme'])

const { goToPlatform, isBridging } = usePanelToPlatformBridge()

defineProps({
  isOpen: { type: Boolean, default: false },
})

const localePath = useLocalePath()
const route = useRoute()

const sections = computed(() => getPanelNavSections(localePath))

function isItemActive(item) {
  return isPanelNavItemActive(route.path, item)
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
