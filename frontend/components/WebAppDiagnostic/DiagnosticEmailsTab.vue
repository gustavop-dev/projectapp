<template>
  <div>
    <TabSplitLayout>
      <template #main>
    <!-- ── Email composer ── -->
    <section class="bg-surface border border-border-muted rounded-xl p-5">
      <div class="flex items-center gap-2 mb-5">
        <svg class="w-5 h-5 text-text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <h3 class="text-sm font-semibold text-text-default dark:text-white">Correo de seguimiento</h3>
      </div>

      <!-- Sub-tab switcher -->
      <div class="mb-5">
        <BaseTabs
          v-model="activeSubTab"
          :tabs="[{ id: 'edit', label: 'Editar' }, { id: 'preview', label: 'Vista previa' }]"
        />
      </div>

      <!-- ── Edit sub-tab ── -->
      <div v-if="activeSubTab === 'edit'" class="space-y-4">
        <div>
          <label class="block text-xs text-text-muted dark:text-white/70 mb-1">Para</label>
          <input v-model="recipient" type="email" placeholder="correo@ejemplo.com"
            class="w-full px-3 py-2 border border-border-default dark:text-white dark:placeholder:text-text-muted rounded-lg text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500" />
        </div>

        <div>
          <label class="block text-xs text-text-muted dark:text-white/70 mb-1">Asunto</label>
          <input v-model="subject" type="text" placeholder="Asunto del correo"
            class="w-full px-3 py-2 border border-border-default dark:text-white dark:placeholder:text-text-muted rounded-lg text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500" />
        </div>

        <div>
          <label class="block text-xs text-text-muted dark:text-white/70 mb-1">Saludo</label>
          <input v-model="greeting" type="text" placeholder="Hola Carlos"
            class="w-full px-3 py-2 border border-border-default dark:text-white dark:placeholder:text-text-muted rounded-lg text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500" />
        </div>

        <!-- Sections (draggable) -->
        <div>
          <label class="block text-xs text-text-muted dark:text-white/70 mb-2">Secciones del correo</label>
          <draggable v-model="sections" item-key="id" handle=".drag-handle" ghost-class="opacity-30"
            class="space-y-3">
            <template #item="{ element: section, index: idx }">
              <div class="bg-surface-muted rounded-lg p-3 border border-border-muted">
                <div class="flex items-center gap-2 mb-2">
                  <span class="drag-handle cursor-grab text-text-subtle hover:text-text-muted select-none text-sm">⠿</span>
                  <span class="text-2xs text-text-subtle uppercase tracking-wide">Sección {{ idx + 1 }}</span>
                  <button v-if="sections.length > 1" type="button"
                    class="ml-auto text-text-subtle hover:text-red-500 transition-colors p-0.5"
                    @click="removeSection(idx)">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
                <textarea v-model="section.text" rows="3" placeholder="Escribe el contenido de esta sección..."
                  class="w-full px-3 py-2 border border-border-default dark:text-white dark:placeholder:text-text-muted rounded-lg text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 resize-y" />
              </div>
            </template>
          </draggable>
          <button type="button" @click="addSection"
            class="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-brand bg-primary-soft rounded-lg hover:bg-primary-soft transition-colors">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Agregar sección
          </button>
        </div>

        <div>
          <label class="block text-xs text-text-muted dark:text-white/70 mb-1">Pie de correo</label>
          <textarea v-model="footer" rows="2" placeholder="Texto de cierre..."
            class="w-full px-3 py-2 border border-border-default dark:text-white dark:placeholder:text-text-muted rounded-lg text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 resize-y" />
        </div>

        <div>
          <label class="block text-xs text-text-muted dark:text-white/70 mb-1">Adjuntos</label>
          <div class="flex flex-col items-start gap-3">
            <div class="flex flex-wrap items-center gap-2">
              <button type="button" @click="showAttachFromDocsModal = true"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary-soft text-text-brand rounded-lg text-xs font-medium hover:bg-primary-soft transition-colors">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
                Adjuntar desde Documentos
              </button>
              <button v-if="canCreateMarkdownAttachment" type="button" @click="showMarkdownModal = true"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 rounded-lg text-xs font-medium hover:bg-indigo-100 dark:hover:bg-indigo-900/30 transition-colors">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Crear documento desde markdown
              </button>
            </div>
            <input ref="fileInput" type="file" multiple
              accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
              class="text-xs dark:text-white/70 file:mr-2 file:py-1.5 file:px-3 file:border-0 file:text-xs file:font-medium file:bg-primary-soft file:text-text-brand file:rounded-lg hover:file:bg-primary-soft"
              @change="handleFilesChange" />
          </div>
          <div v-if="docRefs.length || attachments.length" class="mt-2 space-y-1">
            <div v-for="(ref, idx) in docRefs" :key="`ref-${ref.key}`"
              class="flex items-center justify-between py-1.5 px-3 bg-primary-soft border border-emerald-100 dark:border-emerald-900/30 rounded-lg">
              <span class="flex items-center gap-2 min-w-0">
                <span class="px-1.5 py-0.5 bg-primary-soft text-text-brand rounded text-2xs font-medium">Documento</span>
                <span class="text-xs text-text-default dark:text-white/70 truncate">{{ ref.label }}</span>
              </span>
              <button type="button" @click="removeDocRef(idx)"
                class="text-text-subtle hover:text-red-500 transition-colors p-0.5">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div v-for="(file, idx) in attachments" :key="`file-${idx}`"
              class="flex items-center justify-between py-1.5 px-3 bg-surface-muted rounded-lg">
              <span class="text-xs text-text-default dark:text-white/70 truncate">{{ file.name }}</span>
              <button type="button" @click="removeAttachment(idx)"
                class="text-text-subtle hover:text-red-500 transition-colors p-0.5">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-between pt-2">
          <p v-if="sendError" class="text-xs text-red-500">{{ sendError }}</p>
          <p v-else-if="sendSuccess" class="text-xs text-text-brand">Correo enviado correctamente.</p>
          <span v-else />
          <button type="button" :disabled="!canSend || sending" @click="handleSend"
            class="inline-flex items-center gap-1.5 px-4 py-2 bg-primary text-white rounded-lg text-xs font-medium hover:bg-primary-strong transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            <svg v-if="!sending" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            <svg v-else class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ sending ? 'Enviando…' : 'Enviar correo' }}
          </button>
        </div>
      </div>

      <!-- ── Preview sub-tab ── -->
      <div v-else>
        <div class="flex items-center gap-2 bg-surface-muted rounded-lg px-3 py-2 mb-4 text-xs text-text-muted">
          <span class="font-medium text-text-default dark:text-white/70">Asunto:</span>
          <span>{{ subject || '(sin asunto)' }}</span>
        </div>

        <EmailPreviewCard
          :greeting="greeting"
          :sections="sections"
          :footer="footer"
          :attachments="attachments"
        />
      </div>
    </section>

      </template>

      <template #aside>
    <!-- ── History ── -->
    <section class="bg-surface border border-border-muted rounded-xl p-5">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="text-sm font-semibold text-text-default dark:text-white">Historial de correos enviados</h3>
      </div>

      <EmailHistoryList
        :history="history"
        :loading="loadingHistory"
        :has-next-page="hasNextPage"
        empty-label="No se han enviado correos desde este diagnóstico."
        @load-more="loadMore"
      >
        <template #entry-meta="{ entry }">
          <span class="text-2xs text-text-subtle">· {{ templateLabel(entry.template_key) }}</span>
        </template>
      </EmailHistoryList>
    </section>
      </template>
    </TabSplitLayout>

    <MarkdownAttachmentModal
      :open="showMarkdownModal"
      :endpoint="`diagnostics/${diagnostic.id}/email/markdown-attachment/`"
      show-diagnostic-templates
      @close="showMarkdownModal = false"
      @attach="handleMarkdownAttach"
    />

    <AttachFromDocumentsModal
      :open="showAttachFromDocsModal"
      source="diagnostic"
      :entity="diagnostic"
      :templates="diagnosticTemplates"
      :preselected="docRefs.map(r => r.key)"
      @close="showAttachFromDocsModal = false"
      @attach="handleDocRefsAttach"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import BaseTabs from '~/components/base/BaseTabs.vue';
import BaseCollapse from '~/components/base/BaseCollapse.vue';
import draggable from 'vuedraggable';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import { DIAGNOSTIC_STATUS } from '~/stores/diagnostics_constants';
import MarkdownAttachmentModal from '~/components/MarkdownAttachmentModal.vue';
import AttachFromDocumentsModal from '~/components/AttachFromDocumentsModal.vue';
import EmailPreviewCard from '~/components/EmailPreviewCard.vue';
import EmailHistoryList from '~/components/EmailHistoryList.vue';
import TabSplitLayout from '~/components/panel/TabSplitLayout.vue';
import { useMarkdownAttachmentHandler } from '~/composables/useMarkdownAttachmentHandler';
import { useDocRefsAttachment } from '~/composables/useDocRefsAttachment';
import { validateEmailAttachments } from '~/utils/emailAttachments';
import { get_request } from '~/stores/services/request_http';

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
const { docRefs, removeDocRef, handleDocRefsAttach, appendDocRefsToFormData, resetDocRefs }
  = useDocRefsAttachment();
const showAttachFromDocsModal = ref(false);
const diagnosticTemplates = ref([]);
const fileInput = ref(null);
const sending = ref(false);
const sendSuccess = ref(false);
const sendError = ref('');

const history = ref([]);
const loadingHistory = ref(false);
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
  appendDocRefsToFormData(formData);

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
  resetDocRefs();
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

// Status/date/expand rendering now lives in EmailHistoryList; only the
// diagnostics-specific template label stays here (passed via #entry-meta).
const TEMPLATE_LABELS = {
  diagnostic_custom_email: 'Seguimiento',
  diagnostic_initial_sent: 'Doc 1',
  diagnostic_final_sent: 'Final',
  diagnostic_documents_sent: 'Documentos',
};
function templateLabel(key) { return TEMPLATE_LABELS[key] || key; }

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

async function loadDiagnosticTemplates() {
  try {
    const res = await get_request('diagnostic-templates/');
    diagnosticTemplates.value = res.data || [];
  } catch (e) {
    diagnosticTemplates.value = [];
  }
}

onMounted(() => {
  Promise.all([loadDefaults(), loadHistory(), loadDiagnosticTemplates()]);
});
</script>
