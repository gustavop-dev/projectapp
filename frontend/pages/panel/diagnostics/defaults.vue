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

    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8">
      <div>
        <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100">Valores por Defecto</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Configura los valores iniciales que se aplicarán a los nuevos diagnósticos.
        </p>
      </div>
      <NuxtLink
        :to="localePath('/panel/diagnostics')"
        class="inline-flex items-center gap-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Volver a Diagnósticos
      </NuxtLink>
    </div>

    <ResponsiveTabs v-model="activeTab" :tabs="tabs" />
    <PanelToast />

    <!-- ═══ TAB: Vista General ═══ -->
    <section v-show="activeTab === 'general'" class="max-w-2xl">
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Estos valores se aplican al crear cada nuevo diagnóstico. Puedes seguir ajustándolos por diagnóstico.
      </p>
      <form
        class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 sm:p-8 space-y-6"
        @submit.prevent="handleSaveGeneral"
      >
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Idioma</label>
            <select
              v-model="generalForm.language"
              data-testid="defaults-language"
              class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white dark:bg-gray-700 dark:text-gray-100"
              @change="onLanguageChange"
            >
              <option value="es">Español</option>
              <option value="en">English</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Moneda</label>
            <select
              v-model="generalForm.default_currency"
              data-testid="defaults-currency"
              class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white dark:bg-gray-700 dark:text-gray-100"
            >
              <option value="COP">COP</option>
              <option value="USD">USD</option>
            </select>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Inversión por defecto</label>
            <input
              v-model.number="generalForm.default_investment_amount"
              type="number"
              min="0"
              step="0.01"
              data-testid="defaults-investment"
              class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Duración por defecto</label>
            <input
              v-model="generalForm.default_duration_label"
              type="text"
              maxlength="80"
              placeholder="ej. 4 semanas"
              data-testid="defaults-duration-label"
              class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100"
            />
          </div>
        </div>

        <fieldset class="border border-gray-100 dark:border-gray-700 rounded-xl p-4">
          <legend class="px-2 text-sm font-medium text-gray-700 dark:text-gray-300">Distribución de pagos</legend>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">% Pago inicial</label>
              <div class="flex items-center gap-3">
                <input
                  v-model.number="generalForm.payment_initial_pct"
                  type="number"
                  min="0"
                  max="100"
                  data-testid="defaults-payment-initial"
                  class="w-32 px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100"
                  @input="syncPaymentFinal"
                />
                <span class="text-sm text-gray-500 dark:text-gray-400">%</span>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">% Pago final</label>
              <div class="flex items-center gap-3">
                <input
                  v-model.number="generalForm.payment_final_pct"
                  type="number"
                  min="0"
                  max="100"
                  data-testid="defaults-payment-final"
                  class="w-32 px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100"
                  @input="syncPaymentInitial"
                />
                <span class="text-sm text-gray-500 dark:text-gray-400">%</span>
              </div>
            </div>
          </div>
          <p
            v-if="!isPaymentValid"
            class="text-xs text-rose-600 dark:text-rose-400 mt-2"
            data-testid="defaults-payment-warning"
          >La suma debe ser exactamente 100% (actual: {{ paymentSum }}%).</p>
          <p v-else class="text-xs text-gray-400 dark:text-gray-500 mt-2">Suma: {{ paymentSum }}%.</p>
        </fieldset>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Días de recordatorio</label>
            <input
              v-model.number="generalForm.reminder_days"
              type="number"
              min="1"
              max="60"
              data-testid="defaults-reminder-days"
              class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Días de urgencia</label>
            <input
              v-model.number="generalForm.urgency_reminder_days"
              type="number"
              min="1"
              max="60"
              data-testid="defaults-urgency-days"
              class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Días de expiración</label>
            <input
              v-model.number="generalForm.expiration_days"
              type="number"
              min="1"
              max="365"
              data-testid="defaults-expiration-days"
              class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none dark:bg-gray-700 dark:text-gray-100"
            />
          </div>
        </div>

        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-4 border-t border-gray-100 dark:border-gray-700">
          <button
            type="button"
            class="text-sm text-gray-500 hover:text-rose-600 dark:text-gray-400 dark:hover:text-rose-400"
            data-testid="defaults-reset-btn"
            @click="confirmReset"
          >
            Restablecer a valores del sistema
          </button>
          <button
            type="submit"
            class="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50 dark:bg-emerald-700 dark:hover:bg-emerald-600"
            :disabled="!isPaymentValid || isSaving"
            data-testid="defaults-save-btn"
          >{{ isSaving ? 'Guardando…' : 'Guardar cambios' }}</button>
        </div>
      </form>
    </section>

    <!-- ═══ TAB: Secciones ═══ -->
    <section v-show="activeTab === 'sections'">
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Lista de las secciones que se sembrarán en cada nuevo diagnóstico para el idioma seleccionado.
        Para editar el contenido detallado, abre un diagnóstico real y modifícalo allí — el editor por
        defecto se gestiona desde el JSON de cada sección.
      </p>
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 divide-y divide-gray-100 dark:divide-gray-700">
        <div
          v-for="section in sectionsList"
          :key="section.section_type"
          class="px-4 py-3 flex items-center justify-between gap-3"
          data-testid="defaults-section-row"
        >
          <div>
            <p class="text-sm font-medium text-gray-800 dark:text-gray-100">{{ section.title }}</p>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
              {{ section.section_type }} · orden {{ section.order }} · visibilidad {{ section.visibility }}
            </p>
          </div>
          <span
            class="text-xs px-2 py-1 rounded-full"
            :class="section.is_enabled
              ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
              : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-300'"
          >{{ section.is_enabled ? 'Activa' : 'Desactivada' }}</span>
        </div>
        <div
          v-if="!sectionsList.length"
          class="px-4 py-6 text-sm text-gray-500 dark:text-gray-400 text-center"
        >No hay secciones configuradas.</div>
      </div>
    </section>

    <!-- ═══ TAB: Plantillas de Email ═══ -->
    <section v-show="activeTab === 'emails'" class="max-w-3xl">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-3">
        <h2 class="text-base font-medium text-gray-800 dark:text-gray-100">Plantillas de email del diagnóstico</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Las plantillas <code class="text-xs">diagnostic_initial_sent</code>, <code class="text-xs">diagnostic_final_sent</code>,
          <code class="text-xs">diagnostic_custom_email</code> y <code class="text-xs">diagnostic_documents_sent</code> se
          editan desde el panel central de plantillas de email.
        </p>
        <NuxtLink
          :to="localePath('/panel/email-templates')"
          class="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700 transition-colors"
        >Ir a Plantillas de Email →</NuxtLink>
      </div>
    </section>

    <!-- ═══ TAB: Diagnostic Prompt ═══ -->
    <section v-show="activeTab === 'prompt'" class="max-w-3xl">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-3">
        <h2 class="text-base font-medium text-gray-800 dark:text-gray-100">Diagnostic Prompt (IA)</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          El panel de prompts de IA del diagnóstico se gestiona por diagnóstico desde la pestaña
          “Prompt” del editor. Aquí no hay todavía un prompt por defecto compartido.
        </p>
      </div>
    </section>

    <!-- ═══ TAB: JSON ═══ -->
    <section v-show="activeTab === 'json'" class="max-w-4xl">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-sm text-gray-500 dark:text-gray-400">JSON crudo del config activo</h2>
        <span v-if="rawConfig?.updated_at" class="text-xs text-gray-400">
          Actualizado: {{ formatDate(rawConfig.updated_at) }}
        </span>
      </div>
      <pre
        class="bg-gray-900 text-gray-100 rounded-xl p-4 text-xs overflow-x-auto"
        data-testid="defaults-json-view"
      >{{ rawConfigPretty }}</pre>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import ResponsiveTabs from '~/components/ui/ResponsiveTabs.vue';
import ConfirmModal from '~/components/ui/ConfirmModal.vue';
import PanelToast from '~/components/panel/PanelToast.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { usePanelToast } from '~/composables/usePanelToast';
import { useDiagnosticsStore } from '~/stores/diagnostics';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const localePath = useLocalePath();
const route = useRoute();
const store = useDiagnosticsStore();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();
const { showToast } = usePanelToast();

const tabs = [
  { id: 'general', label: 'Vista General' },
  { id: 'sections', label: 'Secciones' },
  { id: 'emails', label: 'Plantillas de Email' },
  { id: 'prompt', label: 'Prompt' },
  { id: 'json', label: 'JSON' },
];
const activeTab = ref(
  ['general', 'sections', 'emails', 'prompt', 'json'].includes(route.query.tab)
    ? route.query.tab
    : 'general'
);

const generalForm = ref({
  language: 'es',
  default_currency: 'COP',
  default_investment_amount: 0,
  default_duration_label: '',
  payment_initial_pct: 60,
  payment_final_pct: 40,
  reminder_days: 7,
  urgency_reminder_days: 14,
  expiration_days: 21,
});

const sectionsList = ref([]);
const rawConfig = ref(null);
const isSaving = ref(false);

const paymentSum = computed(
  () => Number(generalForm.value.payment_initial_pct || 0)
       + Number(generalForm.value.payment_final_pct || 0)
);
const isPaymentValid = computed(() => paymentSum.value === 100);

const rawConfigPretty = computed(() => {
  if (!rawConfig.value) return '{}';
  try {
    return JSON.stringify(rawConfig.value, null, 2);
  } catch (_) {
    return String(rawConfig.value);
  }
});

function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
}

function applyConfig(data) {
  rawConfig.value = data;
  sectionsList.value = Array.isArray(data.sections_json) ? data.sections_json : [];
  generalForm.value = {
    language: data.language || generalForm.value.language,
    default_currency: data.default_currency || 'COP',
    default_investment_amount: data.default_investment_amount ?? 0,
    default_duration_label: data.default_duration_label || '',
    payment_initial_pct: Number(data.payment_initial_pct ?? 60),
    payment_final_pct: Number(data.payment_final_pct ?? 40),
    reminder_days: Number(data.reminder_days ?? 7),
    urgency_reminder_days: Number(data.urgency_reminder_days ?? 14),
    expiration_days: Number(data.expiration_days ?? 21),
  };
}

function syncPaymentFinal() {
  const initial = Number(generalForm.value.payment_initial_pct || 0);
  if (initial >= 0 && initial <= 100) {
    generalForm.value.payment_final_pct = 100 - initial;
  }
}

function syncPaymentInitial() {
  const final = Number(generalForm.value.payment_final_pct || 0);
  if (final >= 0 && final <= 100) {
    generalForm.value.payment_initial_pct = 100 - final;
  }
}

async function loadDefaults(lang) {
  const result = await store.fetchDiagnosticDefaults(lang);
  if (!result.success) {
    showToast({ type: 'error', text: 'No se pudieron cargar los valores por defecto.' });
    return;
  }
  applyConfig(result.data || {});
}

async function onLanguageChange() {
  await loadDefaults(generalForm.value.language);
}

async function handleSaveGeneral() {
  if (!isPaymentValid.value) {
    showToast({ type: 'error', text: 'La distribución de pagos debe sumar 100%.' });
    return;
  }
  isSaving.value = true;
  try {
    const result = await store.saveDiagnosticDefaults(
      generalForm.value.language,
      sectionsList.value,
      generalForm.value,
    );
    if (result.success) {
      applyConfig(result.data || {});
      showToast({ type: 'success', text: 'Valores guardados correctamente.' });
    } else {
      const detail = result.errors?.detail
        || Object.values(result.errors || {}).flat().join(' ')
        || 'Error al guardar.';
      showToast({ type: 'error', text: detail });
    }
  } finally {
    isSaving.value = false;
  }
}

function confirmReset() {
  requestConfirm({
    title: 'Restablecer valores por defecto',
    message: '¿Eliminar el config personalizado y volver a los valores del sistema (60/40, COP, 21 días)?',
    confirmText: 'Restablecer',
    cancelText: 'Cancelar',
    variant: 'danger',
    onConfirm: async () => {
      const result = await store.resetDiagnosticDefaults(generalForm.value.language);
      if (result.success) {
        await loadDefaults(generalForm.value.language);
        showToast({ type: 'success', text: 'Valores restablecidos.' });
      } else {
        showToast({ type: 'error', text: 'No se pudo restablecer.' });
      }
    },
  });
}

onMounted(() => {
  loadDefaults(generalForm.value.language);
});
</script>
