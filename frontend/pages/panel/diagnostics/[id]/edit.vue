<template>
  <div v-if="store.isLoading && !store.current" class="text-gray-500">Cargando…</div>

  <div v-else-if="!store.current" class="text-rose-600">No se encontró el diagnóstico.</div>

  <div v-else class="space-y-6">
    <header class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <NuxtLink :to="localePath('/panel/diagnostics')" class="text-sm text-gray-500 hover:underline">
          ← Diagnósticos
        </NuxtLink>
        <h1 class="text-2xl font-light text-gray-900 mt-1">{{ store.current.title }}</h1>
        <div class="flex items-center gap-2 mt-1">
          <DiagnosticStatusBadge :status="store.current.status" />
          <span class="text-sm text-gray-500">{{ store.current.client?.name }}</span>
        </div>
      </div>
      <a
        :href="store.current.public_url"
        target="_blank"
        class="text-sm text-emerald-700 hover:underline"
      >Ver vista pública ↗</a>
    </header>

    <nav class="border-b flex gap-6 text-sm">
      <button
        v-for="t in tabs"
        :key="t.id"
        class="py-2 border-b-2 -mb-px"
        :class="activeTab === t.id ? 'border-emerald-600 text-emerald-700' : 'border-transparent text-gray-500 hover:text-gray-700'"
        @click="activeTab = t.id"
      >{{ t.label }}</button>
    </nav>

    <!-- Resumen -->
    <section v-if="activeTab === 'summary'" class="bg-white rounded-xl border p-6 space-y-4">
      <div class="grid md:grid-cols-2 gap-4 text-sm">
        <div>
          <div class="text-gray-500">Cliente</div>
          <div class="font-medium">{{ store.current.client?.name }}</div>
          <div class="text-gray-500 text-xs">{{ store.current.client?.email }}</div>
        </div>
        <div>
          <div class="text-gray-500">Idioma</div>
          <div>{{ store.current.language === 'es' ? 'Español' : 'English' }}</div>
        </div>
        <div>
          <div class="text-gray-500">Inversión</div>
          <div>
            <span v-if="store.current.investment_amount">
              {{ Intl.NumberFormat('es-CO').format(Number(store.current.investment_amount)) }} {{ store.current.currency }}
            </span>
            <span v-else class="text-gray-400">— por definir</span>
          </div>
        </div>
        <div>
          <div class="text-gray-500">Vistas</div>
          <div>{{ store.current.view_count }} · última {{ store.current.last_viewed_at || '—' }}</div>
        </div>
      </div>

      <div class="border-t pt-4 flex flex-wrap gap-2">
        <button
          v-if="status === DIAGNOSTIC_STATUS.DRAFT"
          class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          :disabled="store.isUpdating"
          @click="onSendInitial"
        >Enviar Doc 1 al cliente</button>
        <button
          v-if="status === DIAGNOSTIC_STATUS.INITIAL_SENT"
          class="px-4 py-2 bg-amber-600 text-white rounded hover:bg-amber-700"
          :disabled="store.isUpdating"
          @click="onMarkAnalysis"
        >Marcar en análisis</button>
        <button
          v-if="status === DIAGNOSTIC_STATUS.IN_ANALYSIS"
          class="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
          :disabled="store.isUpdating"
          @click="onSendFinal"
        >Enviar diagnóstico final</button>
        <button
          v-if="status !== DIAGNOSTIC_STATUS.ACCEPTED && status !== DIAGNOSTIC_STATUS.REJECTED"
          class="px-4 py-2 border border-rose-300 text-rose-700 rounded hover:bg-rose-50"
          :disabled="store.isUpdating"
          @click="onDelete"
        >Eliminar</button>
      </div>
      <p v-if="actionMsg" class="text-sm" :class="actionMsgOk ? 'text-emerald-700' : 'text-rose-600'">
        {{ actionMsg }}
      </p>
    </section>

    <!-- Pricing -->
    <section v-if="activeTab === 'pricing'" class="bg-white rounded-xl border p-6">
      <DiagnosticPricingForm
        v-model="formPricing"
        :busy="store.isUpdating"
        @submit="savePricing"
      />
    </section>

    <!-- Radiografía -->
    <section v-if="activeTab === 'radiography'" class="bg-white rounded-xl border p-6">
      <DiagnosticRadiographyForm
        v-model="formRadiography"
        :busy="store.isUpdating"
        @submit="saveRadiography"
      />
    </section>

    <!-- Documentos -->
    <section v-if="activeTab === 'documents'" class="space-y-6">
      <DiagnosticDocumentEditor
        v-for="doc in store.visibleDocuments"
        :key="doc.id"
        :doc="doc"
        @update:content="(v) => onDocContent(doc, v)"
        @toggle-ready="(v) => onDocReady(doc, v)"
        @restore="() => onDocRestore(doc)"
      />
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import { DIAGNOSTIC_STATUS } from '~/stores/diagnostics_constants';
import DiagnosticStatusBadge from '~/components/WebAppDiagnostic/DiagnosticStatusBadge.vue';
import DiagnosticPricingForm from '~/components/WebAppDiagnostic/DiagnosticPricingForm.vue';
import DiagnosticRadiographyForm from '~/components/WebAppDiagnostic/DiagnosticRadiographyForm.vue';
import DiagnosticDocumentEditor from '~/components/WebAppDiagnostic/DiagnosticDocumentEditor.vue';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const route = useRoute();
const router = useRouter();
const localePath = useLocalePath();
const store = useDiagnosticsStore();

const id = computed(() => Number(route.params.id));
const status = computed(() => store.current?.status);
const activeTab = ref('summary');
const tabs = [
  { id: 'summary', label: 'Resumen' },
  { id: 'pricing', label: 'Pricing' },
  { id: 'radiography', label: 'Radiografía' },
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

const actionMsg = ref('');
const actionMsgOk = ref(true);

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
  actionMsg.value = '';
  const result = await store.update(id.value, formPricing.value);
  actionMsgOk.value = result.success;
  actionMsg.value = result.success ? 'Pricing guardado.' : (result.error || 'Error al guardar.');
}

async function saveRadiography() {
  actionMsg.value = '';
  const result = await store.update(id.value, formRadiography.value);
  actionMsgOk.value = result.success;
  actionMsg.value = result.success ? 'Radiografía guardada.' : (result.error || 'Error al guardar.');
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
async function onDocRestore(doc) {
  if (!confirm(`¿Restaurar "${doc.title}" desde el template original? Se perderán los cambios actuales.`)) return;
  await store.restoreDocument(id.value, doc.id);
}

async function onSendInitial() {
  if (!confirm('Enviar Doc 1 al cliente por email y mover el diagnóstico a "Inicial enviada"?')) return;
  const r = await store.sendInitial(id.value);
  actionMsgOk.value = r.success;
  actionMsg.value = r.success ? 'Doc 1 enviado.' : (r.message || r.error);
}
async function onMarkAnalysis() {
  if (!confirm('¿Confirmar que el cliente autorizó? Se moverá a "En análisis".')) return;
  const r = await store.markInAnalysis(id.value);
  actionMsgOk.value = r.success;
  actionMsg.value = r.success ? 'Diagnóstico en análisis.' : (r.message || r.error);
}
async function onSendFinal() {
  if (!confirm('Enviar el diagnóstico final (3 documentos) al cliente?')) return;
  const r = await store.sendFinal(id.value);
  actionMsgOk.value = r.success;
  actionMsg.value = r.success ? 'Diagnóstico final enviado.' : (r.message || r.error);
}

async function onDelete() {
  if (!confirm('Eliminar este diagnóstico? Esta acción no se puede deshacer.')) return;
  const r = await store.remove(id.value);
  if (r.success) router.push(localePath('/panel/diagnostics'));
}

onMounted(() => store.fetchDetail(id.value));
</script>
