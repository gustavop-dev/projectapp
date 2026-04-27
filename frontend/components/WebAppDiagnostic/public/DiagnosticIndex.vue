<template>
  <div class="diagnostic-index fixed left-0 top-0 z-50 pointer-events-none">
    <button
      data-testid="diagnostic-index-toggle"
      class="index-toggle absolute left-4 top-4 z-50 pointer-events-auto
             w-10 h-10 rounded-full
             bg-surface dark:bg-primary-strong shadow-lg
             border border-input-border/10 dark:border-input-border/25
             flex items-center justify-center
             text-text-brand dark:text-text-brand
             hover:bg-primary/5 dark:hover:bg-primary/80
             transition-colors"
      @click="isOpen = !isOpen"
    >
      <svg v-if="!isOpen" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
      <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>

    <Transition name="idx-fade">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[9990] bg-surface/60 dark:bg-black/60 backdrop-blur-[3px] pointer-events-auto"
        @click="isOpen = false"
      />
    </Transition>

    <nav
      data-testid="diagnostic-index-panel"
      class="index-panel z-[9999]
             bg-surface/95 dark:bg-primary/95 backdrop-blur-md overflow-y-auto transition-all duration-300
             fixed inset-0 py-4 px-4
             sm:relative sm:inset-auto sm:ml-3 sm:py-4 sm:px-3 sm:mt-[50vh] sm:-translate-y-1/2
             sm:rounded-2xl sm:shadow-xl sm:border sm:border-border-muted dark:sm:border-input-border/15
             sm:max-h-[80vh]"
      :class="isOpen ? 'pointer-events-auto' : 'pointer-events-none translate-x-[-120%]'"
    >
      <button
        class="sm:hidden absolute left-4 top-4 z-10
               w-10 h-10 rounded-full
               bg-surface dark:bg-primary-strong shadow-lg
               border border-input-border/10 dark:border-input-border/25
               flex items-center justify-center
               text-text-brand dark:text-text-brand
               hover:bg-primary/5 dark:hover:bg-primary/80
               transition-colors"
        @click="isOpen = false"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <p class="text-[10px] uppercase tracking-[0.2em] text-text-brand dark:text-text-brand font-medium mb-2 px-2 mt-14 sm:mt-0">
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
              ? 'bg-primary/5 dark:bg-primary-soft/10 text-text-brand dark:text-text-brand font-medium'
              : 'text-text-muted dark:text-text-brand/60 hover:text-text-default dark:hover:text-text-brand hover:bg-gray-50 dark:hover:bg-primary-soft/5'"
            @click="$emit('navigate', idx); isOpen = false"
          >
            <span
              class="w-6 h-6 sm:w-5 sm:h-5 rounded-full flex items-center justify-center text-[11px] sm:text-[10px] font-medium flex-shrink-0 transition-colors"
              :class="idx === currentIndex
                ? 'bg-primary text-accent dark:bg-accent-soft dark:text-text-brand'
                : visitedIds.has(section.id)
                  ? 'bg-primary/10 dark:bg-primary-soft/15 text-text-brand dark:text-text-brand'
                  : 'bg-gray-200 dark:bg-primary-soft/10 text-text-muted dark:text-text-brand/60 group-hover:bg-gray-300 dark:group-hover:bg-primary-soft/20'"
            >
              <svg
                v-if="visitedIds.has(section.id) && idx !== currentIndex"
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
import { ref } from 'vue';

defineProps({
  sections: {
    type: Array,
    default: () => [],
  },
  currentIndex: {
    type: Number,
    default: 0,
  },
  visitedIds: {
    type: Set,
    default: () => new Set(),
  },
});

defineEmits(['navigate']);

const isOpen = ref(false);
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
