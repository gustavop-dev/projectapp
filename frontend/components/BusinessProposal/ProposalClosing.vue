<template>
  <section ref="sectionRef" class="proposal-closing min-h-screen w-full bg-white flex flex-col items-center justify-center py-8 px-6 md:px-12 lg:px-24">
    <div class="max-w-4xl w-full mx-auto text-center flex flex-col items-center gap-6">
      <!-- Validity notice -->
      <div v-if="validityMessage" data-animate="fade-up" class="validity-notice w-full bg-yellow-50 border-2 border-yellow-200 p-4 md:p-6 rounded-xl text-left">
        <div class="flex items-start">
          <svg class="w-5 h-5 text-yellow-600 mr-3 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
          </svg>
          <div>
            <h4 class="font-bold text-gray-900 mb-1 text-sm md:text-base">Validez de la Propuesta</h4>
            <p class="text-xs md:text-sm text-gray-600">{{ validityMessage }}</p>
          </div>
        </div>
      </div>

      <!-- Thank you message -->
      <div v-if="thankYouMessage" data-animate="fade-up">
        <h3 class="text-2xl md:text-3xl font-bold text-gray-900 mb-2">¡Gracias por tu Tiempo!</h3>
        <p class="text-base md:text-lg text-gray-600 max-w-2xl mx-auto">{{ thankYouMessage }}</p>
      </div>

      <!-- Accept / Reject buttons -->
      <div v-if="canRespond && !submitted" data-animate="fade-up" class="flex flex-col sm:flex-row gap-4 justify-center items-center pt-2">
        <button
          class="px-6 sm:px-8 py-3 sm:py-4 bg-emerald-600 text-white rounded-xl font-medium text-sm sm:text-base
                 hover:bg-emerald-700 transition-colors shadow-lg flex items-center gap-2"
          :disabled="isSubmitting"
          @click="showAcceptConfirm = true"
        >
          <span>✅</span> Acepto la propuesta
        </button>
        <button
          class="px-6 sm:px-8 py-3 sm:py-4 bg-white text-gray-600 rounded-xl font-medium text-sm sm:text-base
                 border-2 border-gray-200 hover:bg-gray-50 hover:text-red-600 hover:border-red-200
                 transition-colors flex items-center gap-2"
          :disabled="isSubmitting"
          @click="showRejectModal = true"
        >
          <span>❌</span> Rechazar propuesta
        </button>
      </div>

      <!-- Success messages -->
      <div v-if="submitted || proposal?.status === 'accepted'" data-animate="fade-up" class="py-4">
        <div class="text-5xl mb-3">🎉</div>
        <p class="text-xl font-bold text-emerald-600">¡Propuesta aceptada!</p>
        <p class="text-gray-500 mt-2">Te enviaremos un email de confirmación.</p>
      </div>
      <div v-else-if="proposal?.status === 'rejected'" data-animate="fade-up" class="py-4">
        <p class="text-lg text-gray-500">Propuesta rechazada. Gracias por tu tiempo.</p>
      </div>
    </div>
  </section>

  <!-- Accept confirmation modal -->
  <teleport to="body">
    <div v-if="showAcceptConfirm" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showAcceptConfirm = false">
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-5 sm:p-8 text-center">
        <div class="text-5xl mb-4">🎉</div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">¿Confirmar aceptación?</h3>
        <p class="text-gray-600 text-sm mb-6">Al aceptar, recibirás un email de confirmación con los próximos pasos.</p>
        <div class="flex gap-3 justify-center">
          <button class="px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors" :disabled="isSubmitting" @click="confirmAccept">
            {{ isSubmitting ? 'Enviando...' : 'Sí, acepto' }}
          </button>
          <button class="px-6 py-2.5 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors" @click="showAcceptConfirm = false">Cancelar</button>
        </div>
      </div>
    </div>
  </teleport>

  <!-- Reject modal -->
  <teleport to="body">
    <div v-if="showRejectModal" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showRejectModal = false">
      <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full mx-4 p-5 sm:p-8">
        <h3 class="text-xl font-bold text-gray-900 mb-2">Lamentamos que no sea el momento</h3>
        <p class="text-gray-600 text-sm mb-6">Tu opinión es muy importante para nosotros. ¿Podrías indicarnos el motivo?</p>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Motivo</label>
            <select v-model="rejectReason" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 outline-none bg-white">
              <option value="">Selecciona un motivo...</option>
              <option value="Presupuesto muy alto">Presupuesto muy alto</option>
              <option value="Encontré otra opción">Encontré otra opción</option>
              <option value="No es el momento">No es el momento</option>
              <option value="No cumple mis expectativas">No cumple mis expectativas</option>
              <option value="Otros">Otros</option>
            </select>
          </div>
          <div v-if="rejectReason">
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ rejectReason === 'Otros' ? 'Cuéntanos más' : 'Comentario adicional (opcional)' }}</label>
            <textarea v-model="rejectComment" rows="3" :placeholder="rejectReason === 'Otros' ? 'Escribe tu motivo aquí...' : 'Algún comentario adicional...'"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 outline-none resize-none" />
          </div>
        </div>
        <div class="flex gap-3 justify-end mt-6">
          <button class="px-5 py-2 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors" @click="showRejectModal = false">Cancelar</button>
          <button class="px-5 py-2 bg-red-600 text-white rounded-xl text-sm font-medium hover:bg-red-700 transition-colors" :disabled="isSubmitting || !rejectReason" @click="confirmReject">
            {{ isSubmitting ? 'Enviando...' : 'Confirmar rechazo' }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useSectionAnimations } from '~/composables/useSectionAnimations';

const sectionRef = ref(null);
useSectionAnimations(sectionRef);

const props = defineProps({
  proposal: { type: Object, default: null },
  validityMessage: { type: String, default: '' },
  thankYouMessage: { type: String, default: '' },
});

const proposalStore = useProposalStore();

const canRespond = computed(() => {
  const s = props.proposal?.status;
  return s === 'sent' || s === 'viewed';
});

const isSubmitting = ref(false);
const submitted = ref(false);
const showAcceptConfirm = ref(false);
const showRejectModal = ref(false);
const rejectReason = ref('');
const rejectComment = ref('');

async function confirmAccept() {
  if (!props.proposal?.uuid) return;
  isSubmitting.value = true;
  try {
    const result = await proposalStore.respondToProposal(props.proposal.uuid, 'accepted');
    if (result.success) {
      submitted.value = true;
      showAcceptConfirm.value = false;
    }
  } finally {
    isSubmitting.value = false;
  }
}

async function confirmReject() {
  if (!props.proposal?.uuid || !rejectReason.value) return;
  isSubmitting.value = true;
  try {
    const result = await proposalStore.respondToProposal(
      props.proposal.uuid, 'rejected',
      { reason: rejectReason.value, comment: rejectComment.value },
    );
    if (result.success) {
      submitted.value = true;
      showRejectModal.value = false;
    }
  } finally {
    isSubmitting.value = false;
  }
}
</script>
