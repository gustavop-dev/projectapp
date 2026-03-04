<template>
  <div v-if="canRespond" class="proposal-response fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-sm border-t border-gray-200 px-6 py-4">
    <div class="max-w-2xl mx-auto flex items-center justify-center gap-4">
      <template v-if="!responded">
        <button
          class="px-6 py-3 bg-emerald-600 text-white rounded-xl font-medium text-sm
                 hover:bg-emerald-700 transition-colors shadow-sm flex items-center gap-2"
          :disabled="isSubmitting"
          @click="showConfirm('accepted')"
        >
          <span>✅</span> Acepto la propuesta
        </button>
        <button
          class="px-6 py-3 bg-white text-gray-600 rounded-xl font-medium text-sm
                 border border-gray-200 hover:bg-gray-50 hover:text-red-600 hover:border-red-200
                 transition-colors flex items-center gap-2"
          :disabled="isSubmitting"
          @click="showConfirm('rejected')"
        >
          <span>❌</span> Rechazo la propuesta
        </button>
      </template>

      <!-- Confirmation dialog -->
      <template v-else-if="pendingAction && !submitted">
        <div class="text-center">
          <p class="text-sm text-gray-600 mb-3">
            {{ pendingAction === 'accepted'
              ? '¿Estás seguro de que deseas aceptar esta propuesta?'
              : '¿Estás seguro de que deseas rechazar esta propuesta?' }}
          </p>
          <div class="flex items-center justify-center gap-3">
            <button
              class="px-5 py-2 rounded-xl text-sm font-medium transition-colors"
              :class="pendingAction === 'accepted'
                ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                : 'bg-red-600 text-white hover:bg-red-700'"
              :disabled="isSubmitting"
              @click="confirmAction"
            >
              {{ isSubmitting ? 'Enviando...' : 'Sí, confirmar' }}
            </button>
            <button
              class="px-5 py-2 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors"
              :disabled="isSubmitting"
              @click="cancelAction"
            >
              Cancelar
            </button>
          </div>
        </div>
      </template>

      <!-- Success message -->
      <template v-else-if="submitted">
        <div class="text-center py-2">
          <p class="text-sm font-medium" :class="submittedAction === 'accepted' ? 'text-emerald-600' : 'text-gray-600'">
            {{ submittedAction === 'accepted'
              ? '✅ ¡Propuesta aceptada! Nos pondremos en contacto contigo pronto.'
              : '❌ Propuesta rechazada. Gracias por tu tiempo.' }}
          </p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  proposal: { type: Object, default: null },
});

const proposalStore = useProposalStore();

const canRespond = computed(() => {
  const s = props.proposal?.status;
  return s === 'sent' || s === 'viewed';
});

const responded = ref(false);
const pendingAction = ref(null);
const isSubmitting = ref(false);
const submitted = ref(false);
const submittedAction = ref(null);

function showConfirm(action) {
  responded.value = true;
  pendingAction.value = action;
}

function cancelAction() {
  responded.value = false;
  pendingAction.value = null;
}

async function confirmAction() {
  if (!pendingAction.value || !props.proposal?.uuid) return;

  isSubmitting.value = true;
  try {
    const result = await proposalStore.respondToProposal(
      props.proposal.uuid,
      pendingAction.value,
    );
    if (result.success) {
      submittedAction.value = pendingAction.value;
      submitted.value = true;
    }
  } finally {
    isSubmitting.value = false;
  }
}
</script>
