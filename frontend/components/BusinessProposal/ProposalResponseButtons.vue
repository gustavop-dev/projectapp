<template>
  <div v-if="canRespond" class="proposal-response fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-sm border-t border-gray-200 px-6 py-4">
    <div class="max-w-2xl mx-auto flex items-center justify-center gap-4">
      <template v-if="!submitted">
        <button
          class="px-6 py-3 bg-emerald-600 text-white rounded-xl font-medium text-sm
                 hover:bg-emerald-700 transition-colors shadow-sm flex items-center gap-2"
          :disabled="isSubmitting"
          @click="handleAccept"
        >
          <span>✅</span> Acepto la propuesta
        </button>
        <button
          class="px-6 py-3 bg-white text-gray-600 rounded-xl font-medium text-sm
                 border border-gray-200 hover:bg-gray-50 hover:text-red-600 hover:border-red-200
                 transition-colors flex items-center gap-2"
          :disabled="isSubmitting"
          @click="showRejectModal = true"
        >
          <span>❌</span> Rechazar
        </button>
      </template>

      <template v-else>
        <div class="text-center py-2">
          <p class="text-sm font-medium" :class="submittedAction === 'accepted' ? 'text-emerald-600' : 'text-gray-600'">
            {{ submittedAction === 'accepted'
              ? '✅ ¡Propuesta aceptada! Te enviaremos un email de confirmación.'
              : '❌ Propuesta rechazada. Gracias por tu tiempo.' }}
          </p>
        </div>
      </template>
    </div>
  </div>

  <!-- Accept confirmation modal -->
  <teleport to="body">
    <div v-if="showAcceptConfirm" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showAcceptConfirm = false">
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-8 text-center">
        <div class="text-5xl mb-4">🎉</div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">¿Confirmar aceptación?</h3>
        <p class="text-gray-600 text-sm mb-6">Al aceptar, recibirás un email de confirmación con los próximos pasos.</p>
        <div class="flex gap-3 justify-center">
          <button
            class="px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors"
            :disabled="isSubmitting"
            @click="confirmAccept"
          >{{ isSubmitting ? 'Enviando...' : 'Sí, acepto' }}</button>
          <button class="px-6 py-2.5 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors" @click="showAcceptConfirm = false">Cancelar</button>
        </div>
      </div>
    </div>
  </teleport>

  <!-- Reject modal -->
  <teleport to="body">
    <div v-if="showRejectModal" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showRejectModal = false">
      <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full mx-4 p-8">
        <h3 class="text-xl font-bold text-gray-900 mb-2">Lamentamos que no sea el momento</h3>
        <p class="text-gray-600 text-sm mb-6">Tu opinión es muy importante para nosotros. ¿Podrías indicarnos el motivo?</p>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Motivo</label>
            <select v-model="rejectReason" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white">
              <option value="">Selecciona un motivo...</option>
              <option value="Presupuesto muy alto">Presupuesto muy alto</option>
              <option value="Encontré otra opción">Encontré otra opción</option>
              <option value="No es el momento">No es el momento</option>
              <option value="No cumple mis expectativas">No cumple mis expectativas</option>
              <option value="Otros">Otros</option>
            </select>
          </div>

          <div v-if="rejectReason === 'Otros' || rejectReason">
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ rejectReason === 'Otros' ? 'Cuéntanos más' : 'Comentario adicional (opcional)' }}</label>
            <textarea
              v-model="rejectComment"
              rows="3"
              :placeholder="rejectReason === 'Otros' ? 'Escribe tu motivo aquí...' : 'Algún comentario adicional...'"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none resize-none"
            />
          </div>
        </div>

        <div class="flex gap-3 justify-end mt-6">
          <button class="px-5 py-2 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors" @click="showRejectModal = false">Cancelar</button>
          <button
            class="px-5 py-2 bg-red-600 text-white rounded-xl text-sm font-medium hover:bg-red-700 transition-colors"
            :disabled="isSubmitting || !rejectReason"
            @click="confirmReject"
          >{{ isSubmitting ? 'Enviando...' : 'Confirmar rechazo' }}</button>
        </div>
      </div>
    </div>
  </teleport>
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

const isSubmitting = ref(false);
const submitted = ref(false);
const submittedAction = ref(null);
const showAcceptConfirm = ref(false);
const showRejectModal = ref(false);
const rejectReason = ref('');
const rejectComment = ref('');

function handleAccept() {
  showAcceptConfirm.value = true;
}

async function confirmAccept() {
  if (!props.proposal?.uuid) return;
  isSubmitting.value = true;
  try {
    const result = await proposalStore.respondToProposal(
      props.proposal.uuid, 'accepted',
    );
    if (result.success) {
      submittedAction.value = 'accepted';
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
      submittedAction.value = 'rejected';
      submitted.value = true;
      showRejectModal.value = false;
    }
  } finally {
    isSubmitting.value = false;
  }
}
</script>
