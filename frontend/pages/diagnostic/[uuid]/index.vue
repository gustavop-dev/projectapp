<template>
  <div
    class="diagnostic-public min-h-screen py-16 px-4"
    data-diagnostic-wrapper
  >
    <DiagnosticIndex
      v-if="sections.length > 1"
      :sections="sections"
      :current-index="activeIndex"
      :visited-ids="visitedIds"
      @navigate="selectSection"
    />

    <div class="max-w-4xl mx-auto">
      <div v-if="store.isLoading" class="text-center text-esmerald/60">Cargando…</div>

      <div v-else-if="store.error === 'not_found'" class="text-center py-16">
        <p class="text-rose-600">Diagnóstico no encontrado.</p>
      </div>

      <template v-else-if="store.current">
        <article
          v-if="sections.length"
          class="diagnostic-card bg-white rounded-3xl shadow-[0_6px_30px_-12px_rgba(0,41,33,0.25)] border border-esmerald/10 p-6 md:p-12 mb-6"
        >
          <component
            :is="componentFor(activeSection.section_type)"
            :content="activeSection.content_json || {}"
            :diagnostic="store.current"
            :render-context="store.current.render_context || {}"
          />
        </article>

        <div
          v-else
          class="diagnostic-card bg-white rounded-3xl shadow-sm border border-esmerald/10 p-6 text-center"
        >
          <p class="text-esmerald font-medium">{{ emptyStateCopy.title }}</p>
          <p class="text-sm text-esmerald/60 mt-2">{{ emptyStateCopy.hint }}</p>
        </div>

        <!-- Prev / next -->
        <div v-if="sections.length > 1" class="flex justify-between items-center mb-8">
          <button
            class="px-4 py-2 text-sm rounded-lg border border-esmerald/20 text-esmerald/80 hover:bg-esmerald/5 disabled:opacity-30"
            :disabled="activeIndex === 0"
            @click="selectSection(activeIndex - 1)"
          >← Anterior</button>
          <span class="text-xs text-esmerald/60">Sección {{ activeIndex + 1 }} de {{ sections.length }}</span>
          <button
            class="px-4 py-2 text-sm rounded-lg border border-esmerald/20 text-esmerald/80 hover:bg-esmerald/5 disabled:opacity-30"
            :disabled="activeIndex === sections.length - 1"
            @click="selectSection(activeIndex + 1)"
          >Siguiente →</button>
        </div>

        <footer
          v-if="canRespond"
          class="diagnostic-card mt-8 bg-white rounded-3xl border border-esmerald/10 p-6 text-center shadow-sm"
        >
          <p class="text-esmerald mb-4">¿Quieres avanzar con el diagnóstico?</p>
          <div class="flex justify-center gap-3 flex-wrap">
            <button
              class="px-6 py-3 bg-esmerald text-lemon rounded-xl hover:bg-esmerald-dark disabled:opacity-50 font-medium"
              :disabled="store.isUpdating"
              @click="respond('accept')"
            >Aceptar propuesta</button>
            <button
              class="px-6 py-3 border border-rose-200 text-rose-600 rounded-xl hover:bg-rose-50 disabled:opacity-50"
              :disabled="store.isUpdating"
              @click="respond('reject')"
            >No por ahora</button>
          </div>
          <p v-if="responseMsg" class="mt-4 text-sm text-esmerald/70">{{ responseMsg }}</p>
        </footer>

        <footer
          v-else-if="store.current.status === DIAGNOSTIC_STATUS.ACCEPTED"
          class="diagnostic-card mt-8 bg-esmerald/5 border border-esmerald/15 rounded-3xl p-6 text-center text-esmerald"
        >
          ¡Gracias! Confirmamos tu aceptación. Te contactaremos para coordinar el inicio.
        </footer>

        <footer
          v-else-if="store.current.status === DIAGNOSTIC_STATUS.REJECTED"
          class="diagnostic-card mt-8 bg-rose-50 border border-rose-200 rounded-3xl p-6 text-center text-rose-800"
        >
          Recibimos tu respuesta. Si cambias de opinión, contáctanos cuando quieras.
        </footer>

        <ShareDiagnosticButton
          v-if="store.current?.uuid"
          :diagnostic-uuid="store.current.uuid"
          :language="store.current.language || 'es'"
        />

        <DownloadDiagnosticPdfButton v-if="store.current?.uuid" />

        <button
          type="button"
          data-testid="diagnostic-theme-toggle"
          class="theme-toggle fixed bottom-6 left-6 z-[9990] w-10 h-10 rounded-full
                 bg-white/90 backdrop-blur-sm shadow-lg border border-esmerald/15
                 flex items-center justify-center text-lg
                 hover:bg-esmerald/5 transition-colors"
          :title="isDark ? 'Modo claro' : 'Modo oscuro'"
          @click="toggleDarkMode"
        >
          <span>{{ isDark ? '☀️' : '🌙' }}</span>
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import { DIAGNOSTIC_STATUS } from '~/stores/diagnostics_constants';
import { useDiagnosticDarkMode } from '~/composables/useDiagnosticDarkMode';

import DiagnosticIndex from '~/components/WebAppDiagnostic/public/DiagnosticIndex.vue';
import PurposeSection from '~/components/WebAppDiagnostic/public/PurposeSection.vue';
import RadiographySection from '~/components/WebAppDiagnostic/public/RadiographySection.vue';
import CategoriesSection from '~/components/WebAppDiagnostic/public/CategoriesSection.vue';
import DeliveryStructureSection from '~/components/WebAppDiagnostic/public/DeliveryStructureSection.vue';
import ExecutiveSummarySection from '~/components/WebAppDiagnostic/public/ExecutiveSummarySection.vue';
import CostSection from '~/components/WebAppDiagnostic/public/CostSection.vue';
import TimelineSection from '~/components/WebAppDiagnostic/public/TimelineSection.vue';
import ScopeSection from '~/components/WebAppDiagnostic/public/ScopeSection.vue';
import ShareDiagnosticButton from '~/components/WebAppDiagnostic/public/ShareDiagnosticButton.vue';
import DownloadDiagnosticPdfButton from '~/components/WebAppDiagnostic/public/DownloadDiagnosticPdfButton.vue';

definePageMeta({ layout: false });

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
const visitedIds = ref(new Set());

// Skip all tracking pings when an admin previews with ?preview=1.
const isPreview = computed(() => route.query?.preview === '1');

const { isDark, toggle: toggleDarkMode } = useDiagnosticDarkMode();

const sections = computed(() => store.current?.sections || []);
const activeSection = computed(() => sections.value[activeIndex.value] || null);

const canRespond = computed(() => (
  store.current?.status === DIAGNOSTIC_STATUS.SENT
  && !!store.current?.final_sent_at
));

const EMPTY_STATE_COPY = {
  [DIAGNOSTIC_STATUS.DRAFT]: {
    title: 'Este diagnóstico todavía no está publicado.',
    hint: 'Nuestro equipo está preparando el contenido. Te avisaremos cuando esté listo para revisar.',
  },
  [DIAGNOSTIC_STATUS.EXPIRED]: {
    title: 'Este diagnóstico ha expirado.',
    hint: 'Si todavía te interesa avanzar, contáctanos y lo reactivamos.',
  },
  [DIAGNOSTIC_STATUS.FINISHED]: {
    title: 'Este diagnóstico ya fue finalizado.',
    hint: 'Si necesitas consultar la información, escríbenos y te ayudamos.',
  },
};
const DEFAULT_EMPTY_STATE = {
  title: 'No hay secciones disponibles en este momento.',
  hint: 'Si crees que es un error, por favor contáctanos.',
};

const emptyStateCopy = computed(
  () => EMPTY_STATE_COPY[store.current?.status] || DEFAULT_EMPTY_STATE,
);

function componentFor(type) {
  return COMPONENTS[type] || null;
}

function markSectionVisited(id) {
  if (id == null) return;
  const next = new Set(visitedIds.value);
  next.add(id);
  visitedIds.value = next;
}

function selectSection(idx) {
  flushSectionTracking();
  activeIndex.value = Math.max(0, Math.min(idx, sections.value.length - 1));
  sectionEnteredAt.value = Date.now();
  markSectionVisited(sections.value[activeIndex.value]?.id);
}

function flushSectionTracking({ beacon = false } = {}) {
  if (isPreview.value) return;
  if (!sessionId.value || !activeSection.value) return;
  const elapsed = (Date.now() - sectionEnteredAt.value) / 1000;
  if (elapsed < 1) return;
  const payload = {
    session_id: sessionId.value,
    section_type: activeSection.value.section_type,
    section_title: activeSection.value.title || '',
    time_spent_seconds: Math.round(elapsed * 10) / 10,
    entered_at: new Date(sectionEnteredAt.value).toISOString(),
  };
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
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return 'sess-' + crypto.randomUUID();
  }
  return 'sess-' + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

onMounted(async () => {
  sessionId.value = generateSessionId();
  await store.fetchPublic(route.params.uuid);
  if (!isPreview.value) {
    await store.trackView(route.params.uuid, sessionId.value);
  }
  sectionEnteredAt.value = Date.now();
  markSectionVisited(sections.value[activeIndex.value]?.id);
});

onBeforeUnmount(() => flushSectionTracking({ beacon: true }));
</script>

<style scoped>
.diagnostic-public {
  background-color: #ffffff;
  background-image:
    radial-gradient(ellipse 80% 60% at 50% 0%, rgba(0, 41, 33, 0.04) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 100%, rgba(0, 41, 33, 0.03) 0%, transparent 55%);
  background-attachment: fixed;
  transition: background-color 0.25s ease;
}

[data-diagnostic-wrapper][data-theme="dark"].diagnostic-public {
  background-color: #0a1f1c;
  background-image:
    radial-gradient(ellipse 80% 60% at 50% 0%, rgba(240, 255, 61, 0.06) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 100%, rgba(16, 185, 129, 0.05) 0%, transparent 50%);
}

[data-diagnostic-wrapper][data-theme="dark"] :deep(.diagnostic-card) {
  background-color: #143d35 !important;
  border-color: rgba(230, 239, 239, 0.1) !important;
  color: #E6EFEF;
}

[data-diagnostic-wrapper][data-theme="dark"] :deep(.text-esmerald) {
  color: #E6EFEF !important;
}
[data-diagnostic-wrapper][data-theme="dark"] :deep(.text-esmerald\/80),
[data-diagnostic-wrapper][data-theme="dark"] :deep(.text-esmerald\/75),
[data-diagnostic-wrapper][data-theme="dark"] :deep(.text-esmerald\/70) {
  color: rgba(230, 239, 239, 0.85) !important;
}
[data-diagnostic-wrapper][data-theme="dark"] :deep(.text-esmerald\/60),
[data-diagnostic-wrapper][data-theme="dark"] :deep(.text-esmerald\/55),
[data-diagnostic-wrapper][data-theme="dark"] :deep(.text-esmerald\/50),
[data-diagnostic-wrapper][data-theme="dark"] :deep(.text-esmerald\/45) {
  color: rgba(230, 239, 239, 0.6) !important;
}
[data-diagnostic-wrapper][data-theme="dark"] :deep(.bg-white) {
  background-color: #143d35 !important;
}
[data-diagnostic-wrapper][data-theme="dark"] :deep(.bg-esmerald\/5) {
  background-color: rgba(230, 239, 239, 0.05) !important;
}
[data-diagnostic-wrapper][data-theme="dark"] :deep(.border-esmerald\/10),
[data-diagnostic-wrapper][data-theme="dark"] :deep(.border-esmerald\/15),
[data-diagnostic-wrapper][data-theme="dark"] :deep(.border-esmerald\/20) {
  border-color: rgba(230, 239, 239, 0.15) !important;
}

.theme-toggle {
  transition: background-color 0.2s ease, transform 0.2s ease;
}
.theme-toggle:hover {
  transform: scale(1.05);
}
[data-diagnostic-wrapper][data-theme="dark"] .theme-toggle {
  background-color: rgba(20, 61, 53, 0.9);
  border-color: rgba(230, 239, 239, 0.15);
  color: #E6EFEF;
}
</style>
