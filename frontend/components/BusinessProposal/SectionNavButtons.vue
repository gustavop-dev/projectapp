<template>
  <div class="section-nav-buttons w-full px-6 sm:px-8 py-8 sm:py-12">
    <div class="max-w-3xl mx-auto flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4"
         :class="isFirst ? 'justify-end' : 'justify-between'">
      <!-- Previous button -->
      <button
        v-if="!isFirst"
        class="nav-btn group flex items-center gap-3 px-5 sm:px-7 py-3 sm:py-3.5
               border-2 border-emerald-600/25 rounded-full
               text-emerald-700 bg-white/60 backdrop-blur-sm
               hover:bg-emerald-50 hover:border-emerald-600/50
               active:scale-[0.97] transition-all duration-200"
        @click="$emit('prev')"
      >
        <svg class="w-5 h-5 flex-shrink-0 transition-transform group-hover:-translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        <span class="flex flex-col items-start leading-tight min-w-0">
          <span class="text-[10px] uppercase tracking-wider text-emerald-600/60 font-medium">Anterior</span>
          <span class="text-sm font-medium truncate max-w-[180px]">{{ prevTitle }}</span>
        </span>
      </button>

      <!-- Next button -->
      <button
        v-if="!isLast"
        class="nav-btn group flex items-center gap-3 px-5 sm:px-7 py-3 sm:py-3.5
               border-2 border-emerald-600/25 rounded-full
               text-emerald-700 bg-white/60 backdrop-blur-sm
               hover:bg-emerald-50 hover:border-emerald-600/50
               active:scale-[0.97] transition-all duration-200 ml-auto"
        @click="$emit('next')"
      >
        <span class="flex flex-col items-end leading-tight min-w-0">
          <span class="text-[10px] uppercase tracking-wider text-emerald-600/60 font-medium">Siguiente</span>
          <span class="text-sm font-medium truncate max-w-[180px]">{{ nextTitle }}</span>
        </span>
        <svg class="w-5 h-5 flex-shrink-0 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </button>

      <!-- Last section: closing button -->
      <button
        v-if="isLast"
        class="nav-btn group flex items-center justify-center gap-2 px-5 sm:px-7 py-3 sm:py-3.5
               border-2 border-emerald-600/25 rounded-full
               text-emerald-700 bg-white/60 backdrop-blur-sm
               hover:bg-emerald-50 hover:border-emerald-600/50
               active:scale-[0.97] transition-all duration-200 ml-auto"
        disabled
      >
        <span class="text-sm font-medium text-emerald-600/50">Fin de la propuesta</span>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  prevTitle: { type: String, default: '' },
  nextTitle: { type: String, default: '' },
  isFirst: { type: Boolean, default: false },
  isLast: { type: Boolean, default: false },
});

defineEmits(['prev', 'next']);
</script>

<style scoped>
.nav-btn {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.nav-btn:hover {
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.12);
}
</style>
