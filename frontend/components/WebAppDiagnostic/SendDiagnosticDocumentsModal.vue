<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/50" @click="$emit('cancel')" />

        <div class="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
          <!-- Header + tabs -->
          <div class="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700 px-6 pt-4 rounded-t-2xl z-10">
            <div class="mb-3">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Enviar documentos al cliente</h2>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Se enviará a <span class="font-medium text-gray-700 dark:text-white/70">{{ recipient }}</span>
              </p>
            </div>
            <div class="flex gap-4">
              <button type="button"
                class="pb-2 text-sm transition-colors border-b-2"
                :class="activeTab === 'preview'
                  ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400 font-semibold'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-white/70'"
                @click="activeTab = 'preview'">Vista previa</button>
              <button type="button"
                class="pb-2 text-sm transition-colors border-b-2"
                :class="activeTab === 'edit'
                  ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400 font-semibold'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-white/70'"
                @click="activeTab = 'edit'">Editar</button>
            </div>
          </div>

          <div class="overflow-y-auto flex-1 px-6 py-5">
            <!-- Preview -->
            <div v-if="activeTab === 'preview'">
              <div class="flex items-center gap-2 bg-gray-50 dark:bg-white/[0.03] rounded-lg px-3 py-2 mb-4 text-xs text-gray-500 dark:text-gray-400">
                <span class="font-medium text-gray-700 dark:text-white/70">Asunto:</span>
                <span>{{ emailForm.subject }}</span>
              </div>
              <div style="background-color:#f3f4f6;border-radius:12px;padding:24px 16px;font-family:Arial,'Helvetica Neue',Helvetica,sans-serif;">
                <div style="background-color:#ffffff;border-radius:16px;overflow:hidden;max-width:560px;margin:0 auto;">
                  <div style="background-color:#059669;padding:28px 32px;text-align:center;">
                    <div style="margin:0;color:#ffffff;font-size:22px;font-weight:700;letter-spacing:-0.02em;">Project App.</div>
                    <div style="margin:6px 0 0;color:#d1fae5;font-size:13px;font-weight:400;">Transformación Digital</div>
                  </div>
                  <div style="padding:32px 32px 20px;">
                    <div style="margin:0;color:#1f2937;font-size:20px;font-weight:600;white-space:pre-wrap;">{{ emailForm.greeting }}</div>
                    <div style="margin:14px 0 0;color:#4b5563;font-size:15px;line-height:1.6;white-space:pre-wrap;">{{ emailForm.body }}</div>
                  </div>
                  <div v-if="emailForm.documentDescriptions.length" style="padding:0 32px 20px;">
                    <div style="background-color:#f0fdf4;border-radius:12px;border:1px solid #bbf7d0;padding:20px;">
                      <div style="margin:0 0 14px;color:#059669;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">
                        Documentos adjuntos
                      </div>
                      <div v-for="(doc, idx) in emailForm.documentDescriptions" :key="idx"
                        :style="{ padding: '10px 0', borderBottom: idx < emailForm.documentDescriptions.length - 1 ? '1px solid #d1fae5' : 'none' }">
                        <div style="margin:0;color:#1f2937;font-size:13px;font-weight:600;">📄 {{ doc.name }}</div>
                        <div style="margin:3px 0 0;color:#6b7280;font-size:12px;line-height:1.5;white-space:pre-wrap;">{{ doc.description }}</div>
                      </div>
                    </div>
                  </div>
                  <div v-if="emailForm.footer" style="padding:0 32px 20px;">
                    <div style="margin:0;color:#4b5563;font-size:14px;line-height:1.6;white-space:pre-wrap;">{{ emailForm.footer }}</div>
                  </div>
                  <div style="padding:0 32px;"><hr style="border:none;border-top:1px solid #e5e7eb;margin:0;" /></div>
                  <div style="padding:20px 32px 28px;text-align:center;">
                    <div style="margin:0 0 6px;color:#6b7280;font-size:13px;line-height:1.5;">
                      ¿Dudas? Respondé este correo o escríbenos por
                      <span style="color:#059669;font-weight:600;">WhatsApp</span>
                    </div>
                    <div style="margin:12px 0 0;color:#9ca3af;font-size:11px;">© 2026 ProjectApp.co | Bogotá, Colombia</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Edit -->
            <form v-else class="space-y-5" @submit.prevent="handleSend">
              <div>
                <label class="block text-xs text-gray-500 dark:text-white/70 mb-1">Asunto</label>
                <input v-model="emailForm.subject" type="text" required class="send-modal-input" />
              </div>
              <div>
                <label class="block text-xs text-gray-500 dark:text-white/70 mb-1">Saludo</label>
                <input v-model="emailForm.greeting" type="text" required class="send-modal-input" />
              </div>
              <div>
                <label class="block text-xs text-gray-500 dark:text-white/70 mb-1">Texto introductorio</label>
                <textarea v-model="emailForm.body" rows="2" required class="send-modal-input resize-y" />
              </div>
              <div>
                <p class="text-xs text-gray-500 dark:text-gray-400 mb-3">
                  Descripción de cada documento (aparece en el cuerpo del correo)
                </p>
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
              <div>
                <label class="block text-xs text-gray-500 dark:text-white/70 mb-1">Texto de cierre</label>
                <textarea v-model="emailForm.footer" rows="2" class="send-modal-input resize-y" />
              </div>
            </form>
          </div>

          <div class="border-t border-gray-100 dark:border-gray-700 px-6 py-4 rounded-b-2xl bg-white dark:bg-gray-800">
            <p v-if="sendError" class="text-xs text-red-500 mb-3">{{ sendError }}</p>
            <div class="flex items-center justify-end gap-3">
              <button type="button"
                class="px-4 py-2 text-sm text-gray-600 dark:text-white hover:text-gray-800 dark:hover:text-white transition-colors"
                @click="$emit('cancel')">Cancelar</button>
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
import { ref, watch } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';

const DEFAULT_DESCRIPTIONS = {
  confidentiality_agreement: 'Acuerdo de confidencialidad bajo legislación colombiana (Ley 1581/2012). Por favor revisarlo antes de la entrega del diagnóstico técnico.',
  amendment: 'Otrosí que modifica o complementa las condiciones del diagnóstico.',
  legal_annex: 'Anexo legal con información complementaria.',
  client_document: 'Documento proporcionado por el cliente como parte del proceso.',
  other: 'Documento adicional relacionado con el diagnóstico.',
};

const MAIN_DOC_LABELS = {
  confidentiality_agreement: 'Acuerdo de Confidencialidad',
};

const props = defineProps({
  visible: { type: Boolean, default: false },
  diagnostic: { type: Object, default: () => ({}) },
  selectedAttachments: { type: Array, default: () => [] },
  selectedMainDocs: { type: Array, default: () => [] },
});

const emit = defineEmits(['cancel', 'sent']);

const store = useDiagnosticsStore();
const sending = ref(false);
const sendError = ref('');
const activeTab = ref('preview');

const recipient = props.diagnostic.client?.email || '';

const emailForm = ref({
  subject: '',
  greeting: '',
  body: '',
  footer: '',
  documentDescriptions: [],
});

function buildDescriptions() {
  const mainDocs = props.selectedMainDocs.map((key) => ({
    name: MAIN_DOC_LABELS[key] || key,
    description: DEFAULT_DESCRIPTIONS[key] || DEFAULT_DESCRIPTIONS.other,
  }));
  const attachments = props.selectedAttachments.map((att) => ({
    name: att.title || att.document_type_display || 'Documento',
    description:
      DEFAULT_DESCRIPTIONS[att.document_type] || DEFAULT_DESCRIPTIONS.other,
  }));
  return [...mainDocs, ...attachments];
}

watch(() => props.visible, (val) => {
  if (val) {
    sendError.value = '';
    activeTab.value = 'preview';
    const clientName = props.diagnostic.client?.name || 'Cliente';
    emailForm.value = {
      subject: `📎 ${clientName}, te compartimos documentos de tu diagnóstico — Project App`,
      greeting: `Hola ${clientName} 👋`,
      body: 'Te enviamos los siguientes documentos relacionados con tu diagnóstico. Encontrarás cada uno adjunto a este correo.',
      footer: 'Si tienes dudas sobre alguno de los documentos, no dudes en responder este correo o escribirnos por WhatsApp.',
      documentDescriptions: buildDescriptions(),
    };
  }
});

async function handleSend() {
  sending.value = true;
  sendError.value = '';
  const result = await store.sendAttachmentsToClient(props.diagnostic.id, {
    attachment_ids: props.selectedAttachments.map((a) => a.id),
    documents: props.selectedMainDocs,
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
    sendError.value = result.error || 'Error al enviar los documentos.';
  }
}
</script>

<style scoped>
.send-modal-input {
  @apply w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-white dark:placeholder:text-gray-500 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500;
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
