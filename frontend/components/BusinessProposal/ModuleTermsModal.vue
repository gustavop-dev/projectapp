<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="fixed inset-0 z-[10000] flex items-center justify-center p-4 sm:p-6" :data-theme="isDark ? 'dark' : 'light'">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('close')" />
        <div class="relative bg-surface rounded-2xl shadow-overlay border border-border-default w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-5 border-b border-border-muted">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center bg-primary-soft">
                <span class="text-xl">{{ icon || '📄' }}</span>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide text-text-subtle">{{ kickerLabel }}</p>
                <h3 class="text-lg font-medium text-text-brand">{{ title }}</h3>
              </div>
            </div>
            <button
              class="w-8 h-8 rounded-lg flex items-center justify-center text-text-subtle hover:text-text-default hover:bg-surface-raised transition-colors"
              :aria-label="closeLabel"
              @click="$emit('close')"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="overflow-y-auto px-6 py-6 flex-1" data-testid="module-terms-body">
            <!-- Condition chips -->
            <div v-if="notes.length" class="flex flex-wrap gap-2 mb-5">
              <span
                v-for="(note, idx) in notes"
                :key="idx"
                class="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full bg-primary-soft text-text-brand"
              >
                {{ note }}
              </span>
            </div>

            <!-- eslint-disable-next-line vue/no-v-html — renderInlineBold escapes all HTML first -->
            <p
              v-if="terms"
              class="text-sm text-text-default/80 font-light leading-relaxed whitespace-pre-line [&_strong]:font-semibold [&_strong]:text-text-default"
              v-html="termsHtml"
            />
            <p v-else class="text-sm text-text-subtle font-light">
              {{ emptyLabel }}
            </p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue';
import { useProposalDarkMode } from '~/composables/useProposalDarkMode';
import { renderInlineBold } from '~/utils/renderInlineBold';

const { isDark } = useProposalDarkMode();

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
  icon: {
    type: String,
    default: '📄',
  },
  terms: {
    type: String,
    default: '',
  },
  notes: {
    type: Array,
    default: () => [],
  },
  language: {
    type: String,
    default: 'es',
  },
});

defineEmits(['close']);

const termsHtml = computed(() => renderInlineBold(props.terms));

const kickerLabel = computed(() => (
  props.language === 'en' ? 'Terms & conditions' : 'Términos y condiciones'
));
const closeLabel = computed(() => (props.language === 'en' ? 'Close' : 'Cerrar'));
const emptyLabel = computed(() => (
  props.language === 'en'
    ? 'No additional terms for this module.'
    : 'Sin términos adicionales para este módulo.'
));
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.25s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
