<template>
  <!-- Previous button — fixed left edge -->
  <button
    v-if="!isFirst && !hideLeft"
    class="nav-side nav-side--left group"
    :class="{ 'nav-blink': blinkPrev }"
    :title="prevTitle"
    @click="$emit('prev')"
  >
    <svg class="w-4 h-4 md:w-5 md:h-5 flex-shrink-0 transition-transform group-hover:-translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
    </svg>
    <span class="nav-label hidden md:inline text-xs font-medium">Anterior</span>
  </button>

  <!-- Next button — fixed right edge -->
  <button
    v-if="!isLast"
    class="nav-side nav-side--right group"
    :class="{ 'nav-blink': blinkNext }"
    :title="nextTitle"
    @click="$emit('next')"
  >
    <span class="nav-label hidden md:inline text-xs font-medium">Siguiente</span>
    <svg class="w-4 h-4 md:w-5 md:h-5 flex-shrink-0 transition-transform group-hover:translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
  hideLeft: { type: Boolean, default: false },
  blinkNext: { type: Boolean, default: false },
  blinkPrev: { type: Boolean, default: false },
});

defineEmits(['prev', 'next']);
</script>

<style scoped>
/* ── Mobile: edge tabs flush against screen border ── */
.nav-side {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 0.375rem;
  color: rgba(4, 120, 87, 0.8);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(6px);
  cursor: pointer;
  transition: all 0.25s ease;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.nav-side--left {
  left: 0;
  border-left: none;
  border-radius: 0 0.75rem 0.75rem 0;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.06);
}

.nav-side--right {
  right: 0;
  border-right: none;
  border-radius: 0.75rem 0 0 0.75rem;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.06);
}

.nav-side:active {
  transform: translateY(-50%) scale(0.92);
}

.nav-blink {
  animation: navDoublePulse 3.6s ease-in-out;
}

@keyframes navDoublePulse {
  0%   { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.3); }
  10%  { box-shadow: 0 0 14px 5px rgba(16, 185, 129, 0.25); }
  24%  { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
  38%  { box-shadow: 0 0 14px 5px rgba(16, 185, 129, 0.25); }
  54%  { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
  100% { box-shadow: none; }
}

/* ── Desktop: floating pill buttons with labels ── */
@media (min-width: 768px) {
  .nav-side {
    padding: 0.625rem 1rem;
    gap: 0.5rem;
    border: 1.5px solid rgba(16, 185, 129, 0.35);
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.75);
  }
  .nav-side:hover {
    color: #047857;
    background: rgba(255, 255, 255, 0.92);
    border-color: rgba(16, 185, 129, 0.5);
    box-shadow: 0 4px 14px rgba(16, 185, 129, 0.15);
  }
  .nav-side--left {
    left: 0.75rem;
    box-shadow: none;
  }
  .nav-side--right {
    right: 0.75rem;
    box-shadow: none;
  }
}
</style>
