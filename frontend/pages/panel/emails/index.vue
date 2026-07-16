<template>
  <div class="max-w-4xl mx-auto space-y-8">

    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-light text-text-default">Emails</h1>
        <p class="text-sm text-text-muted mt-1">Envía correos con el branding de la marca a cualquier destinatario.</p>
      </div>
    </div>

    <!-- ── Page tabs ── -->
    <BaseTabs v-model="activeTab" :tabs="PAGE_TABS" variant="underline" />

    <!-- ── Email composer ── -->
    <section v-if="activeTab === 'compose'" class="bg-surface border border-border-muted rounded-xl p-5  ">
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
              <div class="bg-surface-muted  rounded-lg p-3 border border-border-muted ">
                <div class="flex items-center gap-2 mb-2">
                  <span class="drag-handle cursor-grab text-text-subtle hover:text-text-muted select-none text-sm">⠿</span>
                  <span class="text-[10px] text-text-muted uppercase tracking-wide">Sección {{ idx + 1 }}</span>
                  <span class="ml-auto flex items-center gap-1.5">
                    <span class="text-[10px] font-medium text-text-muted uppercase tracking-wide">Markdown</span>
                    <BaseToggle v-model="section.markdown" size="sm" aria-label="Activar Markdown en esta sección" />
                  </span>
                  <button v-if="sections.length > 1" type="button" @click="removeSection(idx)"
                    class="text-text-subtle hover:text-danger-strong transition-colors p-0.5">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
                <textarea v-model="section.text" v-auto-resize rows="3" placeholder="Escribe el contenido de esta sección..."
                  class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface  focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring resize-none" />
                <p v-if="section.markdown" class="mt-1 text-[10px] text-text-subtle">
                  Soporta **negrita**, *cursiva*, listas con -, [enlaces](https://...) y títulos con #.
                </p>
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
          <textarea v-model="footer" v-auto-resize rows="2" placeholder="Texto de cierre..."
            class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring resize-none" />
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
              class="flex items-center justify-between py-1.5 px-3 bg-surface-muted  rounded-lg">
              <span class="text-xs text-text-default truncate">{{ file.name }}</span>
              <button type="button" @click="removeAttachment(idx)"
                class="text-text-subtle hover:text-danger-strong transition-colors p-0.5">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Send button -->
        <div class="flex items-center justify-between pt-2">
          <p v-if="sendError" class="text-xs text-danger-strong">{{ sendError }}</p>
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
        <div class="flex items-center gap-2 bg-surface-muted  rounded-lg px-3 py-2 mb-4 text-xs text-text-muted">
          <span class="font-medium text-text-default">Asunto:</span>
          <span>{{ subject || '(sin asunto)' }}</span>
        </div>

        <!-- Server-rendered preview: the real branded template (emails/branded_email.html) -->
        <ComposedEmailPreview
          :subject="subject"
          :greeting="greeting"
          :sections="sections"
          :footer="footer"
          :attachment-names="attachments.map(f => f.name)"
        />
      </div>
    </section>

    <!-- ── Defaults config ── -->
    <section v-else-if="activeTab === 'defaults'" class="bg-surface border border-border-muted rounded-xl p-5">
      <div class="flex items-center gap-2 mb-2">
        <svg class="w-5 h-5 text-text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <h3 class="text-sm font-semibold text-text-default">Valores por defecto</h3>
      </div>
      <p class="text-xs text-text-muted mb-5">
        Estos valores se precargan automáticamente al redactar un correo nuevo.
      </p>

      <div v-if="emailStore.isLoadingDefaults" class="text-xs text-text-subtle py-4 text-center">Cargando valores...</div>

      <div v-else class="space-y-4 max-w-xl">
        <div>
          <label class="block text-xs text-text-muted mb-1">Saludo por defecto</label>
          <BaseInput v-model="cfgGreeting" placeholder="Hola {client_name}" />
          <p v-if="availableVariables.length" class="mt-1 text-[11px] text-text-muted">
            Variables disponibles: <span class="font-mono">{{ variablesHint }}</span>
          </p>
        </div>

        <div>
          <label class="block text-xs text-text-muted mb-1">Pie de correo por defecto</label>
          <BaseTextarea v-model="cfgFooter" :rows="3" placeholder="Texto de cierre..." />
        </div>

        <div>
          <label class="block text-xs text-text-muted mb-1">Firmante por defecto</label>
          <BaseSelect v-model="cfgSigner" :options="signerOptions" placeholder="Selecciona un firmante" />
          <p class="mt-1 text-[11px] text-text-muted">La firma aparece al final del correo con nombre y cargo.</p>
        </div>

        <div class="flex flex-col sm:flex-row sm:items-center gap-2 pt-2">
          <BaseButton size="sm" :disabled="emailStore.isSavingDefaults" @click="handleSaveDefaults">
            {{ emailStore.isSavingDefaults ? 'Guardando...' : 'Guardar valores' }}
          </BaseButton>
          <BaseButton size="sm" variant="ghost" :disabled="emailStore.isSavingDefaults" @click="handleRestoreDefaults">
            Restaurar valores originales
          </BaseButton>
        </div>
      </div>
    </section>

    <!-- ── History ── -->
    <section v-else class="bg-surface border border-border-muted rounded-xl p-5  ">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-info-strong" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="text-sm font-semibold text-text-default">Historial de correos enviados</h3>
      </div>

      <div v-if="emailStore.isLoadingHistory" class="text-xs text-text-subtle py-4 text-center">Cargando historial...</div>

      <div v-else-if="!emailStore.history.length" class="text-xs text-text-subtle py-4 text-center">
        No se han enviado correos aún.
      </div>

      <div v-else class="space-y-2">
        <div v-for="entry in emailStore.history" :key="entry.id"
          class="border border-border-muted  rounded-lg overflow-hidden">
          <!-- Summary row -->
          <button type="button" @click="toggleExpand(entry.id)"
            class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-surface-muted transition-colors">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-xs font-medium text-text-default truncate">{{ entry.subject }}</span>
                <span class="px-1.5 py-0.5 rounded text-[10px] font-medium"
                  :class="{
                    'bg-primary-soft text-text-brand ': entry.status === 'sent' || entry.status === 'delivered',
                    'bg-danger-soft text-danger-strong': entry.status === 'failed' || entry.status === 'bounced',
                  }">
                  {{ statusLabel(entry.status) }}
                </span>
              </div>
              <div class="flex items-center gap-2 mt-0.5">
                <span class="text-[11px] text-text-muted">{{ entry.recipient }}</span>
                <span class="text-[10px] text-text-subtle">{{ formatDate(entry.sent_at) }}</span>
              </div>
            </div>
            <svg class="w-4 h-4 text-text-subtle transition-transform" :class="{ 'rotate-180': expandedIds[entry.id] }"
              fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Expanded detail -->
          <div v-if="expandedIds[entry.id]" class="border-t border-border-muted  px-4 py-3 bg-surface-muted  space-y-3">
            <div v-if="entry.metadata?.greeting">
              <p class="text-[10px] text-text-subtle uppercase tracking-wide mb-0.5">Saludo</p>
              <p class="text-xs text-text-default">{{ entry.metadata.greeting }}</p>
            </div>
            <div v-if="entry.metadata?.sections?.length">
              <p class="text-[10px] text-text-subtle uppercase tracking-wide mb-1">Secciones</p>
              <div v-for="(section, idx) in entry.metadata.sections" :key="idx"
                class="bg-surface rounded-lg px-3 py-2 mb-1.5 border border-border-muted ">
                <span v-if="sectionIsMarkdown(section)"
                  class="inline-block mb-1 px-1.5 py-0.5 bg-primary-soft text-text-brand rounded text-[9px] font-medium uppercase tracking-wide">MD</span>
                <p class="text-xs text-text-default whitespace-pre-wrap">{{ sectionText(section) }}</p>
              </div>
            </div>
            <div v-if="entry.metadata?.footer">
              <p class="text-[10px] text-text-subtle uppercase tracking-wide mb-0.5">Pie de correo</p>
              <p class="text-xs text-text-default">{{ entry.metadata.footer }}</p>
            </div>
            <div v-if="entry.metadata?.attachment_names?.length">
              <p class="text-[10px] text-text-subtle uppercase tracking-wide mb-0.5">Adjuntos</p>
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
            class="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium text-text-muted bg-surface-muted  rounded-lg hover:bg-surface-raised transition-colors disabled:opacity-50">
            {{ emailStore.isLoadingHistory ? 'Cargando...' : 'Cargar más' }}
          </button>
        </div>
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import draggable from 'vuedraggable';
import ComposedEmailPreview from '~/components/ComposedEmailPreview.vue';
import { useEmailStore } from '~/stores/emails';
import { validateEmailAttachments } from '~/utils/emailAttachments';
import { vAutoResize } from '~/utils/autoResizeDirective';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { usePanelNotify } from '~/composables/usePanelNotify';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const emailStore = useEmailStore();
const notify = usePanelNotify();
const route = useRoute();
const router = useRouter();

// ── Page tabs (synced to ?tab= for deep-linking) ──
const PAGE_TABS = [
  { id: 'compose', label: 'Redactar' },
  { id: 'history', label: 'Historial' },
  { id: 'defaults', label: 'Valores por defecto' },
];
const TAB_IDS = PAGE_TABS.map(t => t.id);
const activeTab = ref(TAB_IDS.includes(route.query.tab) ? route.query.tab : 'compose');
watch(activeTab, (tab) => {
  router.replace({ query: { ...route.query, tab } });
});

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
const sections = ref([{ id: nextSectionId(), text: '', markdown: false }]);
const footer = ref(defaultFooter.value);
const attachments = ref([]);
const fileInput = ref(null);
const sending = ref(false);
const sendError = ref('');

// ── History state ──
const expandedIds = ref({});

// ── Sections ──
function addSection() {
  sections.value.push({ id: nextSectionId(), text: '', markdown: false });
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
async function handleSend() {
  sending.value = true;
  sendError.value = '';

  const formData = new FormData();
  formData.append('recipient_email', recipient.value.trim());
  formData.append('subject', subject.value.trim());
  formData.append('greeting', greeting.value.trim());
  formData.append('sections', JSON.stringify(
    sections.value.filter(s => s.text.trim()).map(s => ({ text: s.text, markdown: !!s.markdown })),
  ));
  formData.append('footer', footer.value.trim());
  for (const file of attachments.value) {
    formData.append('attachments', file);
  }

  const result = await emailStore.sendEmail(formData);
  sending.value = false;

  if (result.success) {
    notify.success({ title: 'Correo enviado correctamente.' });
    resetForm();
    await emailStore.fetchHistory(1);
  } else {
    sendError.value = result.error || 'Error al enviar el correo. Intenta de nuevo.';
    notify.error({ title: 'No se pudo enviar el correo', detail: sendError.value });
  }
}

function resetForm() {
  recipient.value = '';
  subject.value = '';
  greeting.value = defaultGreeting.value;
  footer.value = defaultFooter.value;
  sections.value = [{ id: nextSectionId(), text: '', markdown: false }];
  attachments.value = [];
  if (fileInput.value) fileInput.value.value = '';
}

// ── Defaults config form ──
const cfgGreeting = ref('');
const cfgFooter = ref('');
const cfgSigner = ref('');

const availableVariables = computed(() => emailStore.defaults?.available_variables || []);
// Built in script: the literal "}}" inside a template interpolation would
// close the interpolation early and break the SFC compiler.
const variablesHint = computed(() =>
  availableVariables.value.map(v => '{' + v + '}').join(', '),
);
const signerOptions = computed(() =>
  (emailStore.defaults?.available_signers || []).map(s => ({
    value: s.key,
    label: `${s.name} — ${s.role}`,
  })),
);

/**
 * Apply a defaults payload: update the composer seeds (only overwriting
 * composer fields the user hasn't touched) and the config form values.
 */
function applyDefaults(data) {
  const prevGreeting = defaultGreeting.value;
  const prevFooter = defaultFooter.value;
  if (data.greeting) defaultGreeting.value = data.greeting;
  if (data.footer) defaultFooter.value = data.footer;
  if (greeting.value === prevGreeting) greeting.value = defaultGreeting.value;
  if (footer.value === prevFooter) footer.value = defaultFooter.value;

  const cfg = data.config || {};
  cfgGreeting.value = cfg.greeting || '';
  cfgFooter.value = cfg.footer || '';
  cfgSigner.value = cfg.signer || '';
}

async function loadDefaults() {
  const result = await emailStore.fetchDefaults();
  if (result.success && result.data) {
    applyDefaults(result.data);
  }
}

async function handleSaveDefaults() {
  const result = await emailStore.saveDefaults({
    greeting: cfgGreeting.value.trim(),
    footer: cfgFooter.value.trim(),
    signer: cfgSigner.value,
  });
  if (result.success && result.data) {
    applyDefaults(result.data);
    notify.success({ title: 'Valores por defecto guardados' });
  } else {
    notify.error({
      title: 'No se pudieron guardar los valores por defecto',
      detail: result.error || 'Intenta de nuevo.',
    });
  }
}

async function handleRestoreDefaults() {
  const originals = emailStore.defaults?.defaults || {};
  cfgGreeting.value = originals.greeting || '';
  cfgFooter.value = originals.footer || '';
  cfgSigner.value = originals.signer || '';
  await handleSaveDefaults();
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

// History metadata stores legacy plain strings and new {text, markdown} dicts.
function sectionText(section) {
  return typeof section === 'string' ? section : (section?.text || '');
}

function sectionIsMarkdown(section) {
  return typeof section === 'object' && !!section?.markdown;
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

function refreshEmails() {
  return Promise.all([loadDefaults(), emailStore.fetchHistory(1)]);
}

onMounted(refreshEmails);
usePanelRefresh(refreshEmails);
</script>
