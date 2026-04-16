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

    <div v-if="store.isLoading && !store.current" class="text-gray-500 dark:text-gray-400">Cargando…</div>

    <div v-else-if="!store.current" class="text-rose-600 dark:text-rose-400">No se encontró el diagnóstico.</div>

    <div v-else class="space-y-6">
      <header class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <NuxtLink
            :to="localePath('/panel/diagnostics')"
            class="text-sm text-gray-500 dark:text-gray-400 hover:underline"
          >← Diagnósticos</NuxtLink>
          <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100 mt-1">{{ store.current.title }}</h1>
          <div class="flex items-center gap-2 mt-1">
            <DiagnosticStatusBadge :status="store.current.status" />
            <span class="text-sm text-gray-500 dark:text-gray-400">{{ store.current.client?.name }}</span>
          </div>
        </div>
        <a
          v-if="store.current.public_url"
          :href="store.current.public_url"
          target="_blank"
          rel="noopener noreferrer"
          class="text-sm text-emerald-700 dark:text-emerald-400 hover:underline"
        >Ver vista pública ↗</a>
      </header>

      <nav class="border-b border-gray-200 dark:border-gray-700 flex gap-6 text-sm">
        <button
          v-for="t in tabs"
          :key="t.id"
          class="px-1 pb-3 -mb-px text-sm font-medium border-b-2 transition-colors"
          :class="activeTab === t.id
            ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400'
            : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'"
          @click="activeTab = t.id"
        >{{ t.label }}</button>
      </nav>

      <!-- Resumen -->
      <section
        v-if="activeTab === 'summary'"
        class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4
               dark:bg-gray-800 dark:border-gray-700"
      >
        <div class="grid md:grid-cols-2 gap-4 text-sm">
          <div>
            <div class="text-gray-500 dark:text-gray-400">Cliente</div>
            <div class="font-medium text-gray-800 dark:text-gray-100">{{ store.current.client?.name }}</div>
            <div class="text-gray-500 dark:text-gray-400 text-xs">{{ store.current.client?.email }}</div>
          </div>
          <div>
            <div class="text-gray-500 dark:text-gray-400">Idioma</div>
            <div class="text-gray-800 dark:text-gray-100">{{ store.current.language === 'es' ? 'Español' : 'English' }}</div>
          </div>
          <div>
            <div class="text-gray-500 dark:text-gray-400">Inversión</div>
            <div class="text-gray-800 dark:text-gray-100">
              <span v-if="store.current.investment_amount">
                {{ Intl.NumberFormat('es-CO').format(Number(store.current.investment_amount)) }} {{ store.current.currency }}
              </span>
              <span v-else class="text-gray-400 dark:text-gray-500">— por definir</span>
            </div>
          </div>
          <div>
            <div class="text-gray-500 dark:text-gray-400">Vistas</div>
            <div class="text-gray-800 dark:text-gray-100">
              {{ store.current.view_count }} · última {{ store.current.last_viewed_at || '—' }}
            </div>
          </div>
        </div>

        <div class="border-t border-gray-100 dark:border-gray-700 pt-4 flex flex-wrap gap-2">
          <button
            v-if="canSendInitial"
            class="px-4 py-2 bg-blue-600 text-white rounded-xl shadow-sm text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
            :disabled="store.isUpdating"
            @click="onSendInitial"
          >Enviar Doc 1 al cliente</button>
          <button
            v-if="canMarkAnalysis"
            class="px-4 py-2 bg-amber-600 text-white rounded-xl shadow-sm text-sm font-medium hover:bg-amber-700 transition-colors disabled:opacity-50"
            :disabled="store.isUpdating"
            @click="onMarkAnalysis"
          >Marcar en análisis</button>
          <button
            v-if="canSendFinal"
            class="px-4 py-2 bg-purple-600 text-white rounded-xl shadow-sm text-sm font-medium hover:bg-purple-700 transition-colors disabled:opacity-50"
            :disabled="store.isUpdating"
            @click="onSendFinal"
          >Enviar diagnóstico final</button>
          <button
            v-if="canDelete"
            class="px-4 py-2 border border-rose-300 text-rose-700 rounded-xl text-sm font-medium hover:bg-rose-50 transition-colors disabled:opacity-50
                   dark:border-rose-700/60 dark:text-rose-400 dark:hover:bg-rose-500/10"
            :disabled="store.isUpdating"
            @click="onDelete"
          >Eliminar</button>
        </div>
      </section>

      <!-- Pricing -->
      <section
        v-if="activeTab === 'pricing'"
        class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6
               dark:bg-gray-800 dark:border-gray-700"
      >
        <DiagnosticPricingForm
          v-model="formPricing"
          :busy="store.isUpdating"
          @submit="savePricing"
        />
      </section>

      <!-- Radiografía -->
      <section
        v-if="activeTab === 'radiography'"
        class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6
               dark:bg-gray-800 dark:border-gray-700"
      >
        <DiagnosticRadiographyForm
          v-model="formRadiography"
          :busy="store.isUpdating"
          @submit="saveRadiography"
        />
      </section>

      <!-- Plantillas (editores markdown) -->
      <section v-if="activeTab === 'templates'" class="space-y-6">
        <DiagnosticDocumentEditor
          v-for="doc in store.visibleDocuments"
          :key="doc.id"
          :doc="doc"
          @update:content="(v) => onDocContent(doc, v)"
          @toggle-ready="(v) => onDocReady(doc, v)"
          @restore="() => onDocRestore(doc)"
        />
      </section>

      <!-- Correos -->
      <DiagnosticEmailsTab
        v-if="activeTab === 'emails'"
        :diagnostic="store.current"
      />

      <!-- Documentos (adjuntos) -->
      <DiagnosticDocumentsTab
        v-if="activeTab === 'documents'"
        :diagnostic="store.current"
      />
    </div>

    <!-- Action toast -->
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
import { ref, computed, watch, onMounted, onBeforeUnmount, onUnmounted } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import { DIAGNOSTIC_STATUS } from '~/stores/diagnostics_constants';
import DiagnosticStatusBadge from '~/components/WebAppDiagnostic/DiagnosticStatusBadge.vue';
import DiagnosticPricingForm from '~/components/WebAppDiagnostic/DiagnosticPricingForm.vue';
import DiagnosticRadiographyForm from '~/components/WebAppDiagnostic/DiagnosticRadiographyForm.vue';
import DiagnosticDocumentEditor from '~/components/WebAppDiagnostic/DiagnosticDocumentEditor.vue';
import DiagnosticEmailsTab from '~/components/WebAppDiagnostic/DiagnosticEmailsTab.vue';
import DiagnosticDocumentsTab from '~/components/WebAppDiagnostic/DiagnosticDocumentsTab.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const route = useRoute();
const router = useRouter();
const localePath = useLocalePath();
const store = useDiagnosticsStore();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const id = computed(() => Number(route.params.id));
const status = computed(() => store.current?.status);
const finalSentAt = computed(() => store.current?.final_sent_at);

const canSendInitial = computed(
  () => status.value === DIAGNOSTIC_STATUS.DRAFT,
);
const canMarkAnalysis = computed(
  () => status.value === DIAGNOSTIC_STATUS.SENT && !finalSentAt.value,
);
const canSendFinal = computed(
  () => status.value === DIAGNOSTIC_STATUS.NEGOTIATING,
);
const canDelete = computed(() => {
  const terminal = [
    DIAGNOSTIC_STATUS.ACCEPTED,
    DIAGNOSTIC_STATUS.REJECTED,
    DIAGNOSTIC_STATUS.FINISHED,
  ];
  return !terminal.includes(status.value);
});
const activeTab = ref('summary');
const tabs = [
  { id: 'summary', label: 'Resumen' },
  { id: 'pricing', label: 'Pricing' },
  { id: 'radiography', label: 'Radiografía' },
  { id: 'templates', label: 'Plantillas' },
  { id: 'emails', label: 'Correos' },
  { id: 'documents', label: 'Documentos' },
];

const formPricing = ref({
  investment_amount: '',
  currency: 'COP',
  payment_terms: { initial_pct: 40, final_pct: 60 },
  duration_label: '',
});

const formRadiography = ref({
  size_category: '',
  radiography: {},
});

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
}

watch(() => store.current?.id, syncForms, { immediate: true });

async function savePricing() {
  const result = await store.update(id.value, formPricing.value);
  showToast(
    result.success ? 'Pricing guardado.' : (result.error || 'Error al guardar.'),
    result.success ? 'success' : 'error',
  );
}

async function saveRadiography() {
  const result = await store.update(id.value, formRadiography.value);
  showToast(
    result.success ? 'Radiografía guardada.' : (result.error || 'Error al guardar.'),
    result.success ? 'success' : 'error',
  );
}

const docTimers = new Map();
function onDocContent(doc, content) {
  const existing = docTimers.get(doc.id);
  if (existing) clearTimeout(existing);
  docTimers.set(
    doc.id,
    setTimeout(() => {
      docTimers.delete(doc.id);
      store.updateDocument(id.value, doc.id, { content_md: content });
    }, 600),
  );
}
onBeforeUnmount(() => {
  docTimers.forEach((t) => clearTimeout(t));
  docTimers.clear();
});
async function onDocReady(doc, ready) {
  await store.updateDocument(id.value, doc.id, { is_ready: ready });
}
function onDocRestore(doc) {
  requestConfirm({
    title: 'Restaurar documento',
    message: `¿Restaurar "${doc.title}" desde el template original? Se perderán los cambios actuales.`,
    variant: 'warning',
    confirmText: 'Restaurar',
    onConfirm: async () => {
      const r = await store.restoreDocument(id.value, doc.id);
      showToast(
        r?.success ? 'Documento restaurado.' : (r?.error || 'Error al restaurar.'),
        r?.success ? 'success' : 'error',
      );
    },
  });
}

function onSendInitial() {
  requestConfirm({
    title: 'Enviar Doc 1',
    message: '¿Enviar Doc 1 al cliente por email y mover el diagnóstico a "Enviada"?',
    variant: 'info',
    confirmText: 'Enviar',
    onConfirm: async () => {
      const r = await store.sendInitial(id.value);
      showToast(
        r.success ? 'Doc 1 enviado.' : (r.message || r.error || 'Error al enviar.'),
        r.success ? 'success' : 'error',
      );
    },
  });
}

function onMarkAnalysis() {
  requestConfirm({
    title: 'Marcar en análisis',
    message: '¿Confirmar que el cliente autorizó? Se moverá a "En negociación".',
    variant: 'warning',
    confirmText: 'Confirmar',
    onConfirm: async () => {
      const r = await store.markInAnalysis(id.value);
      showToast(
        r.success ? 'Diagnóstico en negociación.' : (r.message || r.error || 'Error.'),
        r.success ? 'success' : 'error',
      );
    },
  });
}

function onSendFinal() {
  requestConfirm({
    title: 'Enviar diagnóstico final',
    message: '¿Enviar el diagnóstico final (3 documentos) al cliente?',
    variant: 'info',
    confirmText: 'Enviar',
    onConfirm: async () => {
      const r = await store.sendFinal(id.value);
      showToast(
        r.success ? 'Diagnóstico final enviado.' : (r.message || r.error || 'Error al enviar.'),
        r.success ? 'success' : 'error',
      );
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
onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer);
});
</script>

<style scoped>
.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.toast-slide-enter-from,
.toast-slide-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
