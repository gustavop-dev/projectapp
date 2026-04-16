<template>
  <div>
    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      @confirm="handleConfirmed"
      @cancel="handleCancelled"
    />

    <div v-if="store.isLoading && !store.current" class="py-16 text-center text-gray-400 dark:text-gray-500 text-sm">
      Cargando…
    </div>

    <div v-else-if="!store.current" class="py-16 text-center text-rose-600 dark:text-rose-400 text-sm">
      No se encontró el diagnóstico.
    </div>

    <template v-else>
      <!-- Sticky header -->
      <div
        class="sticky top-0 z-30 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md
               border-b border-gray-200 dark:border-gray-700
               -mx-4 sm:-mx-8 px-4 sm:px-8 py-3 mb-6"
      >
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="min-w-0 flex-1">
            <NuxtLink
              :to="localePath('/panel/diagnostics')"
              class="inline-flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors mb-1"
            >
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
              Diagnósticos
            </NuxtLink>
            <div class="flex flex-wrap items-center gap-2">
              <h1 class="text-base font-semibold text-gray-900 dark:text-gray-100 truncate">
                {{ store.current.title }}
              </h1>
              <DiagnosticStatusBadge :status="store.current.status" />
              <span class="text-sm text-gray-400 dark:text-gray-500">·</span>
              <span class="text-sm text-gray-500 dark:text-gray-400">{{ store.current.client?.name }}</span>
            </div>
          </div>
          <a
            v-if="store.current.public_url"
            :href="store.current.public_url"
            target="_blank"
            rel="noopener noreferrer"
            class="shrink-0 inline-flex items-center gap-1 text-xs font-medium text-emerald-700 dark:text-emerald-400 hover:underline"
          >
            Vista pública
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        </div>
      </div>

      <!-- Tabs -->
      <ResponsiveTabs :tabs="tabs" v-model="activeTab" />

      <!-- Resumen -->
      <section v-if="activeTab === 'summary'" class="space-y-4">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 flex-1">
              <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">Cliente</div>
              <div class="font-semibold text-gray-800 dark:text-gray-100 text-sm">{{ store.current.client?.name || '—' }}</div>
              <div v-if="store.current.client?.email" class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                {{ store.current.client.email }}
              </div>
              <div v-if="store.current.client?.company" class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                {{ store.current.client.company }}
              </div>
            </div>
            <button type="button" class="shrink-0 text-xs font-medium text-emerald-600 dark:text-emerald-400 hover:underline" @click="toggleClientForm">
              {{ clientForm.open ? 'Cancelar' : 'Cambiar' }}
            </button>
          </div>
          <div v-if="clientForm.open" class="mt-4 space-y-3 pt-4 border-t border-gray-100 dark:border-gray-700">
            <div class="text-xs text-gray-500 dark:text-gray-400">Selecciona el nuevo cliente para este diagnóstico:</div>
            <ClientAutocomplete
              v-model="clientForm.client_id"
              :initial-label="''"
              placeholder="Buscar cliente por nombre, email o empresa…"
              @select="onClientSelected"
            />
            <div v-if="clientForm.selectedClient" class="flex items-center justify-between gap-3">
              <div class="text-xs text-gray-500 dark:text-gray-400">
                Nuevo cliente: <span class="font-medium text-gray-700 dark:text-gray-200">{{ clientForm.selectedClient.name }}</span>
              </div>
              <button type="button" :disabled="store.isUpdating"
                class="px-4 py-1.5 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700 disabled:opacity-50"
                @click="saveClient">{{ store.isUpdating ? 'Guardando…' : 'Guardar cliente' }}</button>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
          <div class="grid sm:grid-cols-2 gap-4 text-sm">
            <div>
              <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">Idioma</div>
              <div class="text-gray-800 dark:text-gray-100">{{ store.current.language === 'es' ? 'Español' : 'English' }}</div>
            </div>
            <div>
              <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">Inversión</div>
              <div class="text-gray-800 dark:text-gray-100">
                <span v-if="store.current.investment_amount">
                  {{ formatMoney(store.current.investment_amount) }} {{ store.current.currency }}
                </span>
                <span v-else class="text-gray-400 dark:text-gray-500 italic">por definir</span>
              </div>
            </div>
            <div>
              <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">Vistas</div>
              <div class="text-gray-800 dark:text-gray-100">
                <span class="font-medium">{{ store.current.view_count }}</span>
                <span v-if="store.current.last_viewed_at" class="text-gray-400 dark:text-gray-500 text-xs ml-1">· última {{ formatDate(store.current.last_viewed_at) }}</span>
                <span v-else class="text-gray-400 dark:text-gray-500 text-xs ml-1">· sin vistas</span>
              </div>
            </div>
            <div>
              <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">Creado</div>
              <div class="text-gray-600 dark:text-gray-400 text-xs">{{ formatDate(store.current.created_at) }}</div>
            </div>
            <div v-if="store.current.initial_sent_at">
              <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">Envío inicial</div>
              <div class="text-gray-600 dark:text-gray-400 text-xs">{{ formatDate(store.current.initial_sent_at) }}</div>
            </div>
            <div v-if="store.current.final_sent_at">
              <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">Envío final</div>
              <div class="text-gray-600 dark:text-gray-400 text-xs">{{ formatDate(store.current.final_sent_at) }}</div>
            </div>
            <div v-if="store.current.responded_at">
              <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">Respondido</div>
              <div class="text-gray-600 dark:text-gray-400 text-xs">{{ formatDate(store.current.responded_at) }}</div>
            </div>
          </div>
        </div>

        <div
          v-if="canSendInitial || canMarkAnalysis || canSendFinal || canDelete"
          class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-5"
        >
          <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-3">Acciones</div>
          <div class="flex flex-wrap gap-2">
            <button v-if="canSendInitial" class="px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-50" :disabled="store.isUpdating" @click="onSendInitial">Enviar envío inicial</button>
            <button v-if="canMarkAnalysis" class="px-4 py-2 bg-amber-600 text-white rounded-xl text-sm font-medium hover:bg-amber-700 disabled:opacity-50" :disabled="store.isUpdating" @click="onMarkAnalysis">Marcar en análisis</button>
            <button v-if="canSendFinal" class="px-4 py-2 bg-purple-600 text-white rounded-xl text-sm font-medium hover:bg-purple-700 disabled:opacity-50" :disabled="store.isUpdating" @click="onSendFinal">Enviar diagnóstico final</button>
            <button v-if="canDelete" class="px-4 py-2 border border-rose-300 text-rose-700 rounded-xl text-sm font-medium hover:bg-rose-50 dark:border-rose-700/60 dark:text-rose-400 dark:hover:bg-rose-500/10 disabled:opacity-50" :disabled="store.isUpdating" @click="onDelete">Eliminar</button>
          </div>
        </div>
      </section>

      <!-- Pricing -->
      <section v-if="activeTab === 'pricing'" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 dark:bg-gray-800 dark:border-gray-700">
        <DiagnosticPricingForm v-model="formPricing" :busy="store.isUpdating" @submit="savePricing" />
      </section>

      <!-- Radiografía -->
      <section v-if="activeTab === 'radiography'" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 dark:bg-gray-800 dark:border-gray-700">
        <DiagnosticRadiographyForm v-model="formRadiography" :busy="store.isUpdating" @submit="saveRadiography" />
      </section>

      <!-- Secciones (JSON-driven content) -->
      <section v-if="activeTab === 'sections'" class="space-y-4">
        <div class="text-xs text-gray-500 dark:text-gray-400">
          Cada tarjeta representa una sección visible para el cliente. Los cambios se guardan
          automáticamente al perder foco.
        </div>
        <DiagnosticSectionEditor
          v-for="section in orderedSections"
          :key="section.id"
          :section="section"
          :is-saving="sectionSavingId === section.id"
          :last-saved-at="sectionLastSaved[section.id]"
          @update:content="(json) => onSectionContentChange(section, json)"
          @update:section="(meta) => onSectionMetaChange(section, meta)"
          @reset="() => onSectionReset(section)"
        />
      </section>

      <!-- Plantillas (JSON raw) -->
      <section v-if="activeTab === 'plantillas'" class="space-y-3">
        <div class="text-xs text-gray-500 dark:text-gray-400">
          Representación JSON de todas las secciones del diagnóstico. Útil para pegar una
          plantilla completa generada con IA.
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div class="flex items-center gap-2 mb-2">
            <button type="button" class="px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700" @click="copyJson">
              {{ jsonCopied ? '¡Copiado!' : 'Copiar JSON' }}
            </button>
            <button
              type="button"
              class="px-3 py-1.5 text-xs font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50"
              :disabled="!jsonDirty || jsonSaving"
              @click="saveJson"
            >
              {{ jsonSaving ? 'Guardando…' : 'Guardar cambios' }}
            </button>
            <span v-if="jsonError" class="text-xs text-rose-500">{{ jsonError }}</span>
          </div>
          <textarea
            v-model="jsonBuffer"
            rows="24"
            class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 rounded-lg text-xs font-mono"
            @input="jsonDirty = true"
          ></textarea>
        </div>
      </section>

      <!-- Prompt -->
      <section v-if="activeTab === 'prompt'">
        <DiagnosticPromptPanel />
      </section>

      <!-- Actividad -->
      <DiagnosticActivityTab
        v-if="activeTab === 'activity'"
        :diagnostic="store.current"
        @log="onLogActivity"
      />

      <!-- Analítica -->
      <DiagnosticAnalytics
        v-if="activeTab === 'analytics'"
        :diagnostic-id="id"
        :loader="() => store.fetchAnalytics(id)"
      />

      <!-- Correos -->
      <DiagnosticEmailsTab v-if="activeTab === 'emails'" :diagnostic="store.current" />

      <!-- Documentos (adjuntos) -->
      <DiagnosticDocumentsTab v-if="activeTab === 'documents'" :diagnostic="store.current" />
    </template>

    <Teleport to="body">
      <Transition name="toast-slide">
        <div
          v-if="actionToast"
          class="fixed bottom-6 right-6 z-[9999] flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-lg text-sm font-medium pointer-events-none"
          :class="actionToast.type === 'success'
            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300 dark:border-emerald-500/20'
            : 'bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-500/10 dark:text-rose-300 dark:border-rose-500/20'"
        >
          <svg v-if="actionToast.type === 'success'" class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <svg v-else class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          {{ actionToast.message }}
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, onUnmounted } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import { DIAGNOSTIC_STATUS } from '~/stores/diagnostics_constants';
import DiagnosticStatusBadge from '~/components/WebAppDiagnostic/DiagnosticStatusBadge.vue';
import DiagnosticPricingForm from '~/components/WebAppDiagnostic/DiagnosticPricingForm.vue';
import DiagnosticRadiographyForm from '~/components/WebAppDiagnostic/DiagnosticRadiographyForm.vue';
import DiagnosticSectionEditor from '~/components/WebAppDiagnostic/admin/DiagnosticSectionEditor.vue';
import DiagnosticPromptPanel from '~/components/WebAppDiagnostic/admin/DiagnosticPromptPanel.vue';
import DiagnosticActivityTab from '~/components/WebAppDiagnostic/admin/DiagnosticActivityTab.vue';
import DiagnosticAnalytics from '~/components/WebAppDiagnostic/admin/DiagnosticAnalytics.vue';
import DiagnosticEmailsTab from '~/components/WebAppDiagnostic/DiagnosticEmailsTab.vue';
import DiagnosticDocumentsTab from '~/components/WebAppDiagnostic/DiagnosticDocumentsTab.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import ResponsiveTabs from '~/components/ui/ResponsiveTabs.vue';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const route = useRoute();
const router = useRouter();
const localePath = useLocalePath();
const store = useDiagnosticsStore();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const moneyFormatter = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });
const dateTimeFormatter = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' });

function formatMoney(amount) {
  const n = Number(amount);
  if (Number.isNaN(n)) return amount;
  return moneyFormatter.format(n);
}
function formatDate(iso) {
  if (!iso) return '';
  return dateTimeFormatter.format(new Date(iso));
}

const id = computed(() => Number(route.params.id));
const status = computed(() => store.current?.status);
const finalSentAt = computed(() => store.current?.final_sent_at);

const canSendInitial = computed(() => status.value === DIAGNOSTIC_STATUS.DRAFT);
const canMarkAnalysis = computed(() => status.value === DIAGNOSTIC_STATUS.SENT && !finalSentAt.value);
const canSendFinal = computed(() => status.value === DIAGNOSTIC_STATUS.NEGOTIATING);
const canDelete = computed(() => {
  const terminal = [DIAGNOSTIC_STATUS.ACCEPTED, DIAGNOSTIC_STATUS.REJECTED, DIAGNOSTIC_STATUS.FINISHED];
  return !terminal.includes(status.value);
});

const tabs = [
  { id: 'summary', label: 'Resumen' },
  { id: 'pricing', label: 'Pricing' },
  { id: 'radiography', label: 'Radiografía' },
  { id: 'sections', label: 'Secciones' },
  { id: 'plantillas', label: 'Plantillas' },
  { id: 'prompt', label: 'Prompt' },
  { id: 'activity', label: 'Actividad' },
  { id: 'analytics', label: 'Analítica' },
  { id: 'emails', label: 'Correos' },
  { id: 'documents', label: 'Documentos' },
];
const tabIds = tabs.map((t) => t.id);
const activeTab = ref(tabIds.includes(route.query.tab) ? route.query.tab : 'summary');

watch(activeTab, (tab) => {
  if (route.query.tab !== tab) {
    router.replace({ query: { ...route.query, tab } });
  }
});

// ── Client edit ────────────────────────────────────────────────────────
const clientForm = reactive({ client_id: null, selectedClient: null, open: false });

function toggleClientForm() {
  clientForm.open = !clientForm.open;
  if (!clientForm.open) {
    clientForm.client_id = null;
    clientForm.selectedClient = null;
  }
}
function onClientSelected(client) {
  clientForm.client_id = client?.id || null;
  clientForm.selectedClient = client || null;
}
async function saveClient() {
  if (!clientForm.client_id) return;
  const result = await store.update(id.value, { client_id: clientForm.client_id });
  if (result.success) {
    clientForm.open = false;
    clientForm.client_id = null;
    clientForm.selectedClient = null;
    showToast('Cliente actualizado.', 'success');
  } else {
    showToast(result.error || 'Error al actualizar el cliente.', 'error');
  }
}

// ── Pricing/Radiography forms ─────────────────────────────────────────
const formPricing = ref({
  investment_amount: '',
  currency: 'COP',
  payment_terms: { initial_pct: 40, final_pct: 60 },
  duration_label: '',
});
const formRadiography = ref({ size_category: '', radiography: {} });

const actionToast = ref(null);
let toastTimer = null;

function showToast(message, type) {
  if (toastTimer) clearTimeout(toastTimer);
  actionToast.value = { message, type };
  toastTimer = setTimeout(() => { actionToast.value = null; }, 3500);
}

function syncForms() {
  if (!store.current) return;
  formPricing.value = {
    investment_amount: store.current.investment_amount || '',
    currency: store.current.currency || 'COP',
    payment_terms: { ...(store.current.payment_terms || { initial_pct: 40, final_pct: 60 }) },
    duration_label: store.current.duration_label || '',
  };
  formRadiography.value = {
    size_category: store.current.size_category || '',
    radiography: { ...(store.current.radiography || {}) },
  };
  resyncJsonBuffer();
}

watch(() => store.current?.id, syncForms, { immediate: true });

async function savePricing() {
  const result = await store.update(id.value, formPricing.value);
  showToast(result.success ? 'Pricing guardado.' : (result.error || 'Error al guardar.'), result.success ? 'success' : 'error');
}
async function saveRadiography() {
  const result = await store.update(id.value, formRadiography.value);
  showToast(result.success ? 'Radiografía guardada.' : (result.error || 'Error al guardar.'), result.success ? 'success' : 'error');
}

// ── Sections tab ──────────────────────────────────────────────────────
const orderedSections = computed(() => {
  const list = store.current?.sections || [];
  return [...list].sort((a, b) => a.order - b.order);
});

const sectionSavingId = ref(null);
const sectionLastSaved = reactive({});
const sectionTimers = new Map();

function scheduleSectionUpdate(sectionId, payload, delay = 600) {
  const existing = sectionTimers.get(sectionId);
  if (existing) clearTimeout(existing);
  sectionTimers.set(sectionId, setTimeout(async () => {
    sectionTimers.delete(sectionId);
    sectionSavingId.value = sectionId;
    try {
      const res = await store.updateSection(id.value, sectionId, payload);
      if (res.success) {
        sectionLastSaved[sectionId] = new Date().toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
        resyncJsonBuffer();
      } else {
        showToast(res.error || 'Error al guardar la sección.', 'error');
      }
    } finally {
      sectionSavingId.value = null;
    }
  }, delay));
}

function onSectionContentChange(section, contentJson) {
  scheduleSectionUpdate(section.id, { content_json: contentJson });
}
function onSectionMetaChange(section, meta) {
  scheduleSectionUpdate(section.id, meta, 300);
}
async function onSectionReset(section) {
  requestConfirm({
    title: 'Restaurar sección',
    message: `¿Restaurar «${section.title}» al contenido por defecto? Se perderán las ediciones actuales.`,
    variant: 'warning',
    confirmText: 'Restaurar',
    onConfirm: async () => {
      const r = await store.resetSection(id.value, section.id);
      showToast(r?.success ? 'Sección restaurada.' : (r?.error || 'Error.'), r?.success ? 'success' : 'error');
      resyncJsonBuffer();
    },
  });
}

onBeforeUnmount(() => {
  sectionTimers.forEach((t) => clearTimeout(t));
  sectionTimers.clear();
});

// ── Plantillas (raw JSON) ─────────────────────────────────────────────
const jsonBuffer = ref('[]');
const jsonDirty = ref(false);
const jsonSaving = ref(false);
const jsonError = ref('');
const jsonCopied = ref(false);

function resyncJsonBuffer() {
  // Don't clobber an unsaved JSON edit the user is typing into; the textarea
  // will pick up the latest server state next time they resync manually.
  if (activeTab.value === 'plantillas' && jsonDirty.value) return;
  jsonBuffer.value = JSON.stringify(orderedSections.value, null, 2);
  jsonDirty.value = false;
  jsonError.value = '';
}

async function copyJson() {
  try {
    await navigator.clipboard.writeText(jsonBuffer.value);
    jsonCopied.value = true;
    setTimeout(() => { jsonCopied.value = false; }, 1500);
  } catch (_) { /* ignore */ }
}

async function saveJson() {
  jsonError.value = '';
  let parsed;
  try {
    parsed = JSON.parse(jsonBuffer.value);
  } catch (err) {
    jsonError.value = `JSON inválido: ${err.message}`;
    return;
  }
  if (!Array.isArray(parsed)) {
    jsonError.value = 'El JSON raíz debe ser un array de secciones.';
    return;
  }
  jsonSaving.value = true;
  try {
    const payload = parsed.map((s) => ({
      id: s.id,
      title: s.title,
      order: s.order,
      is_enabled: s.is_enabled,
      visibility: s.visibility,
      content_json: s.content_json,
    }));
    const r = await store.bulkUpdateSections(id.value, payload);
    if (r.success) {
      showToast('Secciones actualizadas.', 'success');
      resyncJsonBuffer();
    } else {
      jsonError.value = r.error || 'Error al guardar.';
    }
  } finally {
    jsonSaving.value = false;
  }
}

// ── Activity ──────────────────────────────────────────────────────────
async function onLogActivity(payload) {
  const r = await store.logActivity(id.value, payload.change_type, payload.description);
  showToast(r.success ? 'Actividad registrada.' : (r.error || 'Error al registrar.'), r.success ? 'success' : 'error');
}

// ── Transitions ───────────────────────────────────────────────────────
function onSendInitial() {
  requestConfirm({
    title: 'Enviar envío inicial',
    message: '¿Enviar el envío inicial al cliente por email y marcar el diagnóstico como «Enviado»?',
    variant: 'info',
    confirmText: 'Enviar',
    onConfirm: async () => {
      const r = await store.sendInitial(id.value);
      showToast(r.success ? 'Envío inicial entregado.' : (r.message || r.error || 'Error al enviar.'), r.success ? 'success' : 'error');
      if (r.success) resyncJsonBuffer();
    },
  });
}

function onMarkAnalysis() {
  requestConfirm({
    title: 'Marcar en análisis',
    message: '¿Confirmar que el cliente autorizó? Se moverá a «En negociación».',
    variant: 'warning',
    confirmText: 'Confirmar',
    onConfirm: async () => {
      const r = await store.markInAnalysis(id.value);
      showToast(r.success ? 'Diagnóstico en negociación.' : (r.message || r.error || 'Error.'), r.success ? 'success' : 'error');
    },
  });
}

function onSendFinal() {
  requestConfirm({
    title: 'Enviar diagnóstico final',
    message: '¿Enviar el diagnóstico final al cliente?',
    variant: 'info',
    confirmText: 'Enviar',
    onConfirm: async () => {
      const r = await store.sendFinal(id.value);
      showToast(r.success ? 'Diagnóstico final enviado.' : (r.message || r.error || 'Error al enviar.'), r.success ? 'success' : 'error');
      if (r.success) resyncJsonBuffer();
    },
  });
}

function onDelete() {
  requestConfirm({
    title: 'Eliminar diagnóstico',
    message: '¿Eliminar este diagnóstico? Esta acción no se puede deshacer.',
    variant: 'danger',
    confirmText: 'Eliminar',
    onConfirm: async () => {
      const r = await store.remove(id.value);
      if (r?.success) {
        router.push(localePath('/panel/diagnostics'));
      } else {
        showToast(r?.error || 'Error al eliminar.', 'error');
      }
    },
  });
}

onMounted(() => store.fetchDetail(id.value));
onUnmounted(() => { if (toastTimer) clearTimeout(toastTimer); });
</script>

<style scoped>
.toast-slide-enter-active, .toast-slide-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.toast-slide-enter-from, .toast-slide-leave-to { opacity: 0; transform: translateY(8px); }
</style>
