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
        <h3 class="text-sm font-semibold text-text-default">{{ activeMode === 'proposal' ? 'Correo de seguimiento' : 'Correo general' }}</h3>
      </div>

      <!-- Mode switcher -->
      <div class="inline-flex items-center bg-surface-raised rounded-full p-0.5 mb-4 gap-0.5">
        <button type="button"
          :class="activeMode === 'proposal'
            ? 'bg-primary text-white shadow-sm'
            : 'text-text-muted hover:text-text-default'"
          class="flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200"
          @click="activeMode = 'proposal'">
          Seguimiento
          <span
            title="Registra el envío como actividad de la propuesta y actualiza la fecha de seguimiento del vendedor."
            class="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full border text-[9px] font-bold cursor-help leading-none"
            :class="activeMode === 'proposal' ? 'border-white/50 text-white/80' : 'border-gray-400 text-gray-400 dark:border-green-light/40 dark:text-green-light/40'"
          >?</span>
        </button>
        <button type="button"
          :class="activeMode === 'branded'
            ? 'bg-primary text-white shadow-sm'
            : 'text-text-muted hover:text-text-default'"
          class="flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200"
          @click="activeMode = 'branded'">
          General
          <span
            title="Envío de marca genérico. No registra actividad ni afecta el seguimiento de la propuesta."
            class="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full border text-[9px] font-bold cursor-help leading-none"
            :class="activeMode === 'branded' ? 'border-white/50 text-white/80' : 'border-gray-400 text-gray-400 dark:border-green-light/40 dark:text-green-light/40'"
          >?</span>
        </button>
      </div>

      <!-- Sub-tab switcher -->
      <div class="flex gap-4 border-b border-border-muted mb-5">
        <button type="button"
          class="pb-2 text-sm transition-colors border-b-2"
          :class="activeSubTab === 'edit'
            ? 'border-emerald-600 text-text-brand  font-semibold'
            : 'border-transparent text-text-muted hover:text-text-default'"
          @click="activeSubTab = 'edit'">
          Editar
        </button>
        <button type="button"
          class="pb-2 text-sm transition-colors border-b-2"
          :class="activeSubTab === 'preview'
            ? 'border-emerald-600 text-text-brand  font-semibold'
            : 'border-transparent text-text-muted hover:text-text-default'"
          @click="activeSubTab = 'preview'">
          Vista previa
        </button>
      </div>

      <!-- ── Edit sub-tab ── -->
      <div v-if="activeSubTab === 'edit'" class="space-y-4">
        <!-- Recipient -->
        <div>
          <label class="block text-xs text-text-muted mb-1">Para</label>
          <input v-model="recipient" type="email" placeholder="correo@ejemplo.com"
            class="w-full px-3 py-2 border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 rounded-lg text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring" />
        </div>

        <!-- Subject -->
        <div>
          <label class="block text-xs text-text-muted mb-1">Asunto</label>
          <input v-model="subject" type="text" placeholder="Asunto del correo"
            class="w-full px-3 py-2 border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 rounded-lg text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring" />
        </div>

        <!-- Greeting -->
        <div>
          <label class="block text-xs text-text-muted mb-1">Saludo</label>
          <input v-model="greeting" type="text" placeholder="Hola Carlos"
            class="w-full px-3 py-2 border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 rounded-lg text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring" />
        </div>

        <!-- Sections (draggable) -->
        <div>
          <label class="block text-xs text-text-muted mb-2">Secciones del correo</label>
          <draggable v-model="sections" item-key="id" handle=".drag-handle" ghost-class="opacity-30"
            class="space-y-3">
            <template #item="{ element: section, index: idx }">
              <div class="bg-surface-raised rounded-lg p-3 border border-border-muted">
                <div class="flex items-center gap-2 mb-2">
                  <span class="drag-handle cursor-grab text-gray-400 dark:text-green-light/40 hover:text-text-muted select-none text-sm">⠿</span>
                  <span class="text-[10px] text-gray-400 dark:text-green-light/40 uppercase tracking-wide">Sección {{ idx + 1 }}</span>
                  <button v-if="sections.length > 1" type="button" @click="removeSection(idx)"
                    class="ml-auto text-gray-400 hover:text-red-500 transition-colors p-0.5">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
                <textarea v-model="section.text" rows="3" placeholder="Escribe el contenido de esta sección..."
                  class="w-full px-3 py-2 border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 rounded-lg text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring resize-y" />
              </div>
            </template>
          </draggable>
          <button type="button" @click="addSection"
            class="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-brand  bg-primary-soft rounded-lg hover:bg-primary-soft dark:hover:bg-emerald-900/30 transition-colors">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Agregar sección
          </button>
        </div>

        <!-- Footer -->
        <div>
          <label class="block text-xs text-text-muted mb-1">Pie de correo</label>
          <textarea v-model="footer" rows="2" placeholder="Texto de cierre..."
            class="w-full px-3 py-2 border border-border-default dark:border-white/[0.08]  dark:text-white dark:placeholder:text-green-light/40 rounded-lg text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring resize-y" />
        </div>

        <!-- Attachments -->
        <div>
          <label class="block text-xs text-text-muted mb-1">Adjuntos</label>
          <div class="flex flex-col items-start gap-3">
            <div class="flex flex-wrap items-center gap-2">
              <button type="button" @click="showAttachFromDocsModal = true"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary-soft text-text-brand  rounded-lg text-xs font-medium hover:bg-primary-soft dark:hover:bg-emerald-900/30 transition-colors">
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
              class="text-xs dark:text-white/70 file:mr-2 file:py-1.5 file:px-3 file:border-0 file:text-xs file:font-medium file:bg-primary-soft dark:file:bg-emerald-900/20 file:text-text-brand dark:file:text-emerald-400 file:rounded-lg hover:file:bg-primary-soft dark:hover:file:bg-emerald-900/30"
              @change="handleFilesChange" />
          </div>
          <div v-if="docRefs.length || attachments.length" class="mt-2 space-y-1">
            <div v-for="(ref, idx) in docRefs" :key="`ref-${ref.key}`"
              class="flex items-center justify-between py-1.5 px-3 bg-primary-soft dark:bg-emerald-900/10 border border-emerald-100 dark:border-emerald-900/30 rounded-lg">
              <span class="flex items-center gap-2 min-w-0">
                <span class="px-1.5 py-0.5 bg-primary-soft text-text-brand rounded text-[10px] font-medium">Documento</span>
                <span class="text-xs text-text-default truncate">{{ ref.label }}</span>
              </span>
              <button type="button" @click="removeDocRef(idx)"
                class="text-gray-400 hover:text-red-500 transition-colors p-0.5">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div v-for="(file, idx) in attachments" :key="`file-${idx}`"
              class="flex items-center justify-between py-1.5 px-3 bg-surface-raised rounded-lg">
              <span class="text-xs text-text-default truncate">{{ file.name }}</span>
              <button type="button" @click="removeAttachment(idx)"
                class="text-gray-400 hover:text-red-500 transition-colors p-0.5">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Send button -->
        <div class="flex items-center justify-between pt-2">
          <p v-if="sendError" class="text-xs text-red-500">{{ sendError }}</p>
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
            {{ sending ? 'Enviando...' : 'Enviar correo' }}
          </button>
        </div>
      </div>

      <!-- ── Preview sub-tab ── -->
      <div v-else>
        <!-- Subject badge -->
        <div class="flex items-center gap-2 bg-surface-raised rounded-lg px-3 py-2 mb-4 text-xs text-text-muted">
          <span class="font-medium text-text-default">Asunto:</span>
          <span>{{ subject || '(sin asunto)' }}</span>
        </div>

        <!-- Email preview card -->
        <div style="background-color:#f3f4f6;border-radius:12px;padding:24px 16px;font-family:Arial,'Helvetica Neue',Helvetica,sans-serif;">
          <div style="background-color:#ffffff;border-radius:16px;overflow:hidden;max-width:560px;margin:0 auto;">

            <!-- Header -->
            <div style="background-color:#059669;padding:28px 32px;text-align:center;">
              <div style="margin:0;color:#ffffff;font-size:22px;font-weight:700;letter-spacing:-0.02em;">
                Project App.
              </div>
              <div style="margin:6px 0 0;color:#d1fae5;font-size:13px;font-weight:400;">
                Transformación Digital
              </div>
            </div>

            <!-- Greeting -->
            <div style="padding:32px 32px 20px;">
              <div style="margin:0;color:#1f2937;font-size:20px;font-weight:600;white-space:pre-wrap;">{{ greeting || '(sin saludo)' }}</div>
            </div>

            <!-- Body sections -->
            <div v-for="(section, idx) in sections" :key="section.id" style="padding:0 32px 14px;">
              <div style="margin:0;color:#4b5563;font-size:15px;line-height:1.6;white-space:pre-wrap;">{{ section.text || '(sección vacía)' }}</div>
            </div>

            <!-- Attachment names -->
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

            <!-- Footer text -->
            <div v-if="footer" style="padding:0 32px 20px;">
              <div style="margin:0;color:#4b5563;font-size:14px;line-height:1.6;white-space:pre-wrap;">{{ footer }}</div>
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
    </section>

      </template>

      <template #aside>
    <!-- ── History ── -->
    <section class="bg-surface border border-border-muted rounded-xl p-5">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="text-sm font-semibold text-text-default">Historial de correos enviados</h3>
      </div>

      <div v-if="loadingHistory" class="text-xs text-gray-400 dark:text-green-light/40 py-4 text-center">Cargando historial...</div>

      <div v-else-if="!history.length" class="text-xs text-gray-400 dark:text-green-light/40 py-4 text-center">
        No se han enviado correos desde esta propuesta.
      </div>

      <div v-else class="space-y-2">
        <div v-for="entry in history" :key="entry.id"
          class="border border-border-muted rounded-lg overflow-hidden">
          <!-- Summary row (always visible) -->
          <button type="button" @click="toggleExpand(entry.id)"
            class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-surface-raised transition-colors">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-xs font-medium text-text-default truncate">{{ entry.subject }}</span>
                <span class="px-1.5 py-0.5 rounded text-[10px] font-medium"
                  :class="{
                    'bg-primary-soft text-text-brand dark:bg-emerald-900/30 ': entry.status === 'sent' || entry.status === 'delivered',
                    'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400': entry.status === 'failed' || entry.status === 'bounced',
                  }">
                  {{ statusLabel(entry.status) }}
                </span>
              </div>
              <div class="flex items-center gap-2 mt-0.5">
                <span class="text-[11px] text-text-muted">{{ entry.recipient }}</span>
                <span class="text-[10px] text-gray-400 dark:text-green-light/40">{{ formatDate(entry.sent_at) }}</span>
              </div>
            </div>
            <svg class="w-4 h-4 text-gray-400 transition-transform" :class="{ 'rotate-180': expandedIds[entry.id] }"
              fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Expanded detail -->
          <div v-if="expandedIds[entry.id]" class="border-t border-border-muted px-4 py-3 bg-surface-raised space-y-3">
            <div v-if="entry.metadata?.greeting">
              <p class="text-[10px] text-gray-400 dark:text-green-light/40 uppercase tracking-wide mb-0.5">Saludo</p>
              <p class="text-xs text-text-default">{{ entry.metadata.greeting }}</p>
            </div>
            <div v-if="entry.metadata?.sections?.length">
              <p class="text-[10px] text-gray-400 dark:text-green-light/40 uppercase tracking-wide mb-1">Secciones</p>
              <div v-for="(section, idx) in entry.metadata.sections" :key="idx"
                class="bg-surface rounded-lg px-3 py-2 mb-1.5 border border-border-muted">
                <p class="text-xs text-text-default whitespace-pre-wrap">{{ section }}</p>
              </div>
            </div>
            <div v-if="entry.metadata?.footer">
              <p class="text-[10px] text-gray-400 dark:text-green-light/40 uppercase tracking-wide mb-0.5">Pie de correo</p>
              <p class="text-xs text-text-default">{{ entry.metadata.footer }}</p>
            </div>
            <div v-if="entry.metadata?.attachment_names?.length">
              <p class="text-[10px] text-gray-400 dark:text-green-light/40 uppercase tracking-wide mb-0.5">Adjuntos</p>
              <div class="flex flex-wrap gap-1">
                <span v-for="(name, idx) in entry.metadata.attachment_names" :key="idx"
                  class="inline-flex items-center gap-1 px-2 py-0.5 bg-surface border border-border-default dark:border-white/[0.08] rounded text-[11px] text-text-muted/60">
                  &#128206; {{ name }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Load more -->
        <div v-if="hasNextPage" class="pt-3 text-center">
          <button type="button" :disabled="loadingHistory" @click="loadMore"
            class="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium text-text-muted bg-surface-raised rounded-lg hover:bg-surface-raised transition-colors disabled:opacity-50">
            {{ loadingHistory ? 'Cargando...' : 'Cargar más' }}
          </button>
        </div>
      </div>
    </section>
      </template>
    </TabSplitLayout>

    <MarkdownAttachmentModal
      :open="showMarkdownModal"
      :endpoint="`proposals/${proposal.id}/proposal-email/markdown-attachment/`"
      @close="showMarkdownModal = false"
      @attach="handleMarkdownAttach"
    />

    <AttachFromDocumentsModal
      :open="showAttachFromDocsModal"
      source="proposal"
      :entity="proposal"
      :preselected="docRefs.map(r => r.key)"
      @close="showAttachFromDocsModal = false"
      @attach="handleDocRefsAttach"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import draggable from 'vuedraggable';
import { usePanelToast } from '~/composables/usePanelToast';
import { useMarkdownAttachmentHandler } from '~/composables/useMarkdownAttachmentHandler';
import { validateEmailAttachments } from '~/utils/emailAttachments';
import MarkdownAttachmentModal from '~/components/MarkdownAttachmentModal.vue';
import AttachFromDocumentsModal from '~/components/AttachFromDocumentsModal.vue';
import TabSplitLayout from '~/components/panel/TabSplitLayout.vue';
import { useDocRefsAttachment } from '~/composables/useDocRefsAttachment';

const { showToast } = usePanelToast();

const props = defineProps({
  proposal: { type: Object, required: true },
});

const activeMode = ref('proposal');

const basePath = computed(() =>
  activeMode.value === 'proposal' ? 'proposal-email' : 'branded-email',
);

const proposalStore = useProposalStore();

let sectionIdSeq = 0;
const nextSectionId = () => ++sectionIdSeq;

// ── Composer state ──
const activeSubTab = ref('edit');
const recipient = ref(props.proposal.client_email || '');
const subject = ref('');
const defaultGreeting = ref(
  props.proposal.client_name ? `Hola ${props.proposal.client_name}` : 'Hola',
);
const defaultFooter = ref('Quedamos atentos a tus comentarios.\nUn abrazo, el equipo de Project App.');
const greeting = ref(defaultGreeting.value);
const sections = ref([{ id: nextSectionId(), text: '' }]);
const footer = ref(defaultFooter.value);
const attachments = ref([]);
const { docRefs, removeDocRef, handleDocRefsAttach, appendDocRefsToFormData, resetDocRefs }
  = useDocRefsAttachment();
const showAttachFromDocsModal = ref(false);
const fileInput = ref(null);
const sending = ref(false);
const sendError = ref('');

// ── History state ──
const history = ref([]);
const loadingHistory = ref(false);
const expandedIds = ref({});
const currentPage = ref(1);
const hasNextPage = ref(false);

// ── Sections ──
function addSection() {
  sections.value.push({ id: nextSectionId(), text: '' });
}

function removeSection(idx) {
  if (sections.value.length > 1) {
    sections.value.splice(idx, 1);
  }
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
const canCreateMarkdownAttachment = true;

const { handleMarkdownAttach } = useMarkdownAttachmentHandler(attachments);

// ── Validation ──
const canSend = computed(() => {
  if (!recipient.value.trim()) return false;
  if (!subject.value.trim()) return false;
  if (!sections.value.some(s => s.text.trim())) return false;
  return true;
});

async function handleSend() {
  sending.value = true;
  sendError.value = '';

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

  const result = await proposalStore.sendComposedEmail(props.proposal.id, formData, basePath.value);
  sending.value = false;

  if (result.success) {
    showToast({ type: 'success', text: 'Correo enviado correctamente.' });
    resetForm();
    await loadHistory(1);
  } else {
    showToast({ type: 'error', text: 'Error al enviar el correo. Intenta de nuevo.' });
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

// ── History ──
async function loadHistory(page = 1) {
  loadingHistory.value = true;
  const result = await proposalStore.fetchEmailHistory(props.proposal.id, page, basePath.value);
  if (result.success) {
    if (page === 1) {
      history.value = result.data.results;
    } else {
      history.value.push(...result.data.results);
    }
    currentPage.value = result.data.page;
    hasNextPage.value = result.data.has_next;
  }
  loadingHistory.value = false;
}

async function loadMore() {
  await loadHistory(currentPage.value + 1);
}

function toggleExpand(id) {
  if (expandedIds.value[id]) {
    delete expandedIds.value[id];
  } else {
    expandedIds.value[id] = true;
  }
}

const STATUS_LABELS = { sent: 'Enviado', delivered: 'Entregado', bounced: 'Rebotado', failed: 'Fallido' };
function statusLabel(s) {
  return STATUS_LABELS[s] || s;
}

function formatDate(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('es-CO', {
    day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

async function loadDefaults() {
  const result = await proposalStore.fetchEmailDefaults(props.proposal.id, basePath.value);
  if (result.success && result.data) {
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

watch(activeMode, async () => {
  resetForm();
  await Promise.all([loadDefaults(), loadHistory()]);
});

onMounted(() => {
  Promise.all([loadDefaults(), loadHistory()]);
});
</script>
