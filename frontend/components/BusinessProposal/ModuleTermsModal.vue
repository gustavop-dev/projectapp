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
            <BaseButton
              unstyled
              icon-only
              class="w-8 h-8 rounded-lg flex items-center justify-center text-text-subtle hover:text-text-default hover:bg-surface-raised transition-colors"
              :aria-label="closeLabel"
              @click="$emit('close')"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </BaseButton>
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

            <!-- Categorised legal clauses (canonical shape) -->
            <ol v-if="resolvedClauses.length" class="space-y-4" data-testid="module-terms-clauses">
              <li
                v-for="(clause, idx) in resolvedClauses"
                :key="idx"
                class="border-l-2 border-primary/30 pl-4"
              >
                <p
                  v-if="clause.label"
                  class="text-[11px] font-semibold uppercase tracking-wider text-text-brand mb-1"
                  data-testid="module-terms-clause-label"
                >
                  {{ clause.label }}
                </p>
                <!-- eslint-disable-next-line vue/no-v-html — renderInlineBold escapes all HTML first -->
                <p
                  class="text-sm text-text-default/80 font-light leading-relaxed whitespace-pre-line [&_strong]:font-semibold [&_strong]:text-text-default"
                  v-html="renderInlineBold(clause.text)"
                />
              </li>
            </ol>
            <p v-else class="text-sm text-text-subtle font-light">
              {{ emptyLabel }}
            </p>

            <!-- The cross-cutting provisions are rendered once at the end of the
                 section (ValueAddedModules.vue), mirroring the PDF annex — they
                 are deliberately not repeated inside every module modal. -->
            <p v-if="generalTermsHint" class="mt-6 pt-5 border-t border-border-muted text-xs text-text-subtle font-light">
              {{ generalTermsHint }}
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
  /** Canonical shape: [{ label, text }]. Falls back to `terms` when empty. */
  clauses: {
    type: Array,
    default: () => [],
  },
  /** Title of the section-level provisions block, used only for a pointer. */
  generalTermsTitle: {
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

function normalizeClauses(list) {
  if (!Array.isArray(list)) return [];
  return list
    .filter((c) => c && typeof c === 'object' && String(c.text || '').trim())
    .map((c) => ({ label: String(c.label || '').trim(), text: String(c.text) }));
}

// Proposals created before the clause format only carry the flat `terms`
// string, which the backend writes as one `**Label.** text` line per clause —
// parse it back so old proposals render the same categorised list.
function clausesFromLegacyTerms(text) {
  return String(text || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const match = line.match(/^\*\*(.+?)\.\*\*\s*(.*)$/);
      if (match) return { label: match[1], text: match[2] };
      return { label: '', text: line };
    });
}

const resolvedClauses = computed(() => {
  const explicit = normalizeClauses(props.clauses);
  if (explicit.length) return explicit;
  return clausesFromLegacyTerms(props.terms);
});

const generalTermsHint = computed(() => {
  const title = String(props.generalTermsTitle || '').trim();
  if (!title) return '';
  return props.language === 'en'
    ? `These terms are supplemented by the "${title}" set out at the end of this section.`
    : `Estos términos se complementan con las "${title}" que aparecen al cierre de esta sección.`;
});

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
