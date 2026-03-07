<template>
  <div class="proposal-index fixed left-0 top-0 z-50 pointer-events-none">
    <!-- Toggle button (always visible) -->
    <button
      data-testid="index-toggle"
      class="index-toggle absolute left-4 top-4 z-50 pointer-events-auto
             w-10 h-10 rounded-full bg-white/90 backdrop-blur-sm shadow-lg
             flex items-center justify-center text-emerald-600
             hover:bg-emerald-50 transition-colors"
      @click="isOpen = !isOpen"
    >
      <svg v-if="!isOpen" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
      <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>

    <!-- Blur backdrop when index is open -->
    <Transition name="idx-fade">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[9990] bg-white/60 backdrop-blur-[3px] sm:bg-white/60 pointer-events-auto"
        @click="isOpen = false"
      />
    </Transition>

    <!-- Index panel: fullscreen on mobile, floating on desktop -->
    <nav
      data-testid="index-panel"
      class="index-panel z-[9999] bg-white/95 backdrop-blur-md overflow-y-auto transition-all duration-300
             fixed inset-0 py-4 px-4
             sm:relative sm:inset-auto sm:ml-3 sm:py-4 sm:px-3 sm:mt-[50vh] sm:-translate-y-1/2
             sm:rounded-2xl sm:shadow-xl sm:border sm:border-gray-100
             sm:max-h-[80vh]"
      :class="isOpen ? 'pointer-events-auto' : 'pointer-events-none translate-x-[-120%]'"
    >
      <!-- Mobile close button — same style/position as hamburger toggle -->
      <button
        class="sm:hidden absolute left-4 top-4 z-10
               w-10 h-10 rounded-full bg-white/90 backdrop-blur-sm shadow-lg
               flex items-center justify-center text-emerald-600
               hover:bg-emerald-50 transition-colors"
        @click="isOpen = false"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <p class="text-[10px] uppercase tracking-[0.2em] text-emerald-600 font-medium mb-2 px-2 mt-14 sm:mt-0">
        Índice
      </p>
      <ul class="space-y-0.5">
        <li
          v-for="(section, idx) in sections"
          :key="section.id"
          class="group"
        >
          <button
            class="w-full text-left px-2.5 py-2 sm:py-1.5 rounded-xl text-sm transition-all duration-200 flex items-center gap-2"
            :class="idx === currentIndex
              ? 'bg-emerald-50 text-emerald-700 font-medium'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'"
            @click="$emit('navigate', idx); isOpen = false"
          >
            <span
              class="w-6 h-6 sm:w-5 sm:h-5 rounded-full flex items-center justify-center text-[11px] sm:text-[10px] font-medium flex-shrink-0 transition-colors"
              :class="idx === currentIndex
                ? 'bg-emerald-600 text-white'
                : visitedPanelIds.has(section.id)
                  ? 'bg-emerald-100 text-emerald-600'
                  : 'bg-gray-200 text-gray-500 group-hover:bg-gray-300'"
            >
              <svg
                v-if="visitedPanelIds.has(section.id) && idx !== currentIndex"
                class="w-3 h-3"
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
              <span v-else>{{ idx + 1 }}</span>
            </span>
            <span class="leading-tight text-base sm:text-sm">{{ section.title }}</span>
          </button>
        </li>
      </ul>
    </nav>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

defineProps({
  sections: {
    type: Array,
    default: () => [],
  },
  currentIndex: {
    type: Number,
    default: 0,
  },
  visitedPanelIds: {
    type: Set,
    default: () => new Set(),
  },
});

const emit = defineEmits(['navigate', 'update:open']);

const isOpen = ref(false);

watch(isOpen, (val) => emit('update:open', val), { immediate: true });
</script>

<style scoped>
.index-panel {
  scrollbar-width: none;
}

@media (min-width: 640px) {
  .index-panel {
    min-width: 180px;
    max-width: 280px;
  }
}

.index-panel::-webkit-scrollbar {
  display: none;
}

.idx-fade-enter-active,
.idx-fade-leave-active {
  transition: opacity 0.25s ease;
}
.idx-fade-enter-from,
.idx-fade-leave-to {
  opacity: 0;
}
</style>
