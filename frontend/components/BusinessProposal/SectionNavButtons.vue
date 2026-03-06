<template>
  <!-- Previous button — fixed left edge -->
  <button
    v-if="!isFirst"
    class="nav-side nav-side--left group"
    :title="prevTitle"
    @click="$emit('prev')"
  >
    <svg class="w-5 h-5 sm:w-6 sm:h-6 flex-shrink-0 transition-transform group-hover:-translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
    </svg>
    <span class="nav-label hidden md:flex flex-col items-start leading-tight min-w-0">
      <span class="text-[10px] uppercase tracking-wider text-emerald-600/60 font-medium">Anterior</span>
      <span class="text-xs font-medium truncate max-w-[120px]">{{ prevTitle }}</span>
    </span>
  </button>

  <!-- Next button — fixed right edge -->
  <button
    v-if="!isLast"
    class="nav-side nav-side--right group"
    :title="nextTitle"
    @click="$emit('next')"
  >
    <span class="nav-label hidden md:flex flex-col items-end leading-tight min-w-0">
      <span class="text-[10px] uppercase tracking-wider text-emerald-600/60 font-medium">Siguiente</span>
      <span class="text-xs font-medium truncate max-w-[120px]">{{ nextTitle }}</span>
    </span>
    <svg class="w-5 h-5 sm:w-6 sm:h-6 flex-shrink-0 transition-transform group-hover:translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
    </svg>
  </button>
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
.nav-side {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  z-index: 40;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem;
  border: 2px solid rgba(16, 185, 129, 0.2);
  border-radius: 9999px;
  color: #047857;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-side:hover {
  background: rgba(236, 253, 245, 0.9);
  border-color: rgba(16, 185, 129, 0.45);
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.15);
}

.nav-side:active {
  transform: translateY(-50%) scale(0.95);
}

.nav-side--left {
  left: 0.5rem;
}

.nav-side--right {
  right: 0.5rem;
}

@media (min-width: 640px) {
  .nav-side {
    padding: 0.75rem;
  }
  .nav-side--left {
    left: 0.75rem;
  }
  .nav-side--right {
    right: 0.75rem;
  }
}

@media (min-width: 768px) {
  .nav-side {
    padding: 0.625rem 1rem;
    border-radius: 9999px;
  }
}
</style>
