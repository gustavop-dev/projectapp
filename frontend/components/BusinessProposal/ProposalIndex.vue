<template>
  <div class="proposal-index fixed left-0 top-0 z-50 pointer-events-none">
    <!-- Toggle button (always visible) -->
    <button
      data-testid="index-toggle"
      class="index-toggle absolute left-4 top-4 z-50 pointer-events-auto
             w-10 h-10 rounded-full bg-surface/90 backdrop-blur-sm shadow-lg
             flex items-center justify-center text-text-brand
             hover:bg-primary/5 transition-colors"
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
        class="fixed inset-0 z-[9990] bg-surface/60 backdrop-blur-[3px] sm:bg-surface/60 pointer-events-auto"
        @click="isOpen = false"
      />
    </Transition>

    <!-- Index panel: fullscreen on mobile, floating on desktop -->
    <nav
      data-testid="index-panel"
      class="index-panel z-[9999] bg-surface/95 backdrop-blur-md overflow-y-auto transition-all duration-300
             fixed inset-0 py-4 px-4
             sm:relative sm:inset-auto sm:ml-3 sm:py-4 sm:px-3 sm:mt-[50vh] sm:-translate-y-1/2
             sm:rounded-2xl sm:shadow-xl sm:border sm:border-border-muted
             sm:max-h-[80vh]"
      :class="isOpen ? 'pointer-events-auto' : 'pointer-events-none translate-x-[-120%]'"
    >
      <!-- Mobile close button — same style/position as hamburger toggle -->
      <button
        class="sm:hidden absolute left-4 top-4 z-10
               w-10 h-10 rounded-full bg-surface/90 backdrop-blur-sm shadow-lg
               flex items-center justify-center text-text-brand
               hover:bg-primary/5 transition-colors"
        @click="isOpen = false"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <p class="text-[10px] uppercase tracking-[0.2em] text-text-brand font-medium mb-2 px-2 mt-14 sm:mt-0">
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
              ? 'bg-primary/5 text-text-brand font-medium'
              : 'text-text-muted hover:text-text-default hover:bg-surface-muted'"
            @click="$emit('navigate', idx); isOpen = false"
          >
            <span
              class="w-6 h-6 sm:w-5 sm:h-5 rounded-full flex items-center justify-center text-[11px] sm:text-[10px] font-medium flex-shrink-0 transition-colors"
              :class="idx === currentIndex
                ? 'bg-primary text-accent'
                : visitedPanelIds.has(section.id)
                  ? 'bg-primary/10 text-text-brand'
                  : 'bg-gray-200 text-text-muted group-hover:bg-gray-300'"
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

      <!-- Switch view mode -->
      <div class="mt-4 px-2 space-y-2">
        <button
          v-if="viewMode === 'executive'"
          data-testid="switch-to-detailed-btn"
          class="sidebar-switch-detailed-btn w-full flex items-center gap-2 px-3 py-2.5 bg-primary text-on-primary rounded-xl text-sm font-medium
                 hover:bg-primary/90 transition-colors shadow-sm"
          @click="$emit('switchToDetailed'); isOpen = false"
        >
          <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
          <span class="leading-tight">{{ language === 'en' ? 'View Full Proposal' : 'Ver Propuesta Completa' }}</span>
        </button>
        <button
          data-testid="back-to-gateway-btn"
          class="w-full flex items-center gap-2 px-3 py-2.5 border border-border-default text-text-muted rounded-xl text-sm font-medium
                 hover:bg-surface-muted hover:border-gray-300 transition-colors"
          @click="$emit('backToGateway'); isOpen = false"
        >
          <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
          </svg>
          <span class="leading-tight">{{ language === 'en' ? 'Change view' : 'Cambiar vista' }}</span>
        </button>
      </div>
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
  viewMode: {
    type: String,
    default: '',
  },
  language: {
    type: String,
    default: 'es',
  },
});

const emit = defineEmits(['navigate', 'update:open', 'switchToDetailed', 'backToGateway']);

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
