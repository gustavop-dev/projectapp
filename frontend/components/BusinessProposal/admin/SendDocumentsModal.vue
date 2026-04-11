<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50" @click="$emit('cancel')" />

        <!-- Modal -->
        <div class="relative bg-white dark:bg-esmerald rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
          <!-- Header with tabs -->
          <div class="sticky top-0 bg-white dark:bg-esmerald border-b border-gray-100 dark:border-white/[0.06] px-6 pt-4 rounded-t-2xl z-10">
            <div class="mb-3">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Enviar documentos al cliente</h2>
              <p class="text-xs text-gray-500 dark:text-green-light/60 mt-0.5">
                Se enviará a <span class="font-medium text-gray-700 dark:text-white/70">{{ proposal.client_email }}</span>
              </p>
            </div>
            <!-- Tab switcher -->
            <div class="flex gap-4">
              <button type="button"
                class="pb-2 text-sm transition-colors border-b-2"
                :class="activeTab === 'preview'
                  ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400 font-semibold'
                  : 'border-transparent text-gray-500 dark:text-green-light/60 hover:text-gray-700 dark:hover:text-white/70'"
                @click="activeTab = 'preview'">
                Vista previa
              </button>
              <button type="button"
                class="pb-2 text-sm transition-colors border-b-2"
                :class="activeTab === 'edit'
                  ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400 font-semibold'
                  : 'border-transparent text-gray-500 dark:text-green-light/60 hover:text-gray-700 dark:hover:text-white/70'"
                @click="activeTab = 'edit'">
                Editar
              </button>
            </div>
          </div>

          <!-- Scrollable content area -->
          <div class="overflow-y-auto flex-1 px-6 py-5">
            <!-- Preview tab -->
            <div v-if="activeTab === 'preview'">
              <!-- Subject badge -->
              <div class="flex items-center gap-2 bg-gray-50 dark:bg-white/[0.03] rounded-lg px-3 py-2 mb-4 text-xs text-gray-500 dark:text-green-light/60">
                <span class="font-medium text-gray-700 dark:text-white/70">Asunto:</span>
                <span>{{ emailForm.subject }}</span>
              </div>

              <!-- Email preview card -->
              <div style="background-color:#f3f4f6;border-radius:12px;padding:24px 16px;font-family:Arial,'Helvetica Neue',Helvetica,sans-serif;">
                <div style="background-color:#ffffff;border-radius:16px;overflow:hidden;max-width:560px;margin:0 auto;">

                  <!-- Email header -->
                  <div style="background-color:#059669;padding:28px 32px;text-align:center;">
                    <div style="margin:0;color:#ffffff;font-size:22px;font-weight:700;letter-spacing:-0.02em;">
                      Project App.
                    </div>
                    <div style="margin:6px 0 0;color:#d1fae5;font-size:13px;font-weight:400;">
                      Transformación Digital
                    </div>
                  </div>

                  <!-- Greeting + body -->
                  <div style="padding:32px 32px 20px;">
                    <div style="margin:0;color:#1f2937;font-size:20px;font-weight:600;white-space:pre-wrap;">{{ emailForm.greeting }}</div>
                    <div style="margin:14px 0 0;color:#4b5563;font-size:15px;line-height:1.6;white-space:pre-wrap;">{{ emailForm.body }}</div>
                    <div v-if="showProposalUrl" style="margin:16px 0 0;">
                      <a :href="proposal.public_url" target="_blank"
                        style="display:inline-block;background-color:#059669;color:#ffffff;padding:10px 22px;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;letter-spacing:0.01em;">
                        Ver propuesta en línea →
                      </a>
                    </div>
                  </div>

                  <!-- Documents list card -->
                  <div v-if="emailForm.documentDescriptions.length" style="padding:0 32px 20px;">
                    <div style="background-color:#f0fdf4;border-radius:12px;border:1px solid #bbf7d0;padding:20px;">
                      <div style="margin:0 0 14px;color:#059669;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">
                        Documentos adjuntos
                      </div>
                      <div v-for="(doc, idx) in emailForm.documentDescriptions" :key="idx"
                        :style="{
                          padding: '10px 0',
                          borderBottom: idx < emailForm.documentDescriptions.length - 1 ? '1px solid #d1fae5' : 'none'
                        }">
                        <div style="margin:0;color:#1f2937;font-size:13px;font-weight:600;">
                          📄 {{ doc.name }}
                        </div>
                        <div style="margin:3px 0 0;color:#6b7280;font-size:12px;line-height:1.5;white-space:pre-wrap;">{{ doc.description }}</div>
                      </div>
                    </div>
                  </div>

                  <!-- Footer text -->
                  <div v-if="emailForm.footer" style="padding:0 32px 20px;">
                    <div style="margin:0;color:#4b5563;font-size:14px;line-height:1.6;white-space:pre-wrap;">{{ emailForm.footer }}</div>
                  </div>

                  <!-- Divider -->
                  <div style="padding:0 32px;">
                    <hr style="border:none;border-top:1px solid #e5e7eb;margin:0;" />
                  </div>

                  <!-- Company footer -->
                  <div style="padding:20px 32px 28px;text-align:center;">
                    <div style="margin:0 0 6px;color:#6b7280;font-size:13px;line-height:1.5;">
                      ¿Dudas? Respondé este correo o escríbenos por
                      <span style="color:#059669;font-weight:600;">WhatsApp</span>
                    </div>
                    <div style="margin:12px 0 0;color:#9ca3af;font-size:11px;">
                      © 2026 ProjectApp.co | Bogotá, Colombia
                    </div>
                  </div>

                </div>
              </div>
            </div>

            <!-- Edit tab -->
            <form v-else id="send-documents-form" class="space-y-5" @submit.prevent="handleSend">
              <!-- Subject -->
              <div>
                <label for="send-subject" class="block text-xs text-gray-500 dark:text-white/70 mb-1">Asunto</label>
                <input id="send-subject" v-model="emailForm.subject" type="text" required class="send-modal-input" />
              </div>

              <!-- Greeting -->
              <div>
                <label for="send-greeting" class="block text-xs text-gray-500 dark:text-white/70 mb-1">Saludo</label>
                <input id="send-greeting" v-model="emailForm.greeting" type="text" required class="send-modal-input" />
              </div>

              <!-- Body (intro text) -->
              <div>
                <label for="send-body" class="block text-xs text-gray-500 dark:text-white/70 mb-1">Texto introductorio</label>
                <textarea id="send-body" v-model="emailForm.body" rows="2" required class="send-modal-input resize-y" />
              </div>

              <!-- Document descriptions -->
              <div>
                <p class="text-xs text-gray-500 dark:text-green-light/60 mb-3">Descripción de cada documento (aparece en el cuerpo del correo)</p>
                <div class="space-y-3">
                  <div v-for="(doc, idx) in emailForm.documentDescriptions" :key="idx"
                    class="bg-gray-50 dark:bg-white/[0.03] rounded-lg p-3">
                    <div class="flex items-center gap-2 mb-1.5">
                      <span class="text-xs font-semibold text-gray-700 dark:text-white/70">{{ doc.name }}</span>
                    </div>
                    <textarea v-model="doc.description" rows="1"
                      class="send-modal-input text-xs py-1.5 resize-y" />
                  </div>
                </div>
              </div>

              <!-- Footer -->
              <div>
                <label for="send-footer" class="block text-xs text-gray-500 dark:text-white/70 mb-1">Texto de cierre</label>
                <textarea id="send-footer" v-model="emailForm.footer" rows="2" class="send-modal-input resize-y" />
              </div>
            </form>
          </div>

          <!-- Sticky footer: error + actions -->
          <div class="border-t border-gray-100 dark:border-white/[0.06] px-6 py-4 rounded-b-2xl bg-white dark:bg-esmerald">
            <p v-if="sendError" class="text-xs text-red-500 mb-3">{{ sendError }}</p>
            <div class="flex items-center justify-end gap-3">
              <button type="button"
                class="px-4 py-2 text-sm text-gray-600 dark:text-green-light hover:text-gray-800 dark:hover:text-white transition-colors"
                @click="$emit('cancel')">
                Cancelar
              </button>
              <button type="button" :disabled="sending"
                class="inline-flex items-center gap-1.5 px-5 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50"
                @click="handleSend">
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
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

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
const activeTab = ref('preview');

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

const showProposalUrl = computed(() =>
  (props.selectedMainDocs.includes('commercial') || props.selectedMainDocs.includes('technical'))
  && !!props.proposal.public_url,
);

watch(() => props.visible, (val) => {
  if (val) {
    sendError.value = '';
    activeTab.value = 'preview';
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
  @apply w-full px-3 py-2 border border-gray-200 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-green-light/40 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500;
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
