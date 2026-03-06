<template>
  <div class="proposal-index fixed left-0 top-0 z-40 h-full flex items-center">
    <!-- Toggle button (always visible) -->
    <button
      class="index-toggle absolute left-4 top-4 z-50
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

    <!-- Index panel -->
    <nav
      class="index-panel ml-3 py-4 px-3 rounded-2xl
             bg-white/90 backdrop-blur-md shadow-xl border border-gray-100
             transition-all duration-300 max-h-[70vh] sm:max-h-[80vh] overflow-y-auto"
      :class="{ 'translate-x-[-120%]': !isOpen }"
    >
      <p class="text-[10px] uppercase tracking-[0.2em] text-emerald-600 font-medium mb-2 px-2">
        Índice
      </p>
      <ul class="space-y-0.5">
        <li
          v-for="(section, idx) in sections"
          :key="section.id"
          class="group"
        >
          <button
            class="w-full text-left px-2.5 py-1.5 rounded-xl text-sm transition-all duration-200 flex items-center gap-2"
            :class="idx === currentIndex
              ? 'bg-emerald-50 text-emerald-700 font-medium'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'"
            @click="$emit('navigate', idx); isOpen = false"
          >
            <span
              class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-medium flex-shrink-0 transition-colors"
              :class="idx === currentIndex
                ? 'bg-emerald-600 text-white'
                : 'bg-gray-200 text-gray-500 group-hover:bg-gray-300'"
            >
              {{ idx + 1 }}
            </span>
            <span class="leading-tight">{{ section.title }}</span>
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
});

const emit = defineEmits(['navigate', 'update:open']);

const isOpen = ref(typeof window !== 'undefined' && window.innerWidth >= 640);

watch(isOpen, (val) => emit('update:open', val), { immediate: true });
</script>

<style scoped>
.index-panel {
  min-width: 180px;
  max-width: 280px;
  scrollbar-width: none;
}

.index-panel::-webkit-scrollbar {
  display: none;
}
</style>
