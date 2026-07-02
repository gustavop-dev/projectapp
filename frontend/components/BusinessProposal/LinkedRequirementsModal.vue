<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="fixed inset-0 z-[10000] flex items-center justify-center p-4 sm:p-6" :class="{ 'dark-modal': isDark }">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('close')" />
        <div class="modal-panel relative bg-surface rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
          <!-- Header -->
          <div class="modal-header flex items-center justify-between px-6 py-5 border-b border-border-muted">
            <div class="flex items-center gap-3">
              <div class="modal-icon-badge w-10 h-10 rounded-xl flex items-center justify-center bg-primary-soft">
                <span class="text-xl">{{ item.icon || '📋' }}</span>
              </div>
              <div>
                <p class="modal-kicker text-xs uppercase tracking-wide text-text-subtle">{{ kickerLabel }}</p>
                <h3 class="modal-title text-lg font-medium text-text-brand">{{ item.name }}</h3>
              </div>
            </div>
            <button
              class="modal-close w-8 h-8 rounded-lg flex items-center justify-center text-text-subtle hover:text-text-default hover:bg-surface-raised transition-colors"
              :aria-label="closeLabel"
              @click="$emit('close')"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="overflow-y-auto px-6 py-6 flex-1">
            <ul class="space-y-4">
              <li v-for="(req, idx) in requirements" :key="req.flowKey || idx"
                  class="requirement-card bg-esmerald/5 p-5 rounded-xl border border-esmerald/10"
                  data-testid="linked-requirement">
                <div class="flex items-start justify-between gap-3">
                  <h4 class="req-title font-bold text-text-brand mb-1">{{ req.title }}</h4>
                  <span v-if="priorityText(req.priority)"
                        class="priority-badge flex-shrink-0 text-xs font-medium px-2.5 py-1 rounded-full bg-primary-soft text-text-brand">
                    {{ priorityText(req.priority) }}
                  </span>
                </div>
                <p v-if="req.description" class="req-description text-sm text-text-default/70 font-light">
                  {{ req.description }}
                </p>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue';
import { useProposalDarkMode } from '~/composables/useProposalDarkMode';
import { priorityLabel } from '~/utils/requirementPriority';

const { isDark } = useProposalDarkMode();

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  item: {
    type: Object,
    default: () => ({ icon: '📋', name: '' }),
  },
  requirements: {
    type: Array,
    default: () => [],
  },
  language: {
    type: String,
    default: 'es',
  },
});

defineEmits(['close']);

const kickerLabel = computed(() => (
  props.language === 'en' ? 'Requirements to implement' : 'Requerimientos a implementar'
));
const closeLabel = computed(() => (props.language === 'en' ? 'Close' : 'Cerrar'));

function priorityText(priority) {
  return priorityLabel(priority, props.language);
}
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

/* ── Dark mode ── */
.dark-modal .modal-panel {
  background-color: #143d35;
  border: 1px solid rgba(16, 185, 129, 0.22);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.7), 0 0 32px rgba(16, 185, 129, 0.15);
}

.dark-modal .modal-header {
  border-color: rgba(16, 185, 129, 0.18);
}

.dark-modal .modal-title {
  color: #E6EFEF;
}

.dark-modal .modal-kicker {
  color: rgba(230, 239, 239, 0.5);
}

.dark-modal .modal-close {
  color: rgba(230, 239, 239, 0.5);
}
.dark-modal .modal-close:hover {
  color: #E6EFEF;
  background-color: rgba(230, 239, 239, 0.08);
}

.dark-modal .modal-icon-badge {
  background-color: rgba(16, 185, 129, 0.30);
}

.dark-modal .requirement-card {
  background-color: #133832;
  border-color: rgba(16, 185, 129, 0.18);
}

.dark-modal .req-title {
  color: #E6EFEF;
}

.dark-modal .req-description {
  color: rgba(230, 239, 239, 0.65);
}

.dark-modal .priority-badge {
  background-color: rgba(16, 185, 129, 0.30);
  color: #E6EFEF;
}
</style>
