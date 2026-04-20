<template>
  <div class="space-y-8">

    <!-- ── Email composer ── -->
    <section class="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-xl p-5">
      <div class="flex items-center gap-2 mb-5">
        <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <h3 class="text-sm font-semibold text-gray-800 dark:text-white">Correo de seguimiento</h3>
      </div>

      <!-- Sub-tab switcher -->
      <div class="flex gap-4 border-b border-gray-100 dark:border-gray-700 mb-5">
        <button type="button"
          class="pb-2 text-sm transition-colors border-b-2"
          :class="activeSubTab === 'edit'
            ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400 font-semibold'
            : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-white/70'"
          @click="activeSubTab = 'edit'">Editar</button>
        <button type="button"
          class="pb-2 text-sm transition-colors border-b-2"
          :class="activeSubTab === 'preview'
            ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400 font-semibold'
            : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-white/70'"
          @click="activeSubTab = 'preview'">Vista previa</button>
      </div>

      <!-- ── Edit sub-tab ── -->
      <div v-if="activeSubTab === 'edit'" class="space-y-4">
        <div>
          <label class="block text-xs text-gray-500 dark:text-white/70 mb-1">Para</label>
          <input v-model="recipient" type="email" placeholder="correo@ejemplo.com"
            class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-white dark:placeholder:text-gray-500 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500" />
        </div>

        <div>
          <label class="block text-xs text-gray-500 dark:text-white/70 mb-1">Asunto</label>
          <input v-model="subject" type="text" placeholder="Asunto del correo"
            class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-white dark:placeholder:text-gray-500 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500" />
        </div>

        <div>
          <label class="block text-xs text-gray-500 dark:text-white/70 mb-1">Saludo</label>
          <input v-model="greeting" type="text" placeholder="Hola Carlos"
            class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-white dark:placeholder:text-gray-500 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500" />
        </div>

        <!-- Sections (draggable) -->
        <div>
          <label class="block text-xs text-gray-500 dark:text-white/70 mb-2">Secciones del correo</label>
          <draggable v-model="sections" item-key="id" handle=".drag-handle" ghost-class="opacity-30"
            class="space-y-3">
            <template #item="{ element: section, index: idx }">
              <div class="bg-gray-50 dark:bg-white/[0.03] rounded-lg p-3 border border-gray-100 dark:border-gray-700">
                <div class="flex items-center gap-2 mb-2">
                  <span class="drag-handle cursor-grab text-gray-400 dark:text-gray-500 hover:text-gray-600 select-none text-sm">⠿</span>
                  <span class="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wide">Sección {{ idx + 1 }}</span>
                  <button v-if="sections.length > 1" type="button"
                    class="ml-auto text-gray-400 hover:text-red-500 transition-colors p-0.5"
                    @click="removeSection(idx)">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
                <textarea v-model="section.text" rows="3" placeholder="Escribe el contenido de esta sección..."
                  class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-white dark:placeholder:text-gray-500 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 resize-y" />
              </div>
            </template>
          </draggable>
          <button type="button" @click="addSection"
            class="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Agregar sección
          </button>
        </div>

        <div>
          <label class="block text-xs text-gray-500 dark:text-white/70 mb-1">Pie de correo</label>
          <textarea v-model="footer" rows="2" placeholder="Texto de cierre..."
            class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-white dark:placeholder:text-gray-500 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 resize-y" />
        </div>

        <div>
          <label class="block text-xs text-gray-500 dark:text-white/70 mb-1">Adjuntos</label>
          <div class="flex flex-col items-start gap-3">
            <button v-if="canCreateMarkdownAttachment" type="button" @click="showMarkdownModal = true"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 rounded-lg text-xs font-medium hover:bg-indigo-100 dark:hover:bg-indigo-900/30 transition-colors">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Crear documento desde markdown
            </button>
            <input ref="fileInput" type="file" multiple
              accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
              class="text-xs dark:text-white/70 file:mr-2 file:py-1.5 file:px-3 file:border-0 file:text-xs file:font-medium file:bg-emerald-50 dark:file:bg-emerald-900/20 file:text-emerald-700 dark:file:text-emerald-400 file:rounded-lg hover:file:bg-emerald-100 dark:hover:file:bg-emerald-900/30"
              @change="handleFilesChange" />
          </div>
          <div v-if="attachments.length" class="mt-2 space-y-1">
            <div v-for="(file, idx) in attachments" :key="idx"
              class="flex items-center justify-between py-1.5 px-3 bg-gray-50 dark:bg-white/[0.03] rounded-lg">
              <span class="text-xs text-gray-700 dark:text-white/70 truncate">{{ file.name }}</span>
              <button type="button" @click="removeAttachment(idx)"
                class="text-gray-400 hover:text-red-500 transition-colors p-0.5">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-between pt-2">
          <p v-if="sendError" class="text-xs text-red-500">{{ sendError }}</p>
          <p v-else-if="sendSuccess" class="text-xs text-emerald-600">Correo enviado correctamente.</p>
          <span v-else />
          <button type="button" :disabled="!canSend || sending" @click="handleSend"
            class="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            <svg v-if="!sending" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            <svg v-else class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ sending ? 'Enviando...' : 'Enviar correo' }}
          </button>
        </div>
      </div>

      <!-- ── Preview sub-tab ── -->
      <div v-else>
        <div class="flex items-center gap-2 bg-gray-50 dark:bg-white/[0.03] rounded-lg px-3 py-2 mb-4 text-xs text-gray-500 dark:text-gray-400">
          <span class="font-medium text-gray-700 dark:text-white/70">Asunto:</span>
          <span>{{ subject || '(sin asunto)' }}</span>
        </div>

        <div style="background-color:#f3f4f6;border-radius:12px;padding:24px 16px;font-family:Arial,'Helvetica Neue',Helvetica,sans-serif;">
          <div style="background-color:#ffffff;border-radius:16px;overflow:hidden;max-width:560px;margin:0 auto;">
            <div style="background-color:#059669;padding:28px 32px;text-align:center;">
              <div style="margin:0;color:#ffffff;font-size:22px;font-weight:700;letter-spacing:-0.02em;">
                Project App.
              </div>
              <div style="margin:6px 0 0;color:#d1fae5;font-size:13px;font-weight:400;">
                Transformación Digital
              </div>
            </div>
            <div style="padding:32px 32px 20px;">
              <div style="margin:0;color:#1f2937;font-size:20px;font-weight:600;white-space:pre-wrap;">{{ greeting || '(sin saludo)' }}</div>
            </div>
            <div v-for="section in sections" :key="section.id" style="padding:0 32px 14px;">
              <div style="margin:0;color:#4b5563;font-size:15px;line-height:1.6;white-space:pre-wrap;">{{ section.text || '(sección vacía)' }}</div>
            </div>
            <div v-if="attachments.length" style="padding:8px 32px 20px;">
              <div style="background-color:#f0fdf4;border-radius:12px;border:1px solid #bbf7d0;padding:16px 20px;">
                <div style="margin:0 0 10px;color:#059669;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">
                  Archivos adjuntos
                </div>
                <div v-for="(file, idx) in attachments" :key="idx"
                  :style="{ margin: idx === 0 ? '0' : '6px 0 0', color: '#1f2937', fontSize: '13px' }">
                  &#128206; {{ file.name }}
                </div>
              </div>
            </div>
            <div v-if="footer" style="padding:0 32px 20px;">
              <div style="margin:0;color:#4b5563;font-size:14px;line-height:1.6;white-space:pre-wrap;">{{ footer }}</div>
            </div>
            <div style="padding:0 32px;">
              <hr style="border:none;border-top:1px solid #e5e7eb;margin:0;" />
            </div>
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
    </section>

    <!-- ── History ── -->
    <section class="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-xl p-5">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="text-sm font-semibold text-gray-800 dark:text-white">Historial de correos enviados</h3>
      </div>

      <div v-if="loadingHistory && !history.length" class="text-xs text-gray-400 dark:text-gray-500 py-4 text-center">
        Cargando historial...
      </div>
      <div v-else-if="!history.length" class="text-xs text-gray-400 dark:text-gray-500 py-4 text-center">
        No se han enviado correos desde este diagnóstico.
      </div>
      <div v-else class="space-y-2">
        <div v-for="entry in history" :key="entry.id"
          class="border border-gray-100 dark:border-gray-700 rounded-lg overflow-hidden">
          <button type="button" @click="toggleExpand(entry.id)"
            class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-white/[0.03] transition-colors">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-xs font-medium text-gray-800 dark:text-white truncate">{{ entry.subject }}</span>
                <span class="px-1.5 py-0.5 rounded text-[10px] font-medium"
                  :class="{
                    'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400': entry.status === 'sent' || entry.status === 'delivered',
                    'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400': entry.status === 'failed' || entry.status === 'bounced',
                  }">{{ statusLabel(entry.status) }}</span>
              </div>
              <div class="flex items-center gap-2 mt-0.5">
                <span class="text-[11px] text-gray-500 dark:text-gray-400">{{ entry.recipient }}</span>
                <span class="text-[10px] text-gray-400 dark:text-gray-500">{{ formatDate(entry.sent_at) }}</span>
                <span class="text-[10px] text-gray-400 dark:text-gray-500">· {{ templateLabel(entry.template_key) }}</span>
              </div>
            </div>
            <svg class="w-4 h-4 text-gray-400 transition-transform" :class="{ 'rotate-180': expandedIds[entry.id] }"
              fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <div v-if="expandedIds[entry.id]" class="border-t border-gray-100 dark:border-gray-700 px-4 py-3 bg-gray-50 dark:bg-white/[0.03] space-y-3">
            <div v-if="entry.metadata?.greeting">
              <p class="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-0.5">Saludo</p>
              <p class="text-xs text-gray-700 dark:text-white/70">{{ entry.metadata.greeting }}</p>
            </div>
            <div v-if="entry.metadata?.sections?.length">
              <p class="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">Secciones</p>
              <div v-for="(section, idx) in entry.metadata.sections" :key="idx"
                class="bg-white dark:bg-gray-800 rounded-lg px-3 py-2 mb-1.5 border border-gray-100 dark:border-gray-700">
                <p class="text-xs text-gray-700 dark:text-white/70 whitespace-pre-wrap">{{ section }}</p>
              </div>
            </div>
            <div v-if="entry.metadata?.footer">
              <p class="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-0.5">Pie de correo</p>
              <p class="text-xs text-gray-700 dark:text-white/70">{{ entry.metadata.footer }}</p>
            </div>
            <div v-if="entry.metadata?.attachment_names?.length">
              <p class="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-0.5">Adjuntos</p>
              <div class="flex flex-wrap gap-1">
                <span v-for="(name, idx) in entry.metadata.attachment_names" :key="idx"
                  class="inline-flex items-center gap-1 px-2 py-0.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded text-[11px] text-gray-600 dark:text-gray-400">
                  &#128206; {{ name }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="hasNextPage" class="pt-3 text-center">
          <button type="button" :disabled="loadingHistory" @click="loadMore"
            class="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium text-gray-600 dark:text-white bg-gray-50 dark:bg-white/[0.03] rounded-lg hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-colors disabled:opacity-50">
            {{ loadingHistory ? 'Cargando...' : 'Cargar más' }}
          </button>
        </div>
      </div>
    </section>

    <MarkdownAttachmentModal
      :open="showMarkdownModal"
      :endpoint="`diagnostics/${diagnostic.id}/email/markdown-attachment/`"
      @close="showMarkdownModal = false"
      @attach="handleMarkdownAttach"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import draggable from 'vuedraggable';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import { DIAGNOSTIC_STATUS } from '~/stores/diagnostics_constants';
import MarkdownAttachmentModal from '~/components/MarkdownAttachmentModal.vue';
import { useMarkdownAttachmentHandler } from '~/composables/useMarkdownAttachmentHandler';
import { validateEmailAttachments } from '~/utils/emailAttachments';

const props = defineProps({
  diagnostic: { type: Object, required: true },
});

const store = useDiagnosticsStore();

let sectionIdSeq = 0;
const nextSectionId = () => ++sectionIdSeq;

const activeSubTab = ref('edit');
const recipient = ref(props.diagnostic.client?.email || '');
const subject = ref('');
const defaultGreeting = ref(
  props.diagnostic.client?.name ? `Hola ${props.diagnostic.client.name}` : 'Hola',
);
const defaultFooter = ref('Quedamos atentos a tus comentarios.');
const greeting = ref(defaultGreeting.value);
const sections = ref([{ id: nextSectionId(), text: '' }]);
const footer = ref(defaultFooter.value);
const attachments = ref([]);
const fileInput = ref(null);
const sending = ref(false);
const sendSuccess = ref(false);
const sendError = ref('');

const history = ref([]);
const loadingHistory = ref(false);
const expandedIds = ref({});
const currentPage = ref(1);
const hasNextPage = ref(false);

function addSection() {
  sections.value.push({ id: nextSectionId(), text: '' });
}
function removeSection(idx) {
  if (sections.value.length > 1) sections.value.splice(idx, 1);
}

function handleFilesChange(e) {
  const { validFiles, errors } = validateEmailAttachments(Array.from(e.target.files || []));
  sendError.value = errors.length ? errors.join(', ') : '';
  if (validFiles.length) attachments.value.push(...validFiles);
  if (fileInput.value) fileInput.value.value = '';
}

function removeAttachment(idx) {
  attachments.value.splice(idx, 1);
}

const showMarkdownModal = ref(false);
const canCreateMarkdownAttachment = computed(
  () => props.diagnostic.status === DIAGNOSTIC_STATUS.NEGOTIATING,
);

const { handleMarkdownAttach } = useMarkdownAttachmentHandler(attachments);

const canSend = computed(() => {
  if (!recipient.value.trim()) return false;
  if (!subject.value.trim()) return false;
  if (!sections.value.some(s => s.text.trim())) return false;
  return true;
});

let successTimer = null;
onBeforeUnmount(() => { clearTimeout(successTimer); });

async function handleSend() {
  sending.value = true;
  sendError.value = '';
  sendSuccess.value = false;

  const formData = new FormData();
  formData.append('recipient_email', recipient.value.trim());
  formData.append('subject', subject.value.trim());
  formData.append('greeting', greeting.value.trim());
  formData.append('sections', JSON.stringify(
    sections.value.filter(s => s.text.trim()).map(s => s.text),
  ));
  formData.append('footer', footer.value.trim());
  for (const file of attachments.value) {
    formData.append('attachments', file);
  }

  const result = await store.sendCustomEmail(props.diagnostic.id, formData);
  sending.value = false;

  if (result.success) {
    sendSuccess.value = true;
    resetForm();
    await loadHistory(1);
    clearTimeout(successTimer);
    successTimer = setTimeout(() => { sendSuccess.value = false; }, 5000);
  } else {
    sendError.value = result.error && result.error !== 'send_failed'
      ? result.error
      : 'Error al enviar el correo. Intenta de nuevo.';
  }
}

function resetForm() {
  subject.value = '';
  greeting.value = defaultGreeting.value;
  footer.value = defaultFooter.value;
  sections.value = [{ id: nextSectionId(), text: '' }];
  attachments.value = [];
  if (fileInput.value) fileInput.value.value = '';
}

async function loadHistory(page = 1) {
  loadingHistory.value = true;
  const result = await store.fetchEmailHistory(props.diagnostic.id, page);
  if (result.success) {
    if (page === 1) history.value = result.data.results;
    else history.value.push(...result.data.results);
    currentPage.value = result.data.page;
    hasNextPage.value = result.data.has_next;
  }
  loadingHistory.value = false;
}
function loadMore() { return loadHistory(currentPage.value + 1); }

function toggleExpand(id) {
  if (expandedIds.value[id]) delete expandedIds.value[id];
  else expandedIds.value[id] = true;
}

const STATUS_LABELS = { sent: 'Enviado', delivered: 'Entregado', bounced: 'Rebotado', failed: 'Fallido' };
function statusLabel(s) { return STATUS_LABELS[s] || s; }

const TEMPLATE_LABELS = {
  diagnostic_custom_email: 'Seguimiento',
  diagnostic_initial_sent: 'Doc 1',
  diagnostic_final_sent: 'Final',
  diagnostic_documents_sent: 'Documentos',
};
function templateLabel(key) { return TEMPLATE_LABELS[key] || key; }

function formatDate(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('es-CO', {
    day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

async function loadDefaults() {
  const result = await store.fetchEmailDefaults(props.diagnostic.id);
  if (result.success && result.data) {
    if (result.data.recipient_email) recipient.value = result.data.recipient_email;
    if (result.data.subject) subject.value = result.data.subject;
    if (result.data.greeting) {
      defaultGreeting.value = result.data.greeting;
      greeting.value = result.data.greeting;
    }
    if (result.data.footer) {
      defaultFooter.value = result.data.footer;
      footer.value = result.data.footer;
    }
  }
}

onMounted(() => {
  Promise.all([loadDefaults(), loadHistory()]);
});
</script>
