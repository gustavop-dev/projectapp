<template>
  <div class="max-w-4xl mx-auto space-y-8">

    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-light text-text-default">Emails</h1>
        <p class="text-sm text-text-muted mt-1">Envía correos con el branding de la marca a cualquier destinatario.</p>
      </div>
    </div>

    <!-- ── Email composer ── -->
    <section class="bg-surface border border-border-muted rounded-xl p-5  ">
      <div class="flex items-center gap-2 mb-5">
        <svg class="w-5 h-5 text-text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <h3 class="text-sm font-semibold text-text-default">Correo general con branding</h3>
      </div>

      <!-- Sub-tab switcher -->
      <div class="flex gap-4 border-b border-border-muted  mb-5">
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
            class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring" />
        </div>

        <!-- Subject -->
        <div>
          <label class="block text-xs text-text-muted mb-1">Asunto</label>
          <input v-model="subject" type="text" placeholder="Asunto del correo"
            class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring" />
        </div>

        <!-- Greeting -->
        <div>
          <label class="block text-xs text-text-muted mb-1">Saludo</label>
          <input v-model="greeting" type="text" placeholder="Hola"
            class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring" />
        </div>

        <!-- Sections (draggable) -->
        <div>
          <label class="block text-xs text-text-muted mb-2">Secciones del correo</label>
          <draggable v-model="sections" item-key="id" handle=".drag-handle" ghost-class="opacity-30"
            class="space-y-3">
            <template #item="{ element: section, index: idx }">
              <div class="bg-gray-50  rounded-lg p-3 border border-border-muted ">
                <div class="flex items-center gap-2 mb-2">
                  <span class="drag-handle cursor-grab text-gray-400 hover:text-text-muted select-none text-sm">⠿</span>
                  <span class="text-[10px] text-gray-400 uppercase tracking-wide">Sección {{ idx + 1 }}</span>
                  <button v-if="sections.length > 1" type="button" @click="removeSection(idx)"
                    class="ml-auto text-gray-400 hover:text-red-500 transition-colors p-0.5">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
                <textarea v-model="section.text" rows="3" placeholder="Escribe el contenido de esta sección..."
                  class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface  focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring resize-y" />
              </div>
            </template>
          </draggable>
          <button type="button" @click="addSection"
            class="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-brand  bg-primary-soft rounded-lg hover:bg-primary-soft transition-colors">
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
            class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring resize-y" />
        </div>

        <!-- Attachments -->
        <div>
          <label class="block text-xs text-text-muted mb-1">Adjuntos</label>
          <input ref="fileInput" type="file" multiple
            accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
            class="text-xs file:mr-2 file:py-1.5 file:px-3 file:border-0 file:text-xs file:font-medium file:bg-primary-soft file:text-text-brand file:rounded-lg hover:file:bg-primary-soft "
            @change="handleFilesChange" />
          <div v-if="attachments.length" class="mt-2 space-y-1">
            <div v-for="(file, idx) in attachments" :key="idx"
              class="flex items-center justify-between py-1.5 px-3 bg-gray-50  rounded-lg">
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
            {{ sending ? 'Enviando...' : 'Enviar correo' }}
          </button>
        </div>
      </div>

      <!-- ── Preview sub-tab ── -->
      <div v-else>
        <!-- Subject badge -->
        <div class="flex items-center gap-2 bg-gray-50  rounded-lg px-3 py-2 mb-4 text-xs text-text-muted">
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

    <!-- ── History ── -->
    <section class="bg-surface border border-border-muted rounded-xl p-5  ">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="text-sm font-semibold text-text-default">Historial de correos enviados</h3>
      </div>

      <div v-if="emailStore.isLoadingHistory" class="text-xs text-gray-400 py-4 text-center">Cargando historial...</div>

      <div v-else-if="!emailStore.history.length" class="text-xs text-gray-400 py-4 text-center">
        No se han enviado correos aún.
      </div>

      <div v-else class="space-y-2">
        <div v-for="entry in emailStore.history" :key="entry.id"
          class="border border-border-muted  rounded-lg overflow-hidden">
          <!-- Summary row -->
          <button type="button" @click="toggleExpand(entry.id)"
            class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-xs font-medium text-text-default truncate">{{ entry.subject }}</span>
                <span class="px-1.5 py-0.5 rounded text-[10px] font-medium"
                  :class="{
                    'bg-primary-soft text-text-brand ': entry.status === 'sent' || entry.status === 'delivered',
                    'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400': entry.status === 'failed' || entry.status === 'bounced',
                  }">
                  {{ statusLabel(entry.status) }}
                </span>
              </div>
              <div class="flex items-center gap-2 mt-0.5">
                <span class="text-[11px] text-text-muted">{{ entry.recipient }}</span>
                <span class="text-[10px] text-gray-400">{{ formatDate(entry.sent_at) }}</span>
              </div>
            </div>
            <svg class="w-4 h-4 text-gray-400 transition-transform" :class="{ 'rotate-180': expandedIds[entry.id] }"
              fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Expanded detail -->
          <div v-if="expandedIds[entry.id]" class="border-t border-border-muted  px-4 py-3 bg-gray-50  space-y-3">
            <div v-if="entry.metadata?.greeting">
              <p class="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">Saludo</p>
              <p class="text-xs text-text-default">{{ entry.metadata.greeting }}</p>
            </div>
            <div v-if="entry.metadata?.sections?.length">
              <p class="text-[10px] text-gray-400 uppercase tracking-wide mb-1">Secciones</p>
              <div v-for="(section, idx) in entry.metadata.sections" :key="idx"
                class="bg-surface rounded-lg px-3 py-2 mb-1.5 border border-border-muted ">
                <p class="text-xs text-text-default whitespace-pre-wrap">{{ section }}</p>
              </div>
            </div>
            <div v-if="entry.metadata?.footer">
              <p class="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">Pie de correo</p>
              <p class="text-xs text-text-default">{{ entry.metadata.footer }}</p>
            </div>
            <div v-if="entry.metadata?.attachment_names?.length">
              <p class="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">Adjuntos</p>
              <div class="flex flex-wrap gap-1">
                <span v-for="(name, idx) in entry.metadata.attachment_names" :key="idx"
                  class="inline-flex items-center gap-1 px-2 py-0.5 bg-surface border border-border-default rounded text-[11px] text-text-muted">
                  &#128206; {{ name }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Load more -->
        <div v-if="emailStore.historyPagination.has_next" class="pt-3 text-center">
          <button type="button" :disabled="emailStore.isLoadingHistory" @click="loadMore"
            class="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium text-text-muted bg-gray-50  rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors disabled:opacity-50">
            {{ emailStore.isLoadingHistory ? 'Cargando...' : 'Cargar más' }}
          </button>
        </div>
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import draggable from 'vuedraggable';
import { useEmailStore } from '~/stores/emails';
import { validateEmailAttachments } from '~/utils/emailAttachments';

definePageMeta({ layout: 'admin' });

const emailStore = useEmailStore();

let sectionIdSeq = 0;
const nextSectionId = () => ++sectionIdSeq;

// ── Defaults (declared early so resetForm can reference them) ──
const defaultGreeting = ref('Hola');
const defaultFooter = ref('Quedamos atentos a tus comentarios.\nUn abrazo, el equipo de Project App.');

// ── Composer state ──
const activeSubTab = ref('edit');
const recipient = ref('');
const subject = ref('');
const greeting = ref(defaultGreeting.value);
const sections = ref([{ id: nextSectionId(), text: '' }]);
const footer = ref(defaultFooter.value);
const attachments = ref([]);
const fileInput = ref(null);
const sending = ref(false);
const sendSuccess = ref(false);
const sendError = ref('');

// ── History state ──
const expandedIds = ref({});

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

// ── Validation ──
const canSend = computed(() => {
  if (!recipient.value.trim()) return false;
  if (!subject.value.trim()) return false;
  if (!sections.value.some(s => s.text.trim())) return false;
  return true;
});

// ── Send ──
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

  const result = await emailStore.sendEmail(formData);
  sending.value = false;

  if (result.success) {
    sendSuccess.value = true;
    resetForm();
    await emailStore.fetchHistory(1);
    clearTimeout(successTimer);
    successTimer = setTimeout(() => { sendSuccess.value = false; }, 5000);
  } else {
    sendError.value = result.error || 'Error al enviar el correo. Intenta de nuevo.';
  }
}

function resetForm() {
  recipient.value = '';
  subject.value = '';
  greeting.value = defaultGreeting.value;
  footer.value = defaultFooter.value;
  sections.value = [{ id: nextSectionId(), text: '' }];
  attachments.value = [];
  if (fileInput.value) fileInput.value.value = '';
}

async function loadDefaults() {
  const result = await emailStore.fetchDefaults();
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

// ── History helpers ──
async function loadMore() {
  const nextPage = emailStore.historyPagination.page + 1;
  await emailStore.fetchHistory(nextPage);
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

onMounted(() => {
  Promise.all([loadDefaults(), emailStore.fetchHistory()]);
});
</script>
