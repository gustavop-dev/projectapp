<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6" :class="{ 'dark-modal': isDark }">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('close')" />
        <div class="modal-panel relative bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
          <!-- Header -->
          <div class="modal-header flex items-center justify-between px-6 py-5 border-b border-gray-100">
            <div class="flex items-center gap-3">
              <div class="modal-icon-badge w-10 h-10 rounded-xl flex items-center justify-center bg-esmerald-light/60">
                <span class="text-xl">{{ group.icon || '🧩' }}</span>
              </div>
              <h3 class="modal-title text-xl font-medium text-esmerald">{{ group.title }}</h3>
            </div>
            <button
              class="modal-close w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
              @click="$emit('close')"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="overflow-y-auto px-6 py-6 flex-1">
            <p v-if="group.description" class="modal-description text-esmerald/80 font-light leading-relaxed text-base mb-8">
              {{ group.description }}
            </p>

            <div v-if="group.items && group.items.length" class="grid md:grid-cols-2 gap-4">
              <div v-for="(item, idx) in group.items" :key="idx"
                   class="requirement-card bg-esmerald/5 p-5 rounded-xl border border-esmerald/10">
                <div class="flex items-start">
                  <div class="req-icon-badge w-9 h-9 rounded-lg bg-esmerald-light/60 border border-esmerald/10 flex items-center justify-center mr-3 flex-shrink-0">
                    <span class="text-lg">{{ item.icon || '✅' }}</span>
                  </div>
                  <div>
                    <h4 class="req-title font-bold text-esmerald mb-1">{{ item.name }}</h4>
                    <p class="req-description text-sm text-esmerald/70 font-light">{{ item.description }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { useProposalDarkMode } from '~/composables/useProposalDarkMode';

const { isDark } = useProposalDarkMode();

defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  group: {
    type: Object,
    default: () => ({
      icon: '🧩',
      title: '',
      description: '',
      items: [],
    }),
  },
});

defineEmits(['close']);
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

.requirement-card {
  transition: all 0.2s ease;
}

.requirement-card:hover {
  border-color: rgba(16, 185, 129, 0.2);
  transform: translateX(4px);
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

.dark-modal .modal-close {
  color: rgba(230, 239, 239, 0.5);
}
.dark-modal .modal-close:hover {
  color: #E6EFEF;
  background-color: rgba(230, 239, 239, 0.08);
}

.dark-modal .modal-description {
  color: rgba(230, 239, 239, 0.72);
}

.dark-modal .modal-icon-badge {
  background-color: rgba(16, 185, 129, 0.30);
}

.dark-modal .requirement-card {
  background-color: #133832;
  border-color: rgba(16, 185, 129, 0.18);
}
.dark-modal .requirement-card:hover {
  border-color: rgba(16, 185, 129, 0.35);
}

.dark-modal .req-title {
  color: #E6EFEF;
}

.dark-modal .req-description {
  color: rgba(230, 239, 239, 0.65);
}

.dark-modal .req-icon-badge {
  background-color: rgba(16, 185, 129, 0.30);
  border-color: rgba(16, 185, 129, 0.18);
}
</style>
