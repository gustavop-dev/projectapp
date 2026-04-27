<template>
  <Teleport to="body">
    <Transition name="fade-modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[9990] bg-black/50 backdrop-blur-sm p-3 sm:p-6 flex"
        @click.self="close"
      >
        <div class="bg-surface rounded-2xl shadow-2xl flex flex-col flex-1 min-h-0 overflow-hidden">
          <div class="flex items-center justify-between gap-3 px-5 sm:px-7 py-3 border-b border-border-muted flex-shrink-0">
            <div class="flex items-center gap-3 min-w-0">
              <h3 class="text-base font-semibold text-text-default truncate">{{ title }}</h3>
              <span class="hidden md:inline-block text-xs text-text-subtle">Presiona ESC para cerrar</span>
            </div>
            <button
              type="button"
              class="w-9 h-9 flex items-center justify-center rounded-lg text-text-subtle hover:text-text-default hover:bg-surface-raised transition-colors flex-shrink-0"
              aria-label="Cerrar vista previa"
              @click="close"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="flex-1 min-h-0 overflow-y-auto px-5 sm:px-10 py-6 sm:py-8">
            <slot />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { watch, onUnmounted } from 'vue';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: 'Vista previa' },
});
const emit = defineEmits(['update:modelValue']);

function close() {
  emit('update:modelValue', false);
}

function onKeydown(event) {
  if (event.key === 'Escape') close();
}

watch(
  () => props.modelValue,
  (open) => {
    if (typeof window === 'undefined') return;
    if (open) {
      window.addEventListener('keydown', onKeydown);
      document.body.style.overflow = 'hidden';
    } else {
      window.removeEventListener('keydown', onKeydown);
      document.body.style.overflow = '';
    }
  },
);

onUnmounted(() => {
  if (typeof window === 'undefined') return;
  window.removeEventListener('keydown', onKeydown);
  document.body.style.overflow = '';
});
</script>

<style scoped>
.fade-modal-enter-active,
.fade-modal-leave-active {
  transition: opacity 0.2s ease;
}
.fade-modal-enter-from,
.fade-modal-leave-to {
  opacity: 0;
}
</style>
