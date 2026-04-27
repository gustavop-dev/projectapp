<template>
  <div
    class="diagnostic-public min-h-screen py-16 px-4"
    :class="{ dark: isDark }"
  >
    <DiagnosticIndex
      v-if="sections.length > 1"
      :sections="sections"
      :current-index="activeIndex"
      :visited-ids="visitedIds"
      @navigate="selectSection"
    />

    <div class="max-w-4xl mx-auto">
      <div v-if="store.isLoading" class="text-center text-text-brand/60 dark:text-text-brand/60">Cargando…</div>

      <div v-else-if="store.error === 'not_found'" class="text-center py-16">
        <p class="text-rose-600 dark:text-rose-300">Diagnóstico no encontrado.</p>
      </div>

      <template v-else-if="store.current">
        <article
          v-if="sections.length"
          class="diagnostic-card bg-surface rounded-3xl shadow-[0_6px_30px_-12px_rgba(0,41,33,0.25)] dark:shadow-[0_6px_30px_-12px_rgba(0,0,0,0.5)] border border-input-border/10 dark:border-input-border/15 p-6 md:p-12 mb-6 text-text-default"
        >
          <component
            :is="componentFor(activeSection.section_type)"
            :content="activeContent"
            :diagnostic="store.current"
            :render-context="store.current.render_context || {}"
          />
        </article>

        <div
          v-else
          class="diagnostic-card bg-surface rounded-3xl shadow-sm border border-input-border/10 dark:border-input-border/15 p-6 text-center"
        >
          <p class="text-text-default font-medium">{{ emptyStateCopy.title }}</p>
          <p class="text-sm text-text-brand/60 dark:text-text-brand/60 mt-2">{{ emptyStateCopy.hint }}</p>
        </div>

        <!-- Prev / next -->
        <div v-if="sections.length > 1" class="section-nav flex justify-between items-center mb-8">
          <button
            class="px-4 py-2 text-sm rounded-lg border border-input-border/20 dark:border-input-border/20 text-text-brand/80 dark:text-text-brand/80 hover:bg-primary/5 dark:hover:bg-primary-soft/10 disabled:opacity-30"
            :disabled="activeIndex === 0"
            @click="selectSection(activeIndex - 1)"
          >← Anterior</button>
          <span class="section-counter text-xs text-text-brand/60 dark:text-text-brand/60">Sección {{ activeIndex + 1 }} de {{ sections.length }}</span>
          <button
            class="px-4 py-2 text-sm rounded-lg border border-input-border/20 dark:border-input-border/20 text-text-brand/80 dark:text-text-brand/80 hover:bg-primary/5 dark:hover:bg-primary-soft/10 disabled:opacity-30"
            :disabled="activeIndex === sections.length - 1"
            @click="selectSection(activeIndex + 1)"
          >Siguiente →</button>
        </div>

        <footer
          v-if="canRespond"
          class="diagnostic-card diagnostic-cta mt-8 bg-surface rounded-3xl border border-input-border/10 dark:border-input-border/15 p-6 text-center shadow-sm"
        >
          <p class="text-text-default mb-4">¿Quieres avanzar con el diagnóstico?</p>
          <div class="flex justify-center gap-3 flex-wrap">
            <button
              class="px-6 py-3 bg-primary dark:bg-accent text-accent dark:text-primary rounded-xl hover:bg-primary-strong dark:hover:bg-accent/90 disabled:opacity-50 font-medium"
              :disabled="store.isUpdating"
              @click="respond('accept')"
            >Aceptar propuesta</button>
            <button
              class="px-6 py-3 border border-rose-200 dark:border-rose-400/30 text-rose-600 dark:text-rose-300 rounded-xl hover:bg-rose-50 dark:hover:bg-rose-900/20 disabled:opacity-50"
              :disabled="store.isUpdating"
              @click="respond('reject')"
            >No por ahora</button>
          </div>
          <p v-if="responseMsg" class="mt-4 text-sm text-text-brand/70 dark:text-text-brand/70">{{ responseMsg }}</p>
        </footer>

        <footer
          v-else-if="store.current.status === DIAGNOSTIC_STATUS.ACCEPTED"
          class="diagnostic-card mt-8 bg-primary/5 dark:bg-primary-soft/5 border border-input-border/15 dark:border-input-border/15 rounded-3xl p-6 text-center text-text-brand dark:text-text-brand"
        >
          ¡Gracias! Confirmamos tu aceptación. Te contactaremos para coordinar el inicio.
        </footer>

        <footer
          v-else-if="store.current.status === DIAGNOSTIC_STATUS.REJECTED"
          class="diagnostic-card mt-8 bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-400/20 rounded-3xl p-6 text-center text-rose-800 dark:text-rose-200"
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
          data-testid="diagnostic-restart-tutorial"
          class="restart-tutorial-btn fixed bottom-[76px] left-6 z-[9990] w-11 h-11 rounded-full
                 bg-surface shadow-lg
                 border border-input-border/15 dark:border-input-border/25
                 text-text-default
                 flex items-center justify-center
                 hover:bg-primary/5 dark:hover:bg-primary/80
                 focus:outline-none focus-visible:ring-2 focus-visible:ring-lemon focus-visible:ring-offset-2
                 transition-all hover:scale-110"
          :aria-label="restartTutorialLabel"
          :title="restartTutorialLabel"
          @click="onboardingRef?.forceStart()"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>

        <DiagnosticOnboarding
          ref="onboardingRef"
          :language="store.current?.language || 'es'"
        />

        <button
          type="button"
          data-testid="diagnostic-theme-toggle"
          class="theme-toggle fixed bottom-6 left-6 z-[9990] w-11 h-11 rounded-full
                 bg-surface/90 dark:bg-primary/90 backdrop-blur-sm shadow-lg
                 border border-input-border/15 dark:border-input-border/20
                 text-text-default
                 flex items-center justify-center
                 hover:bg-primary/5 dark:hover:bg-primary-soft/10
                 focus:outline-none focus-visible:ring-2 focus-visible:ring-lemon focus-visible:ring-offset-2
                 transition-colors"
          :aria-label="isDark ? 'Activar modo claro' : 'Activar modo oscuro'"
          :aria-pressed="isDark"
          @click="toggleDarkMode"
        >
          <!-- Moon (visible in light mode → tap to go dark) -->
          <svg
            v-if="!isDark"
            class="w-5 h-5"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="1.8"
            aria-hidden="true"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z" />
          </svg>
          <!-- Sun (visible in dark mode → tap to go light) -->
          <svg
            v-else
            class="w-5 h-5"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="1.8"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="4" stroke-linecap="round" stroke-linejoin="round" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1.8M12 19.2V21M4.22 4.22l1.27 1.27M18.51 18.51l1.27 1.27M3 12h1.8M19.2 12H21M4.22 19.78l1.27-1.27M18.51 5.49l1.27-1.27" />
          </svg>
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import { DIAGNOSTIC_STATUS } from '~/stores/diagnostics_constants';
import { useDiagnosticDarkMode, DIAGNOSTIC_THEME_STORAGE_KEY } from '~/composables/useDiagnosticDarkMode';

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
import DiagnosticOnboarding from '~/components/WebAppDiagnostic/public/DiagnosticOnboarding.vue';

definePageMeta({ layout: false });

// Inline early script: applies the `dark` class to the diagnostic wrapper
// before Vue hydration to prevent a flash of light theme for users who
// previously chose dark or whose system prefers dark. Storage key is shared
// with the composable so they cannot drift.
useHead({
  script: [
    {
      tagPosition: 'bodyClose',
      innerHTML: `(function(){try{var k=${JSON.stringify(DIAGNOSTIC_THEME_STORAGE_KEY)};var v=localStorage.getItem(k);var d=v==='dark'||(v!=='light'&&window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches);if(!d)return;var apply=function(el){if(el)el.classList.add('dark');};var found=document.querySelector('.diagnostic-public');if(found){apply(found);return;}var mo=new MutationObserver(function(){var el=document.querySelector('.diagnostic-public');if(el){apply(el);mo.disconnect();}});mo.observe(document.body,{childList:true});setTimeout(function(){mo.disconnect();},3000);}catch(e){}})();`,
    },
  ],
});

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
const onboardingRef = ref(null);

const restartTutorialLabel = computed(() => (
  (store.current?.language || 'es') === 'en' ? 'Restart guide' : 'Reiniciar guía'
));

// Skip all tracking pings when an admin previews with ?preview=1.
const isPreview = computed(() => route.query?.preview === '1');

const { isDark, toggle: toggleDarkMode, hydrate: hydrateTheme } = useDiagnosticDarkMode();

const sections = computed(() => store.current?.sections || []);
const activeSection = computed(() => sections.value[activeIndex.value] || null);
const activeContent = computed(() => ({
  ...(activeSection.value?.content_json || {}),
  index: String(activeIndex.value + 1),
}));

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
  hydrateTheme();
  sessionId.value = generateSessionId();
  await Promise.all([
    store.fetchPublic(route.params.uuid),
    isPreview.value ? null : store.trackView(route.params.uuid, sessionId.value),
  ]);
  sectionEnteredAt.value = Date.now();
  markSectionVisited(sections.value[activeIndex.value]?.id);
  if (!isPreview.value && store.current && sections.value.length > 0) {
    nextTick(() => onboardingRef.value?.start());
  }
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

.diagnostic-public.dark {
  background-color: #001713;
  background-image:
    radial-gradient(ellipse 80% 60% at 50% 0%, rgba(240, 255, 61, 0.06) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 100%, rgba(16, 185, 129, 0.05) 0%, transparent 50%);
}

.theme-toggle {
  transition: background-color 0.2s ease, transform 0.2s ease;
}
.theme-toggle:hover {
  transform: scale(1.05);
}
</style>
