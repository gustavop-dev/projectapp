<template>
  <div class="fixed top-0 left-0 w-full z-[60] pointer-events-none">
    <div
      class="h-[3px] bg-gradient-to-r from-emerald-500 to-emerald-400 transition-[width] duration-150 ease-out"
      :style="{ width: `${progress}%` }"
    />
  </div>
  <Transition name="fade">
    <div
      v-if="remainingMinutes > 0 && progress > 5 && progress < 95"
      class="fixed top-4 right-4 z-40 px-3 py-1.5 rounded-full bg-white/90 backdrop-blur-sm shadow-sm border border-border-default/60 text-xs text-text-muted pointer-events-none"
    >
      ~{{ remainingMinutes }} min {{ lang === 'en' ? 'remaining' : 'restantes' }}
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  readTimeMinutes: { type: Number, default: 0 },
  lang: { type: String, default: 'es' },
});

const progress = ref(0);

function updateProgress() {
  const scrollTop = window.scrollY || document.documentElement.scrollTop;
  const docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
  if (docHeight <= 0) {
    progress.value = 0;
    return;
  }
  progress.value = Math.min(100, Math.max(0, (scrollTop / docHeight) * 100));
}

const remainingMinutes = computed(() => {
  if (!props.readTimeMinutes) return 0;
  const remaining = Math.ceil((1 - progress.value / 100) * props.readTimeMinutes);
  return Math.max(0, remaining);
});

onMounted(() => {
  window.addEventListener('scroll', updateProgress, { passive: true });
  updateProgress();
});

onUnmounted(() => {
  window.removeEventListener('scroll', updateProgress);
});
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
