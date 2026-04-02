<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50" @click="$emit('cancel')" />

        <!-- Modal -->
        <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div class="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 rounded-t-2xl z-10">
            <h2 class="text-lg font-semibold text-gray-900">Enviar documentos al cliente</h2>
            <p class="text-xs text-gray-500 mt-1">
              Revisa y edita el contenido del correo antes de enviar.
              Se enviará a <span class="font-medium text-gray-700">{{ proposal.client_email }}</span>
            </p>
          </div>

          <form class="px-6 py-5 space-y-5" @submit.prevent="handleSend">
            <!-- Subject -->
            <div>
              <label class="block text-xs text-gray-500 mb-1">Asunto</label>
              <input v-model="emailForm.subject" type="text" required class="send-modal-input" />
            </div>

            <!-- Greeting -->
            <div>
              <label class="block text-xs text-gray-500 mb-1">Saludo</label>
              <input v-model="emailForm.greeting" type="text" required class="send-modal-input" />
            </div>

            <!-- Body (intro text) -->
            <div>
              <label class="block text-xs text-gray-500 mb-1">Texto introductorio</label>
              <textarea v-model="emailForm.body" rows="2" required class="send-modal-input resize-y" />
            </div>

            <!-- Document descriptions -->
            <div>
              <p class="text-xs text-gray-500 mb-3">Descripción de cada documento (aparece en el cuerpo del correo)</p>
              <div class="space-y-3">
                <div v-for="(doc, idx) in emailForm.documentDescriptions" :key="idx"
                  class="bg-gray-50 rounded-lg p-3">
                  <div class="flex items-center gap-2 mb-1.5">
                    <span class="text-xs font-semibold text-gray-700">{{ doc.name }}</span>
                  </div>
                  <textarea v-model="doc.description" rows="1"
                    class="send-modal-input text-xs py-1.5 resize-y" />
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div>
              <label class="block text-xs text-gray-500 mb-1">Texto de cierre</label>
              <textarea v-model="emailForm.footer" rows="2" class="send-modal-input resize-y" />
            </div>

            <!-- Error message -->
            <p v-if="sendError" class="text-xs text-red-500">{{ sendError }}</p>

            <!-- Actions -->
            <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-100">
              <button type="button"
                class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
                @click="$emit('cancel')">
                Cancelar
              </button>
              <button type="submit" :disabled="sending"
                class="inline-flex items-center gap-1.5 px-5 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50">
                <svg v-if="!sending" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {{ sending ? 'Enviando...' : 'Enviar documentos' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue';

const DEFAULT_DESCRIPTIONS = {
  draft_contract: 'Contrato de desarrollo de software formalizado para el proyecto.',
  commercial: 'Propuesta comercial con el alcance, inversión y condiciones del proyecto.',
  technical: 'Documento técnico con las especificaciones y metodología del proyecto.',
  amendment: 'Otrosí que modifica o complementa las condiciones del contrato.',
  legal_annex: 'Anexo legal con información complementaria del acuerdo.',
  client_document: 'Documento proporcionado por el cliente como parte del proceso.',
  other: 'Documento adicional relacionado con el proyecto.',
};

const DOC_NAMES = {
  draft_contract: 'Contrato de desarrollo (borrador)',
  commercial: 'Propuesta comercial',
  technical: 'Detalle técnico',
};

const props = defineProps({
  visible: { type: Boolean, default: false },
  proposal: { type: Object, default: () => ({}) },
  selectedMainDocs: { type: Array, default: () => [] },
  selectedAdditionalDocs: { type: Array, default: () => [] },
});

const emit = defineEmits(['cancel', 'sent']);

const proposalStore = useProposalStore();
const sending = ref(false);
const sendError = ref('');

const emailForm = ref({
  subject: '',
  greeting: '',
  body: '',
  footer: '',
  documentDescriptions: [],
});

function buildDescriptions() {
  const descriptions = [];
  for (const key of props.selectedMainDocs) {
    descriptions.push({
      name: DOC_NAMES[key] || key,
      description: DEFAULT_DESCRIPTIONS[key] || '',
    });
  }
  for (const doc of props.selectedAdditionalDocs) {
    const docType = doc.document_type || 'other';
    descriptions.push({
      name: doc.title || doc.document_type_display || 'Documento',
      description: DEFAULT_DESCRIPTIONS[docType] || DEFAULT_DESCRIPTIONS.other,
    });
  }
  return descriptions;
}

watch(() => props.visible, (val) => {
  if (val) {
    sendError.value = '';
    const clientName = props.proposal.client_name || 'Cliente';
    emailForm.value = {
      subject: `\uD83D\uDCCE ${clientName}, te compartimos documentos de tu proyecto \u2014 Project App`,
      greeting: `Hola ${clientName} \uD83D\uDC4B`,
      body: 'Te enviamos los siguientes documentos relacionados con tu proyecto. Encontrarás cada uno adjunto a este correo.',
      footer: 'Si tienes dudas sobre alguno de los documentos, no dudes en responder este correo o escribirnos por WhatsApp.',
      documentDescriptions: buildDescriptions(),
    };
  }
});

async function handleSend() {
  sending.value = true;
  sendError.value = '';
  const result = await proposalStore.sendDocumentsToClient(props.proposal.id, {
    documents: props.selectedMainDocs,
    additional_doc_ids: props.selectedAdditionalDocs.map(d => d.id),
    subject: emailForm.value.subject,
    greeting: emailForm.value.greeting,
    body: emailForm.value.body,
    footer: emailForm.value.footer,
    document_descriptions: emailForm.value.documentDescriptions,
  });
  sending.value = false;
  if (result.success) {
    emit('sent');
  } else {
    sendError.value = 'Error al enviar los documentos. Intenta de nuevo.';
  }
}
</script>

<style scoped>
.send-modal-input {
  @apply w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
