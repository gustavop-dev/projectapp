<template>
  <div class="min-h-screen bg-gray-50 py-10 px-4">
    <div class="max-w-4xl mx-auto">
      <header class="mb-8 text-center">
        <p class="text-xs font-semibold tracking-widest text-emerald-700 uppercase">Project App</p>
        <h1 class="text-3xl md:text-4xl font-light text-gray-900 mt-2">
          {{ store.current?.title || 'Diagnóstico de Aplicaciones Web' }}
        </h1>
        <p v-if="store.current?.client_name" class="text-sm text-gray-500 mt-2">
          Preparado para {{ store.current.client_name }}
        </p>
      </header>

      <div v-if="store.isLoading" class="text-center text-gray-500">Cargando…</div>

      <div v-else-if="store.error === 'not_found'" class="text-center py-16">
        <p class="text-rose-600">Diagnóstico no encontrado.</p>
      </div>

      <template v-else-if="store.current">
        <!-- Section nav -->
        <nav v-if="sections.length > 1" class="flex flex-wrap justify-center gap-2 mb-6">
          <button
            v-for="(s, i) in sections"
            :key="s.id"
            class="px-4 py-1.5 rounded-full text-xs border"
            :class="activeIndex === i
              ? 'bg-emerald-600 text-white border-emerald-600'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'"
            @click="selectSection(i)"
          >{{ i + 1 }}. {{ s.title }}</button>
        </nav>

        <article
          v-if="sections.length"
          class="bg-white rounded-2xl shadow-sm border p-6 md:p-12 mb-6"
        >
          <component
            :is="componentFor(activeSection.section_type)"
            :content="activeSection.content_json || {}"
            :diagnostic="store.current"
            :render-context="store.current.render_context || {}"
          />
        </article>

        <div v-else class="bg-white rounded-2xl shadow-sm border p-6 text-center text-gray-500">
          No hay secciones disponibles en este momento.
        </div>

        <!-- Prev / next -->
        <div v-if="sections.length > 1" class="flex justify-between items-center mb-8">
          <button
            class="px-4 py-2 text-sm rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 disabled:opacity-30"
            :disabled="activeIndex === 0"
            @click="selectSection(activeIndex - 1)"
          >← Anterior</button>
          <span class="text-xs text-gray-500">Sección {{ activeIndex + 1 }} de {{ sections.length }}</span>
          <button
            class="px-4 py-2 text-sm rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 disabled:opacity-30"
            :disabled="activeIndex === sections.length - 1"
            @click="selectSection(activeIndex + 1)"
          >Siguiente →</button>
        </div>

        <footer
          v-if="canRespond"
          class="mt-8 bg-white rounded-2xl border p-6 text-center"
        >
          <p class="text-gray-700 mb-4">¿Quieres avanzar con el diagnóstico?</p>
          <div class="flex justify-center gap-3">
            <button
              class="px-6 py-3 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 disabled:opacity-50"
              :disabled="store.isUpdating"
              @click="respond('accept')"
            >Aceptar propuesta</button>
            <button
              class="px-6 py-3 border border-rose-300 text-rose-700 rounded-xl hover:bg-rose-50 disabled:opacity-50"
              :disabled="store.isUpdating"
              @click="respond('reject')"
            >No por ahora</button>
          </div>
          <p v-if="responseMsg" class="mt-4 text-sm text-gray-600">{{ responseMsg }}</p>
        </footer>

        <footer
          v-else-if="store.current.status === DIAGNOSTIC_STATUS.ACCEPTED"
          class="mt-8 bg-emerald-50 border border-emerald-200 rounded-2xl p-6 text-center text-emerald-800"
        >
          ¡Gracias! Confirmamos tu aceptación. Te contactaremos para coordinar el inicio.
        </footer>

        <footer
          v-else-if="store.current.status === DIAGNOSTIC_STATUS.REJECTED"
          class="mt-8 bg-rose-50 border border-rose-200 rounded-2xl p-6 text-center text-rose-800"
        >
          Recibimos tu respuesta. Si cambias de opinión, contáctanos cuando quieras.
        </footer>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import { DIAGNOSTIC_STATUS } from '~/stores/diagnostics_constants';

import PurposeSection from '~/components/WebAppDiagnostic/public/PurposeSection.vue';
import RadiographySection from '~/components/WebAppDiagnostic/public/RadiographySection.vue';
import CategoriesSection from '~/components/WebAppDiagnostic/public/CategoriesSection.vue';
import DeliveryStructureSection from '~/components/WebAppDiagnostic/public/DeliveryStructureSection.vue';
import ExecutiveSummarySection from '~/components/WebAppDiagnostic/public/ExecutiveSummarySection.vue';
import CostSection from '~/components/WebAppDiagnostic/public/CostSection.vue';
import TimelineSection from '~/components/WebAppDiagnostic/public/TimelineSection.vue';
import ScopeSection from '~/components/WebAppDiagnostic/public/ScopeSection.vue';

definePageMeta({ layout: 'default' });

const COMPONENTS = {
  purpose: PurposeSection,
  radiography: RadiographySection,
  categories: CategoriesSection,
  delivery_structure: DeliveryStructureSection,
  executive_summary: ExecutiveSummarySection,
  cost: CostSection,
  timeline: TimelineSection,
  scope: ScopeSection,
};

const route = useRoute();
const store = useDiagnosticsStore();
const activeIndex = ref(0);
const responseMsg = ref('');
const sessionId = ref('');
const sectionEnteredAt = ref(0);

const sections = computed(() => store.current?.sections || []);
const activeSection = computed(() => sections.value[activeIndex.value] || null);

const canRespond = computed(() => (
  store.current?.status === DIAGNOSTIC_STATUS.SENT
  && !!store.current?.final_sent_at
));

function componentFor(type) {
  return COMPONENTS[type] || null;
}

function selectSection(idx) {
  flushSectionTracking();
  activeIndex.value = Math.max(0, Math.min(idx, sections.value.length - 1));
  sectionEnteredAt.value = Date.now();
}

function flushSectionTracking({ beacon = false } = {}) {
  if (!sessionId.value || !activeSection.value) return;
  const elapsed = (Date.now() - sectionEnteredAt.value) / 1000;
  if (elapsed < 1) return;
  const payload = {
    session_id: sessionId.value,
    section_type: activeSection.value.section_type,
    section_title: activeSection.value.title || '',
    time_spent_seconds: Math.round(elapsed * 10) / 10,
  };
  // On teardown the normal fetch may be cancelled. sendBeacon survives unload.
  if (beacon && typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
    try {
      const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
      navigator.sendBeacon(
        `/api/diagnostics/public/${route.params.uuid}/track-section/`,
        blob,
      );
      return;
    } catch (_) { /* fall through to fetch */ }
  }
  store.trackSectionView(route.params.uuid, payload);
}

async function respond(decision) {
  responseMsg.value = '';
  const r = await store.respondPublic(route.params.uuid, decision);
  responseMsg.value = r.success
    ? (decision === 'accept' ? 'Tu aceptación quedó registrada.' : 'Tu respuesta quedó registrada.')
    : 'No pudimos registrar tu respuesta. Por favor inténtalo nuevamente.';
}

function generateSessionId() {
  return 'sess-' + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

onMounted(async () => {
  sessionId.value = generateSessionId();
  await store.fetchPublic(route.params.uuid);
  await store.trackView(route.params.uuid, sessionId.value);
  sectionEnteredAt.value = Date.now();
});

onBeforeUnmount(() => flushSectionTracking({ beacon: true }));
</script>
