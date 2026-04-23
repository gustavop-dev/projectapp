<template>
  <div class="business-proposal" :class="(proposalDarkMode && viewMode) ? 'bg-[#0a1f1c]' : 'bg-white'">
    <!-- Loading state -->
    <PreloaderAnimation
      v-if="!showContent && !loadError"
      :active="true"
      :clientName="proposal?.client_name || ''"
      :language="pLang"
      @animationComplete="onAnimationComplete"
    />

    <!-- Error state -->
    <div v-else-if="loadError === 'not_found'" class="min-h-screen flex items-center justify-center">
      <div class="text-center">
        <h1 class="text-4xl font-light text-gray-400 mb-4">404</h1>
        <p class="text-gray-500">{{ browserLang === 'es' ? 'Esta propuesta no fue encontrada.' : 'This proposal was not found.' }}</p>
      </div>
    </div>

    <!-- Expired state (legacy 410 fallback — no full data available) -->
    <ProposalExpired v-else-if="loadError === 'expired'" :proposal="proposal" />

    <!-- Main proposal view -->
    <div
      v-else-if="showContent && proposal"
      ref="proposalContainer"
      class="proposal-wrapper"
      data-proposal-wrapper
      @touchstart.passive="onTouchStart"
      @touchend.passive="onTouchEnd"
    >
      <!-- Expired proposal banner — persistent, shown over full proposal -->
      <div v-if="isExpired" class="fixed top-0 left-0 right-0 z-[9998] bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg">
        <div class="max-w-4xl mx-auto px-4 py-3 flex flex-col sm:flex-row items-center justify-between gap-2 text-center sm:text-left">
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            <span class="text-sm font-medium">
              {{ pLang === 'es'
                ? `Esta propuesta expiró${expiredAtFormatted ? ' el ' + expiredAtFormatted : ''}. ¿Quieres que ${expiredSellerName} te envíe una versión actualizada?`
                : `This proposal expired${expiredAtFormatted ? ' on ' + expiredAtFormatted : ''}. Want ${expiredSellerName} to send you an updated version?`
              }}
            </span>
          </div>
          <a
            v-if="expiredWhatsappUrl"
            :href="expiredWhatsappUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-1.5 px-4 py-1.5 bg-white text-amber-700 rounded-lg text-sm font-semibold hover:bg-amber-50 transition-colors flex-shrink-0"
          >
            <svg class="w-4 h-4" viewBox="0 0 448 512" fill="currentColor"><path d="M380.9 97.1C339 55.1 283.2 32 223.9 32c-122.4 0-222 99.6-222 222 0 39.1 10.2 77.3 29.6 111L0 480l117.7-30.9c32.4 17.7 68.9 27 106.1 27h.1c122.3 0 224.1-99.6 224.1-222 0-59.3-25.2-115-67.1-157"/></svg>
            {{ pLang === 'es' ? 'Contactar por WhatsApp' : 'Contact via WhatsApp' }}
          </a>
        </div>
      </div>

      <!-- Preview mode banner -->
      <div v-if="isPreviewMode" class="fixed top-0 left-0 right-0 z-[9999] bg-amber-500 text-white text-center py-2 text-xs font-semibold tracking-wide shadow-md">
        👁 {{ pLang === 'es' ? 'MODO PREVIEW — El cliente no ve este banner' : 'PREVIEW MODE — The client does not see this banner' }}
        <button class="ml-4 underline text-white/80 hover:text-white" @click="exitPreview">{{ pLang === 'es' ? 'Volver al panel' : 'Back to panel' }}</button>
      </div>

      <!-- View mode gateway: shown when user hasn't chosen a view yet -->
      <Transition name="gateway-reveal">
        <ProposalViewGateway
          v-if="!viewMode"
          :language="pLang"
          :clientName="proposal.client_name || ''"
          :show-technical="hasTechnicalDocument"
          @select="handleViewModeSelect"
        />
      </Transition>

      <!-- Proposal sections: shown after view mode is chosen -->
      <template v-if="viewMode">
        <!-- UX overlay elements -->
        <ProposalIndex
          :sections="displayPanels"
          :currentIndex="currentIndex"
          :visitedPanelIds="visitedPanelIds"
          :viewMode="viewMode"
          :language="pLang"
          @navigate="handleNavigate"
          @update:open="(val) => indexOpen = val"
          @switchToDetailed="handleSwitchToDetailed"
          @backToGateway="handleBackToGateway"
        />
        <SectionCounter :current="currentIndex + 1" :total="totalSections" />
        <ExpirationBadge v-if="proposal.expires_at" :expiresAt="proposal.expires_at" />

        <!-- PDF download + Share -->
        <PdfDownloadButton
          :view-mode="viewMode"
          :selected-module-ids="pdfSelectedModuleIds"
        />
        <ShareProposalButton
          v-if="proposal?.uuid"
          :proposalUuid="proposal.uuid"
          :language="proposal?.language || 'es'"
        />

        <!-- Restart tutorial button -->
        <button
          v-if="viewMode && viewMode !== 'technical'"
          class="restart-tutorial-btn fixed bottom-[68px] left-6 z-[9990] w-10 h-10 rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-110"
          :class="proposalDarkMode ? 'bg-gray-700 text-emerald-300 hover:bg-gray-600' : 'bg-white text-emerald-600 border border-gray-200 hover:bg-gray-50'"
          :title="pLang === 'es' ? 'Reiniciar tutorial' : 'Restart tutorial'"
          @click="onboardingRef?.forceStart()"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>

        <!-- Dark mode toggle -->
        <button
          v-if="viewMode && viewMode !== 'technical'"
          class="dark-mode-toggle fixed bottom-6 left-6 z-[9990] w-10 h-10 rounded-full shadow-lg flex items-center justify-center text-lg transition-all hover:scale-110"
          :class="proposalDarkMode ? 'bg-gray-700 text-yellow-300 hover:bg-gray-600' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'"
          :title="pLang === 'es' ? 'Cambiar tema' : 'Toggle theme'"
          @click="toggleProposalDarkMode"
        >
          {{ proposalDarkMode ? '&#9728;&#65039;' : '&#127769;' }}
        </button>

        <!-- Onboarding tutorial tooltips -->
        <ProposalOnboarding
          v-if="viewMode !== 'technical'"
          ref="onboardingRef"
          :language="pLang"
          @complete="showReadingTimePopup"
        />

        <!-- Investment section onboarding (customize button tutorial) -->
        <InvestmentOnboarding
          v-if="viewMode === 'detailed'"
          ref="investmentOnboardingRef"
          :language="pLang"
          :proposalUuid="proposal?.uuid || ''"
          :hasModules="investmentHasModules"
        />

        <!-- Executive mode: teaser button onboarding -->
        <ExecutiveInvestmentOnboarding
          v-if="viewMode === 'executive'"
          ref="executiveInvestmentOnboardingRef"
          :language="pLang"
          :proposalUuid="proposal?.uuid || ''"
        />

        <!-- Functional requirements onboarding (click cards tutorial) -->
        <RequirementsOnboarding
          v-if="viewMode !== 'technical'"
          ref="requirementsOnboardingRef"
          :language="pLang"
          :proposalUuid="proposal?.uuid || ''"
        />



      <!-- View mode transition overlay (used for gateway selection + switch-to-detailed) -->
      <Teleport to="body">
        <Transition name="switch-mode-overlay">
          <div v-if="switchOverlayVisible" class="fixed inset-0 z-[10001] flex items-center justify-center bg-esmerald">
            <div class="text-center px-6">
              <div class="w-16 h-16 bg-lemon rounded-2xl flex items-center justify-center mx-auto mb-6 animate-bounce">
                <svg v-if="switchOverlayMode === 'executive'" class="w-8 h-8 text-esmerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <svg v-else-if="switchOverlayMode === 'technical'" class="w-8 h-8 text-esmerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                <svg v-else-if="switchOverlayMode === 'gateway'" class="w-8 h-8 text-esmerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
                <svg v-else class="w-8 h-8 text-esmerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h2 class="text-2xl sm:text-3xl font-bold text-lemon mb-3">
                {{ switchOverlayMode === 'executive'
                  ? (pLang === 'es' ? 'Vista Ejecutiva' : 'Executive View')
                  : switchOverlayMode === 'technical'
                    ? (pLang === 'es' ? 'Detalle técnico' : 'Technical detail')
                    : switchOverlayMode === 'gateway'
                      ? (pLang === 'es' ? 'Seleccionar vista' : 'Select view')
                      : (pLang === 'es' ? 'Propuesta Completa' : 'Full Proposal') }}
              </h2>
              <p class="text-sm text-lemon/70 font-light max-w-xs mx-auto">
                {{ switchOverlayMode === 'executive'
                  ? (pLang === 'es' ? 'Lo esencial de tu proyecto en un vistazo' : 'The essentials of your project at a glance')
                  : switchOverlayMode === 'technical'
                    ? (pLang === 'es' ? 'Arquitectura, stack y requerimientos técnicos' : 'Architecture, stack, and technical requirements')
                    : switchOverlayMode === 'gateway'
                      ? (pLang === 'es' ? 'Elige cómo quieres ver la propuesta' : 'Choose how to view the proposal')
                      : (pLang === 'es' ? 'Ahora verás todos los detalles de tu proyecto' : 'Now you\'ll see all the details of your project') }}
              </p>
            </div>
          </div>
        </Transition>
      </Teleport>

      <!-- Welcome-back toast (non-blocking) -->
      <Teleport to="body">
        <Transition name="fade-popup">
          <div v-if="welcomeBack" class="fixed bottom-6 right-6 z-[10000] max-w-xs w-full">
            <div class="bg-white rounded-2xl shadow-2xl border border-gray-100 p-5 relative">
              <button
                class="absolute top-3 right-3 w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-200 transition-colors text-xs"
                @click="welcomeBack = null"
              >✕</button>
              <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center flex-shrink-0">
                  <span class="text-xl">👋</span>
                </div>
                <h3 class="text-sm font-bold text-esmerald leading-tight">
                  {{ pLang === 'es' ? 'Bienvenido de nuevo' : 'Welcome back' }}{{ welcomeBack.clientName ? ', ' + welcomeBack.clientName : '' }}
                </h3>
              </div>
              <p class="text-xs text-esmerald/70 font-light leading-relaxed mb-4">
                <span v-if="welcomeBack.lastVisitTimestamp" class="block text-[10px] text-gray-400 mb-1">
                  {{ formatRelativeTime(welcomeBack.lastVisitTimestamp, pLang) }}
                </span>
                {{ pLang === 'es' ? 'La última vez llegaste hasta' : 'Last time you reached' }} <strong>{{ welcomeBack.sectionTitle }}</strong>.
              </p>
              <button
                class="w-full px-4 py-2.5 bg-esmerald text-lemon rounded-xl font-bold text-xs
                       hover:bg-esmerald/90 transition-colors shadow-sm"
                @click="navigateTo(welcomeBack.sectionIndex); welcomeBack = null"
              >
                {{ pLang === 'es' ? 'Continuar donde lo dejé' : 'Continue where I left off' }}
              </button>
              <button
                class="w-full mt-2 px-4 py-2 text-xs text-gray-400 hover:text-gray-600 transition-colors"
                @click="navigateTo(0); welcomeBack = null"
              >
                {{ pLang === 'es' ? 'Ver desde el inicio' : 'Start from the beginning' }}
              </button>
            </div>
          </div>
        </Transition>
      </Teleport>

      <!-- Reading time popup -->
      <Teleport to="body">
        <Transition name="fade-popup">
          <div v-if="readingPopupVisible" class="fixed inset-0 z-[10000] flex items-center justify-center p-6">
            <div class="absolute inset-0 bg-white/60 backdrop-blur-[3px]" />
            <div class="relative bg-white rounded-3xl shadow-2xl border border-gray-100 p-6 sm:p-8 max-w-sm w-full text-center">
              <div class="w-14 h-14 bg-esmerald rounded-2xl flex items-center justify-center mx-auto mb-5">
                <svg class="w-7 h-7 text-lemon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 class="text-lg font-bold text-esmerald mb-2">{{ pLang === 'es' ? `Tiempo de lectura: ~${readMinutesEstimate} minutos` : `Reading time: ~${readMinutesEstimate} minutes` }}</h3>
              <p class="text-sm text-esmerald/70 font-light leading-relaxed mb-6">
                {{ pLang === 'es' ? 'Por favor lee el contenido de todas las secciones. Cada una aborda un punto importante y diferente de la propuesta.' : 'Please read through all sections. Each one covers an important and different aspect of the proposal.' }}
              </p>
              <button
                class="w-full px-6 py-3 bg-esmerald text-lemon rounded-xl font-bold text-sm
                       hover:bg-esmerald/90 transition-colors shadow-sm"
                @click="readingPopupVisible = false"
              >
                {{ pLang === 'es' ? 'Entendido' : 'Got it' }}
              </button>
            </div>
          </div>
        </Transition>
      </Teleport>

      <!-- Side navigation arrows (fixed, outside transition) -->
      <SectionNavButtons
        :prevTitle="prevPanelTitle"
        :nextTitle="nextPanelTitle"
        :isFirst="currentIndex === 0"
        :isLast="currentIndex === totalSections - 1"
        :hideLeft="indexOpen"
        :blinkNext="navBlinkNext"
        :blinkPrev="navBlinkPrev"
        @prev="goPrev"
        @next="goNext"
      />

      <!-- Single-panel view with transition -->
      <Transition :name="transitionName" mode="out-in">
        <div :key="currentPanel.id" class="panel-container" :data-section-type="currentPanel.section_type">
          <RawContentSection
            v-if="isPastePanel(currentPanel)"
            :title="getPastePanelTitle(currentPanel)"
            :index="getPastePanelIndex(currentPanel)"
            :rawText="getPastePanelRawText(currentPanel)"
          />
          <component
            v-else
            :is="sectionComponentMap[currentPanel.section_type]"
            v-bind="getSectionProps(currentPanel)"
            v-on="getSectionListeners(currentPanel)"
          />
        </div>
      </Transition>
    </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onBeforeUnmount, onMounted, toRef, watch } from 'vue';
import { useProposalTracking } from '~/composables/useProposalTracking';
import PreloaderAnimation from '~/components/animations/PreloaderAnimation.vue';
import {
  Greeting,
  ExecutiveSummary,
  ContextDiagnostic,
  ConversionStrategy,
  DesignUX,
  CreativeSupport,
  DevelopmentStages,
  FunctionalRequirements,
  FunctionalRequirementsGroup,
  Timeline,
  Investment,
  FinalNote,
  NextSteps,
  ProposalSummary,
  ProcessMethodology,
  ValueAddedModules,
} from '~/components/BusinessProposal';
import ProposalIndex from '~/components/BusinessProposal/ProposalIndex.vue';
import SectionCounter from '~/components/BusinessProposal/SectionCounter.vue';
import ExpirationBadge from '~/components/BusinessProposal/ExpirationBadge.vue';
import ProposalExpired from '~/components/BusinessProposal/ProposalExpired.vue';
import PdfDownloadButton from '~/components/BusinessProposal/PdfDownloadButton.vue';
import RawContentSection from '~/components/BusinessProposal/RawContentSection.vue';
import ProposalClosing from '~/components/BusinessProposal/ProposalClosing.vue';
import SectionNavButtons from '~/components/BusinessProposal/SectionNavButtons.vue';
import ProposalOnboarding from '~/components/BusinessProposal/ProposalOnboarding.vue';
import InvestmentOnboarding from '~/components/BusinessProposal/InvestmentOnboarding.vue';
import ExecutiveInvestmentOnboarding from '~/components/BusinessProposal/ExecutiveInvestmentOnboarding.vue';
import RequirementsOnboarding from '~/components/BusinessProposal/RequirementsOnboarding.vue';
import ShareProposalButton from '~/components/BusinessProposal/ShareProposalButton.vue';
import WhatsAppFloatingButton from '~/components/BusinessProposal/WhatsAppFloatingButton.vue';
import ProposalViewGateway from '~/components/BusinessProposal/ProposalViewGateway.vue';
import TechnicalDocumentPublicPanel from '~/components/BusinessProposal/TechnicalDocumentPublicPanel.vue';
import { buildSyntheticTechnicalPanels } from '~/utils/technicalProposalPanels';
import {
  buildProposalModuleLinkCatalog,
  normalizeTechnicalDocumentModuleLinks,
} from '~/utils/proposalModuleLinkOptions';
import { filterTechnicalDocumentByModules } from '~/utils/filterTechnicalDocumentByModules';
import { useProposalDarkMode } from '~/composables/useProposalDarkMode';
import { normalizePersistedSelectedIds } from '~/utils/proposalModuleSelectionStorage';

definePageMeta({ layout: false });

const route = useRoute();
const router = useRouter();
const proposalStore = useProposalStore();

const isPreviewMode = computed(() => route.query.preview === '1' || route.query.preview === 'true');
function exitPreview() {
  router.back();
}

const { isDark: proposalDarkMode, toggle: toggleProposalDarkMode, applyTheme: applyProposalTheme } = useProposalDarkMode();

const pLang = computed(() => proposal.value?.language || 'es');
const browserLang = computed(() => {
  if (import.meta.server) return 'en';
  return (navigator.language || '').startsWith('es') ? 'es' : 'en';
});

const sectionComponentMap = {
  greeting: Greeting,
  executive_summary: ExecutiveSummary,
  context_diagnostic: ContextDiagnostic,
  conversion_strategy: ConversionStrategy,
  design_ux: DesignUX,
  creative_support: CreativeSupport,
  development_stages: DevelopmentStages,
  process_methodology: ProcessMethodology,
  functional_requirements: FunctionalRequirements,
  functional_requirements_group: FunctionalRequirementsGroup,
  value_added_modules: ValueAddedModules,
  timeline: Timeline,
  investment: Investment,
  final_note: FinalNote,
  next_steps: NextSteps,
  proposal_summary: ProposalSummary,
  proposal_closing: ProposalClosing,
  technical_document_public: TechnicalDocumentPublicPanel,
};

const proposal = computed(() => proposalStore.currentProposal);
const enabledSections = computed(() => proposalStore.enabledSections);

// Expired proposal banner data (from expired_meta returned by backend)
const expiredAtFormatted = computed(() => {
  const raw = proposal.value?.expired_meta?.expired_at;
  if (!raw) return '';
  try {
    const lang = pLang.value === 'es' ? 'es-CO' : 'en-US';
    return new Date(raw).toLocaleDateString(lang, { day: 'numeric', month: 'long', year: 'numeric' });
  } catch { return ''; }
});
const expiredSellerName = computed(() => {
  return proposal.value?.expired_meta?.seller_name || (pLang.value === 'es' ? 'nuestro equipo' : 'our team');
});
const expiredWhatsappUrl = computed(() => {
  return proposal.value?.expired_meta?.whatsapp_url || '';
});

// 4.5 — Personalized OG meta tags for WhatsApp sharing
useHead({
  title: computed(() => proposal.value ? `Propuesta para ${proposal.value.client_name}` : 'Propuesta'),
  meta: computed(() => {
    if (!proposal.value) return [];
    const p = proposal.value;
    const lang = p.language || 'es';
    const title = lang === 'en'
      ? `Proposal for ${p.client_name}`
      : `Propuesta para ${p.client_name}`;
    const desc = lang === 'en'
      ? `${p.client_name}, here is your custom proposal: ${p.title}`
      : `${p.client_name}, aquí está tu propuesta personalizada: ${p.title}`;
    return [
      { property: 'og:title', content: title },
      { property: 'og:description', content: desc },
      { property: 'og:type', content: 'website' },
      { name: 'description', content: desc },
    ];
  }),
});

const viewMode = ref(null); // null = gateway, 'executive', 'detailed', 'technical'
const EXECUTIVE_SECTION_TYPES = new Set([
  'greeting', 'executive_summary', 'proposal_summary', 'value_added_modules', 'functional_requirements', 'investment', 'timeline', 'proposal_closing',
]);

const hasTechnicalDocument = computed(() =>
  enabledSections.value.some((s) => s.section_type === 'technical_document'),
);

const technicalModuleLinkCatalog = computed(() =>
  buildProposalModuleLinkCatalog(enabledSections.value),
);

const hasConfirmedModuleSelection = ref(false);

function effectiveSelectedModuleIdsForTechnical() {
  if (!hasConfirmedModuleSelection.value) return null;
  const fromUi = [...selectedCalculatorModuleIds.value];
  if (fromUi.length) return fromUi;
  const persisted = proposal.value?.selected_modules;
  if (Array.isArray(persisted)) return [...persisted];
  return [];
}

const readMinutesEstimate = computed(() => {
  if (viewMode.value === 'executive') return 2;
  if (viewMode.value === 'technical') return 12;
  return 8;
});

// Build display panels: skip next_steps (merged into final_note), no FR sub-panels
// When viewMode is 'executive', filter to only executive section types
// When 'technical', synthetic panels from technical_document + closing
const displayPanels = computed(() => {
  const lang = pLang.value === 'en' ? 'en' : 'es';

  if (viewMode.value === 'technical') {
    const tech = enabledSections.value.find((s) => s.section_type === 'technical_document');
    if (!tech) return [];
    const rawDoc = tech.content_json && typeof tech.content_json === 'object' ? tech.content_json : {};
    const normalizedDoc = normalizeTechnicalDocumentModuleLinks(
      rawDoc,
      technicalModuleLinkCatalog.value.aliasMap,
    );
    const docForPanels = filterTechnicalDocumentByModules(
      normalizedDoc,
      effectiveSelectedModuleIdsForTechnical(),
      technicalModuleLinkCatalog.value.alwaysIncludedIds,
    );
    const panels = buildSyntheticTechnicalPanels({ ...tech, content_json: docForPanels }, lang);
    if (enabledSections.value.length > 0) {
      const finalNote = enabledSections.value.find((s) => s.section_type === 'final_note');
      const fnContent = finalNote?.content_json || {};
      panels.push({
        id: 'proposal_closing',
        section_type: 'proposal_closing',
        title: lang === 'en' ? '🤝 Next Steps' : '🤝 Próximos pasos',
        _validityMessage: fnContent.validityMessage || '',
        _thankYouMessage: fnContent.thankYouMessage || '',
        _expiresAt: proposal.value?.expires_at || '',
      });
    }
    return panels;
  }

  const panels = [];
  const isExecutive = viewMode.value === 'executive';

  const frSection = enabledSections.value.find((s) => s.section_type === 'functional_requirements');
  const frGroupIds = new Set(
    (frSection?.content_json?.groups || [])
      .map((g) => g && g.id)
      .filter(Boolean),
  );

  for (const section of enabledSections.value) {
    // Skip next_steps — its content is merged into final_note
    if (section.section_type === 'next_steps') continue;
    if (section.section_type === 'technical_document') continue;
    // In executive mode, skip sections not in the executive set
    if (isExecutive && !EXECUTIVE_SECTION_TYPES.has(section.section_type)) continue;
    // Hide value_added_modules when no ids resolve against FR groups
    if (section.section_type === 'value_added_modules') {
      const ids = section.content_json?.module_ids || [];
      const resolvable = ids.some((id) => frGroupIds.has(id));
      if (!resolvable) continue;
    }
    panels.push(section);
  }

  // Add closing panel (validity, thank-you, accept/reject) after all sections
  // Only add when sections are loaded to prevent marking it as visited on first render
  if (enabledSections.value.length > 0) {
    const finalNote = enabledSections.value.find(s => s.section_type === 'final_note');
    const fnContent = finalNote?.content_json || {};
    panels.push({
      id: 'proposal_closing',
      section_type: 'proposal_closing',
      title: lang === 'es' ? '🤝 Próximos pasos' : '🤝 Next Steps',
      _validityMessage: fnContent.validityMessage || '',
      _thankYouMessage: fnContent.thankYouMessage || '',
      _expiresAt: proposal.value?.expires_at || '',
    });
  }

  return panels;
});

const totalSections = computed(() => displayPanels.value.length);

const showContent = ref(false);
const loadError = ref(null);
const proposalContainer = ref(null);
const currentIndex = ref(0);
const visitedPanelIds = ref(new Set());
const transitionName = ref('slide-left');
const indexOpen = ref(false);
const navBlinkNext = ref(false);
const navBlinkPrev = ref(false);
let blinkTimer = null;
const onboardingRef = ref(null);
const investmentOnboardingRef = ref(null);
const executiveInvestmentOnboardingRef = ref(null);
const requirementsOnboardingRef = ref(null);
const readingPopupVisible = ref(false);
const switchOverlayVisible = ref(false);
const switchOverlayMode = ref('detailed');
const welcomeBack = ref(null);

// Current panel and neighbors
const currentPanel = computed(() => displayPanels.value[currentIndex.value] || displayPanels.value[0]);

// Track visited panels whenever currentIndex changes
watch(currentPanel, (panel) => {
  if (panel?.id !== undefined) {
    visitedPanelIds.value = new Set([...visitedPanelIds.value, panel.id]);
  }
  // Persist progress for welcome-back
  if (panel && proposal.value?.uuid && !isPreviewMode.value) {
    try {
      const key = `proposal-${proposal.value.uuid}-progress`;
      localStorage.setItem(key, JSON.stringify({
        sectionIndex: currentIndex.value,
        sectionTitle: panel.title || '',
        clientName: proposal.value.client_name || '',
        lastVisitTimestamp: Date.now(),
      }));
    } catch (_e) { /* ignore */ }
  }
}, { immediate: true });

// Investment onboarding: detect if investment section has modules (customize button)
const investmentHasModules = computed(() => {
  const inv = enabledSections.value.find(s => s.section_type === 'investment');
  const modules = inv?.content_json?.modules || [];
  return modules.length > 0 || allGroupCalculatorItems.value.length > 0;
});

// Trigger investment onboarding when user navigates to investment section
let investmentOnboardingTriggered = false;
let executiveInvestmentOnboardingTriggered = false;
let requirementsOnboardingTriggered = false;
watch(currentPanel, (panel) => {
  if (
    panel?.section_type === 'investment' &&
    !investmentOnboardingTriggered &&
    investmentHasModules.value &&
    viewMode.value === 'detailed'
  ) {
    investmentOnboardingTriggered = true;
    setTimeout(() => {
      investmentOnboardingRef.value?.start();
    }, 800);
  }
  // Trigger executive investment onboarding (teaser button) in executive mode
  if (
    panel?.section_type === 'investment' &&
    !executiveInvestmentOnboardingTriggered &&
    viewMode.value === 'executive'
  ) {
    executiveInvestmentOnboardingTriggered = true;
    setTimeout(() => {
      executiveInvestmentOnboardingRef.value?.start();
    }, 800);
  }
  // Trigger requirements onboarding when user reaches functional_requirements section
  if (
    panel?.section_type === 'functional_requirements' &&
    !requirementsOnboardingTriggered &&
    viewMode.value !== 'technical'
  ) {
    requirementsOnboardingTriggered = true;
    setTimeout(() => {
      requirementsOnboardingRef.value?.start();
    }, 800);
  }
});

// Section engagement tracking
const proposalUuidRef = computed(() => proposal.value?.uuid || route.params.uuid);
const { flush: flushTracking } = useProposalTracking(proposalUuidRef, currentPanel, viewMode);

function showReadingTimePopup() {
  readingPopupVisible.value = true;
}

function formatRelativeTime(timestamp, lang) {
  const diff = Date.now() - timestamp;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (lang === 'es') {
    if (minutes < 60) return `Hace ${minutes} ${minutes === 1 ? 'minuto' : 'minutos'}`;
    if (hours < 24) return `Hace ${hours} ${hours === 1 ? 'hora' : 'horas'}`;
    return `Hace ${days} ${days === 1 ? 'día' : 'días'}`;
  }
  if (minutes < 60) return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`;
  if (hours < 24) return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
  return `${days} ${days === 1 ? 'day' : 'days'} ago`;
}
// Extract WhatsApp link from next_steps section primaryCTA if it contains wa.me
const extractedWhatsappLink = computed(() => {
  const nextSteps = enabledSections.value.find(s => s.section_type === 'next_steps');
  const cta = nextSteps?.content_json?.primaryCTA;
  if (cta?.link && cta.link.includes('wa.me')) return cta.link;
  return '';
});

// Unified calculator items: every FR group with price_percent becomes a toggleable calculator item
const allGroupCalculatorItems = computed(() => {
  const frSection = enabledSections.value.find(s => s.section_type === 'functional_requirements');
  if (!frSection) return [];
  const investmentSection = enabledSections.value.find(s => s.section_type === 'investment');
  const investContent = investmentSection?.content_json || {};
  const baseTotal = parseInt(String(investContent.totalInvestment || '').replace(/[^\d]/g, ''), 10) || 0;
  const cj = frSection.content_json || {};
  const allGroups = [...(cj.groups || []), ...(cj.additionalModules || [])].filter(g => {
    if (g.is_visible === false) return false;
    return g.is_calculator_module === true;
  });
  const items = [];
  for (const group of allGroups) {
    const isCalcModule = group.is_calculator_module === true;
    const pricePercent = group.price_percent ?? 0;
    const price = pricePercent > 0 ? Math.round(baseTotal * pricePercent / 100) : 0;
    // Backward compat: selected ?? default_selected ?? true (regular groups default to selected)
    const defaultSelected = group.selected ?? group.default_selected ?? !isCalcModule;
    items.push({
      id: isCalcModule ? `module-${group.id}` : `group-${group.id}`,
      name: `${group.icon || ''} ${group.title}`.trim(),
      groupId: group.id,
      price,
      included: true,
      is_required: pricePercent === 0 && !group.is_invite,
      default_selected: defaultSelected,
      is_calculator_module: isCalcModule,
      is_invite: group.is_invite || false,
      invite_note: group.invite_note || '',
      _source: isCalcModule ? 'calculator_module' : 'functional_requirements',
      description: group.description || '',
      detailItems: group.items || [],
    });
  }
  return items;
});

const selectedCalculatorModuleIds = ref(new Set());
const customizedTotal = ref(null);
const effectiveInvestment = ref(null);

// Client-facing total: client's customization wins, then backend effective
// (base + admin-default additional modules), then plain base as last resort.
const resolvedInvestmentTotal = computed(() =>
  customizedTotal.value
  ?? effectiveInvestment.value
  ?? Number(proposal.value?.total_investment || 0),
);

// PDF download includes the current in-memory selection only when the client
// has actively confirmed a customization; otherwise the backend-stored
// selected_modules are used server-side.
const pdfSelectedModuleIds = computed(() => {
  if (!hasConfirmedModuleSelection.value) return null;
  const ids = [...selectedCalculatorModuleIds.value];
  return ids.length ? ids : null;
});

const effectiveBaselineTotal = computed(() =>
  Number(effectiveInvestment.value || proposal.value?.total_investment || 0),
);

const isInvestmentCustomized = computed(() =>
  customizedTotal.value != null
  && Number(customizedTotal.value) !== effectiveBaselineTotal.value,
);

const confirmedModuleCount = computed(() =>
  hasConfirmedModuleSelection.value ? selectedCalculatorModuleIds.value.size : null,
);

// Helper: recompute payment option amounts using ratio logic (same as Investment.vue computedPaymentOptions)
function recomputePaymentOptions(paymentOptions, baseTotalStr, customTotal) {
  if (customTotal == null || !paymentOptions?.length) return paymentOptions;
  const baseNum = parseInt(String(baseTotalStr || '').replace(/[^\d]/g, ''), 10) || 0;
  if (baseNum <= 0) return paymentOptions;
  const ratio = customTotal / baseNum;
  return paymentOptions.map(opt => {
    const descNum = parseInt(String(opt.description || '').replace(/[^\d]/g, ''), 10) || 0;
    if (descNum <= 0) return opt;
    const newAmount = Math.round(descNum * ratio);
    const formatted = newAmount.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    const newDesc = opt.description.replace(/[\$]?[\d.,]+/, formatted);
    return { ...opt, description: newDesc.startsWith('$') ? newDesc : '$' + newDesc };
  });
}

const prevPanelTitle = computed(() => {
  const prev = displayPanels.value[currentIndex.value - 1];
  return prev?.title || '';
});
const nextPanelTitle = computed(() => {
  const next = displayPanels.value[currentIndex.value + 1];
  return next?.title || '';
});

// Effective total comes from the backend so admin, client view, and PDF
// stay aligned; ``customizedTotal`` is reserved for real client changes that
// the client makes during this page session (calculator confirm). Page
// reload always returns to the backend baseline — no localStorage rehydration.
function computeInitialSelection() {
  if (!proposal.value) return;

  const calcItems = allGroupCalculatorItems.value;
  const investmentSection = enabledSections.value.find(s => s.section_type === 'investment');
  const investmentModules = investmentSection?.content_json?.modules || [];

  const persistedRaw = Array.isArray(proposal.value.selected_modules)
    ? proposal.value.selected_modules
    : [];
  const persisted = normalizePersistedSelectedIds(persistedRaw, calcItems);

  let selectedIds;
  if (persisted.length) {
    selectedIds = new Set(persisted);
  } else {
    const derived = [];
    for (const m of investmentModules) {
      if (m.is_required === true || m.default_selected !== false) derived.push(m.id);
    }
    for (const m of calcItems) {
      if (m.default_selected === true) derived.push(m.id);
    }
    selectedIds = new Set(derived);
  }

  selectedCalculatorModuleIds.value = new Set(selectedIds);
  hasConfirmedModuleSelection.value = proposal.value.has_confirmed_module_selection === true;
  customizedTotal.value = null;

  const base = Number(proposal.value.total_investment || 0);
  const backendEffective = Number(proposal.value.effective_total_investment || 0);
  effectiveInvestment.value = backendEffective > 0 ? backendEffective : base;
}

// --- Fetch proposal on mount ---
const isExpired = ref(false);

onMounted(async () => {
  const uuid = route.params.uuid;
  const result = await proposalStore.fetchPublicProposal(uuid);
  if (!result.success) {
    loadError.value = result.error;
  } else if (result.expired) {
    isExpired.value = true;
  } else {
    computeInitialSelection();
  }
});

// --- Section props transformer ---
function getSectionProps(section) {
  const content = section.content_json || {};

  if (section.section_type === 'proposal_closing') {
    const investmentSection = enabledSections.value.find(s => s.section_type === 'investment');
    const investContent = investmentSection?.content_json || {};
    const rawPaymentOptions = investContent.paymentOptions || [];
    const displayTotal = resolvedInvestmentTotal.value;
    return {
      proposal: proposal.value,
      validityMessage: section._validityMessage || '',
      thankYouMessage: section._thankYouMessage || '',
      expiresAt: section._expiresAt || '',
      language: proposal.value?.language || 'es',
      whatsappLink: extractedWhatsappLink.value,
      paymentOptions: recomputePaymentOptions(rawPaymentOptions, investContent.totalInvestment, displayTotal),
      customizedTotal: displayTotal,
      selectedModuleIds: effectiveSelectedModuleIdsForTechnical() || [],
      viewMode: viewMode.value || 'detailed',
    };
  }

  if (section.section_type === 'technical_document_public') {
    return {
      fragment: section._technicalFragment || 'intro',
      contentJson: section.content_json || {},
      language: proposal.value?.language || 'es',
    };
  }

  if (section.section_type === 'greeting') {
    return {
      proposalTitle: content.proposalTitle || proposal.value?.title || '',
      clientName: content.clientName || proposal.value?.client_name || '',
      inspirationalQuote: content.inspirationalQuote,
    };
  }

  if (section.section_type === 'value_added_modules') {
    return {
      section,
      proposal: proposal.value || { sections: enabledSections.value },
      proposalUuid: proposal.value?.uuid || '',
    };
  }

  if ([
    'executive_summary', 'context_diagnostic', 'conversion_strategy',
    'design_ux', 'creative_support',
  ].includes(section.section_type)) {
    return { content };
  }

  if (section.section_type === 'functional_requirements') {
    // Use groups from content_json; fall back to legacy requirement_groups from proposal
    let groups = content.groups || [];
    if (!groups.length) {
      const legacyGroups = proposal.value?.requirement_groups || [];
      groups = legacyGroups.map((g) => ({
        id: g.group_id,
        icon: g.title?.trim().split(' ')[0] || '🧩',
        title: g.title?.trim().split(' ').slice(1).join(' ') || g.title,
        description: g.description,
        items: (g.items || []).map((item) => ({
          icon: item.icon,
          name: item.name,
          description: item.description,
        })),
      }));
    }
    // Build a price map for all groups with price_percent so FR cards can show price badges
    const investmentSection = enabledSections.value.find(s => s.section_type === 'investment');
    const investContent = investmentSection?.content_json || {};
    const baseTotal = parseInt(String(investContent.totalInvestment || '').replace(/[^\d]/g, ''), 10) || 0;
    const groupPriceMap = {};
    for (const g of [...(content.additionalModules || []), ...groups]) {
      if (g.price_percent != null && g.price_percent > 0) {
        groupPriceMap[g.id] = Math.round(baseTotal * g.price_percent / 100);
      }
    }
    // Unified selected IDs: combine calculator module selections + group selections
    const allSelectedIds = [...selectedCalculatorModuleIds.value];
    // Hide groups already showcased in the value_added_modules section (when enabled)
    // to avoid visual duplication. Their canonical data stays in FR.groups[] as catalog.
    const vamSection = enabledSections.value.find(
      (s) => s.section_type === 'value_added_modules' && s.is_enabled !== false,
    );
    const valueAddedModuleIds = Array.isArray(vamSection?.content_json?.module_ids)
      ? vamSection.content_json.module_ids
      : [];
    return {
      data: {
        ...content,
        groups,
        additionalModules: content.additionalModules || [],
      },
      language: proposal.value?.language || 'es',
      selectedCalculatorModules: allSelectedIds,
      calculatorModulePrices: groupPriceMap,
      currency: investContent.currency || proposal.value?.currency || 'COP',
      proposalUuid: proposal.value?.uuid || '',
      valueAddedModuleIds,
    };
  }

  // For investment: inject discount data from proposal
  if (section.section_type === 'investment') {
    const investmentModules = (content.modules || []).map(m => ({ ...m, _source: 'investment' }));
    const allCalculatorItems = [...investmentModules, ...allGroupCalculatorItems.value];
    // Extract baseWeeks from timeline section's totalDuration
    const timelineSection = enabledSections.value.find(s => s.section_type === 'timeline');
    const totalDuration = timelineSection?.content_json?.totalDuration || '';
    const weeksMatch = totalDuration.match(/(\d+)\s*(semana|week)/i);
    const baseWeeks = weeksMatch ? parseInt(weeksMatch[1], 10) : 0;
    // Always use proposal.total_investment as the source of truth for display
    const proposalTotal = Number(proposal.value?.total_investment || 0);
    const proposalCurrency = proposal.value?.currency || content.currency || 'COP';
    const formattedTotal = proposalTotal > 0
      ? '$' + proposalTotal.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
      : content.totalInvestment || '';
    // Model fields are the source of truth for hosting %/discounts; content_json.hostingPlan
    // only supplies presentation (title, specs, copy). Override numeric fields so the public
    // view never drifts from what the admin configured in the General tab.
    const baseHostingPlan = content.hostingPlan || {};
    const discountByFrequency = {
      semiannual: proposal.value?.hosting_discount_semiannual,
      quarterly: proposal.value?.hosting_discount_quarterly,
    };
    const hostingPlan = {
      ...baseHostingPlan,
      hostingPercent: proposal.value?.hosting_percent ?? baseHostingPlan.hostingPercent ?? 30,
      billingTiers: (baseHostingPlan.billingTiers || []).map((tier) => {
        const override = discountByFrequency[tier?.frequency];
        return override != null ? { ...tier, discountPercent: override } : tier;
      }),
    };
    return {
      ...content,
      hostingPlan,
      totalInvestment: formattedTotal,
      currency: proposalCurrency,
      language: proposal.value?.language || 'es',
      discountPercent: proposal.value?.discount_percent || 0,
      discountedInvestment: proposal.value?.discounted_investment || '',
      expiresAt: proposal.value?.expires_at || '',
      modules: allCalculatorItems,
      proposalUuid: proposal.value?.uuid || '',
      whatsappLink: extractedWhatsappLink.value,
      baseWeeks,
      sentAt: proposal.value?.sent_at || '',
      viewMode: viewMode.value || 'detailed',
      effectiveTotal: resolvedInvestmentTotal.value || effectiveBaselineTotal.value,
      isCustomized: isInvestmentCustomized.value,
      selectedModuleIds: [...selectedCalculatorModuleIds.value],
    };
  }

  // For proposal_summary: inject proposal-level data + investment info for calculator sync
  if (section.section_type === 'proposal_summary') {
    const timelineSection = enabledSections.value.find(s => s.section_type === 'timeline');
    const timelineDuration = timelineSection?.content_json?.totalDuration || '';
    const investmentSection = enabledSections.value.find(s => s.section_type === 'investment');
    const investContent = investmentSection?.content_json || {};
    const investmentModules = (investContent.modules || []).map(m => ({ ...m, _source: 'investment' }));
    const allCalculatorItems = [...investmentModules, ...allGroupCalculatorItems.value];
    const effectiveTotal = resolvedInvestmentTotal.value;
    const formattedSummaryTotal = effectiveTotal > 0
      ? '$' + effectiveTotal.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
      : investContent.totalInvestment || '';
    const rawPaymentOptions = investContent.paymentOptions || [];
    return {
      content,
      proposal: proposal.value,
      timelineDuration,
      language: proposal.value?.language || 'es',
      proposalUuid: proposal.value?.uuid || '',
      investmentModules: allCalculatorItems,
      rawTotalInvestment: formattedSummaryTotal,
      paymentOptions: recomputePaymentOptions(rawPaymentOptions, investContent.totalInvestment, effectiveTotal),
      customizedTotal: effectiveTotal,
      isCustomized: isInvestmentCustomized.value,
      selectedModuleCount: confirmedModuleCount.value,
    };
  }

  // For final_note: merge next_steps data as additional props
  if (section.section_type === 'final_note') {
    const nextStepsSection = enabledSections.value.find(s => s.section_type === 'next_steps');
    const nsContent = nextStepsSection?.content_json || {};
    const lang = proposal.value?.language || 'es';
    const defaultKickoff = lang === 'en'
      ? [
          { day: 'D1', title: 'Contract signing', description: 'We formalize the agreement and send you access credentials.' },
          { day: 'D2', title: 'Onboarding call', description: 'Your Project Manager contacts you to align expectations and priorities.' },
          { day: 'D3', title: 'Access & setup', description: 'We configure the technical environment and shared tools.' },
          { day: 'D4', title: 'Technical kickoff', description: 'The development team reviews the architecture and starts the first tasks.' },
          { day: 'D5', title: 'Sprint planning', description: 'We define the first sprint goals and deliverables together.' },
        ]
      : [
          { day: 'D1', title: 'Firma de contrato', description: 'Formalizamos el acuerdo y te enviamos credenciales de acceso.' },
          { day: 'D2', title: 'Llamada de onboarding', description: 'Tu Project Manager te contacta para alinear expectativas y prioridades.' },
          { day: 'D3', title: 'Accesos y setup', description: 'Configuramos el entorno técnico y herramientas compartidas.' },
          { day: 'D4', title: 'Kickoff técnico', description: 'El equipo de desarrollo revisa la arquitectura e inicia las primeras tareas.' },
          { day: 'D5', title: 'Sprint planning', description: 'Definimos juntos los objetivos y entregables del primer sprint.' },
        ];
    return {
      ...content,
      language: lang,
      kickoffPlan: content.kickoffPlan || defaultKickoff,
      nextSteps: nsContent.steps || [],
      nextStepsIntro: nsContent.introMessage || '',
      ctaMessage: nsContent.ctaMessage || '',
      primaryCTA: nsContent.primaryCTA || {},
      secondaryCTA: nsContent.secondaryCTA || {},
      contactMethods: nsContent.contactMethods || [],
    };
  }

  // For development_stages, timeline, etc.
  // Spread content_json as individual props
  return content;
}

function getSectionListeners(section) {
  const type = section.section_type;
  const listeners = {};
  if (type === 'investment') {
    listeners.navigateToRequirements = handleNavigateToRequirements;
    listeners.updateCalculatorModules = onCalculatorModulesUpdate;
    listeners.updateCustomTotal = onCustomTotalUpdate;
    listeners.selectionConfirmed = onModuleSelectionConfirmed;
    listeners.switchToDetailed = handleSwitchToDetailed;
  }
  return listeners;
}

function isPastePanel(panel) {
  return panel.content_json?._editMode === 'paste' && panel.content_json?.rawText;
}

function getPastePanelTitle(panel) {
  return panel.content_json?.title || panel.title;
}

function getPastePanelIndex(panel) {
  return panel.content_json?.index || '';
}

function getPastePanelRawText(panel) {
  return panel.content_json?.rawText || '';
}

// --- Navigation ---
function triggerNavBlink() {
  if (blinkTimer) clearTimeout(blinkTimer);
  navBlinkNext.value = false;
  navBlinkPrev.value = false;
  // Use nextTick to re-trigger animation even if same prop value
  setTimeout(() => {
    const isLast = currentIndex.value === totalSections.value - 1;
    if (isLast) {
      navBlinkPrev.value = true;
    } else {
      navBlinkNext.value = true;
    }
    blinkTimer = setTimeout(() => {
      navBlinkNext.value = false;
      navBlinkPrev.value = false;
    }, 4000);
  }, 100);
}

function navigateTo(index) {
  if (index < 0 || index >= totalSections.value) return;
  transitionName.value = index > currentIndex.value ? 'slide-left' : 'slide-right';
  currentIndex.value = index;
  window.scrollTo({ top: 0, behavior: 'auto' });
  triggerNavBlink();
}

function handleNavigate(index) {
  navigateTo(index);
}

function handleNavigateToRequirements() {
  const idx = displayPanels.value.findIndex(p => p.section_type === 'functional_requirements');
  if (idx !== -1) navigateTo(idx);
}


const OVERLAY_TRANSITION_MS = 1000;

function switchMode(overlayMode, newViewMode, { scrollToTop = false, beforeSwitch = null, startOnboarding = false } = {}) {
  switchOverlayMode.value = overlayMode;
  switchOverlayVisible.value = true;
  setTimeout(() => {
    if (beforeSwitch) beforeSwitch();
    viewMode.value = newViewMode;
    currentIndex.value = 0;
    if (scrollToTop) window.scrollTo({ top: 0, behavior: 'auto' });
    switchOverlayVisible.value = false;
    if (startOnboarding && !welcomeBack.value) nextTick(() => onboardingRef.value?.start());
  }, OVERLAY_TRANSITION_MS);
}

function handleViewModeSelect(mode) {
  switchMode(mode, mode, { startOnboarding: true });
}

function handleSwitchToDetailed() {
  switchMode('detailed', 'detailed', { scrollToTop: true });
}

function handleBackToGateway() {
  switchMode('gateway', null, { scrollToTop: true, beforeSwitch: flushTracking });
}

function onCustomTotalUpdate(total) {
  customizedTotal.value = total;
}

function onCalculatorModulesUpdate(selectedIds) {
  if (!Array.isArray(selectedIds)) return;
  // Store the full live selection — both investment-type and calculator-type
  // module IDs — so the modal can reopen in the same state after the user
  // navigates between sections, even if they didn't explicitly confirm.
  selectedCalculatorModuleIds.value = new Set(selectedIds);
}

function onModuleSelectionConfirmed({ selectedIds } = {}) {
  hasConfirmedModuleSelection.value = true;
  selectedCalculatorModuleIds.value = new Set(
    Array.isArray(selectedIds) ? selectedIds : [],
  );
}

function goNext() {
  navigateTo(currentIndex.value + 1);
}

function goPrev() {
  navigateTo(currentIndex.value - 1);
}

// --- Keyboard navigation ---
function handleKeydown(e) {
  const tag = document.activeElement?.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
  if (e.key === 'ArrowRight') { e.preventDefault(); goNext(); }
  if (e.key === 'ArrowLeft') { e.preventDefault(); goPrev(); }
}

// --- Swipe gesture detection ---
let touchStartX = 0;
let touchStartY = 0;

function onTouchStart(e) {
  const touch = e.touches?.[0];
  if (!touch) return;
  touchStartX = touch.clientX;
  touchStartY = touch.clientY;
}

function onTouchEnd(e) {
  const touch = e.changedTouches?.[0];
  if (!touch) return;
  const deltaX = touch.clientX - touchStartX;
  const deltaY = touch.clientY - touchStartY;

  // Only trigger if horizontal swipe is dominant and long enough
  if (Math.abs(deltaX) > 50 && Math.abs(deltaX) > Math.abs(deltaY) * 1.5) {
    if (deltaX < 0) goNext();   // swipe left → next
    else goPrev();              // swipe right → previous
  }
}

// --- Lifecycle ---
const onAnimationComplete = () => {
  if (loadError.value) return;
  showContent.value = true;
  nextTick(() => applyProposalTheme(false));
  window.addEventListener('keydown', handleKeydown);

  // Allow bypassing gateway via URL query param (used by E2E tests and direct links)
  const queryMode = typeof route.query.mode === 'string' ? route.query.mode : '';
  if (queryMode === 'executive' || queryMode === 'detailed' || queryMode === 'technical') {
    if (queryMode !== 'technical' || hasTechnicalDocument.value) {
      viewMode.value = queryMode;
    }
  }

  // Check for returning client (welcome-back) — viewMode is null here so gateway always shows first
  // The welcome-back data is stored so we can show it after the user picks a view mode
  if (!isPreviewMode.value && proposal.value?.uuid) {
    try {
      const key = `proposal-${proposal.value.uuid}-progress`;
      const saved = localStorage.getItem(key);
      if (saved) {
        const data = JSON.parse(saved);
        if (data.sectionIndex > 0 && data.sectionIndex < totalSections.value) {
          welcomeBack.value = data;
          return; // Skip onboarding — show welcome-back instead
        }
      }
    } catch (_e) { /* ignore */ }
  }

  // If viewMode is set (returning visitor), start onboarding; otherwise gateway is shown
  if (viewMode.value) {
    nextTick(() => {
      onboardingRef.value?.start();
    });
  }
};

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown);
});
</script>

<style scoped>
.business-proposal {
  overflow-x: hidden;
}

.proposal-wrapper {
  opacity: 0;
  animation: fadeIn 0.8s ease-in forwards;
}

.panel-container {
  width: 100%;
  min-height: 100vh;
}

.panel-container :deep(section:not(.greeting-section)) {
  scroll-margin-top: 40px;
}

.panel-container :deep(.min-h-screen:not(.greeting-section)) {
  padding-top: 48px;
}

.panel-container :deep(.greeting-section) {
  padding-top: 0;
}

/* On mobile: scrollable sections get bottom padding so PDF/WhatsApp buttons
   don't cover content. Greeting stays untouched. */
@media (max-width: 639px) {
  .panel-container :deep(.min-h-screen:not(.greeting-section)) {
    padding-top: 48px;
  }
  .panel-container :deep(section:not(.greeting-section):not(.min-h-screen)) {
    padding-top: 80px;
    padding-bottom: 100px;
  }
  .panel-container :deep(.greeting-section) {
    padding-top: 0;
  }
}

/* Slide left (navigating forward) */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: transform 0.65s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.65s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-left-enter-from {
  opacity: 0;
  transform: translateX(30px);
}
.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* Slide right (navigating backward) */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.65s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.65s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}
.slide-right-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}

.fade-popup-enter-active {
  transition: opacity 0.3s ease;
}
.fade-popup-leave-active {
  transition: opacity 0.2s ease;
}
.fade-popup-enter-from,
.fade-popup-leave-to {
  opacity: 0;
}

/* Gateway reveal — enters while overlay fades out, creating a crossfade.
   transition-delay staggers the reveal slightly behind the overlay fade-out start. */
.gateway-reveal-enter-active {
  transition: opacity 0.7s ease-out, transform 0.7s cubic-bezier(0.22, 1, 0.36, 1);
  transition-delay: 0.15s;
}
.gateway-reveal-leave-active {
  transition: opacity 0.25s ease-in;
}
.gateway-reveal-enter-from {
  opacity: 0;
  transform: translateY(28px);
}
.gateway-reveal-leave-to {
  opacity: 0;
}

/* Mode switch overlay — clean scale+fade in, slow fade-out to crossfade with incoming content */
.switch-mode-overlay-enter-active {
  transition: opacity 0.35s ease-out, transform 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}
.switch-mode-overlay-leave-active {
  transition: opacity 0.55s ease-in-out;
}
.switch-mode-overlay-enter-from {
  opacity: 0;
  transform: scale(1.04);
}
.switch-mode-overlay-leave-to {
  opacity: 0;
}

/* ── Proposal Dark Mode Overrides ── */
/* All selectors use :deep() to penetrate into child section components */

[data-theme="dark"] {
  background-color: #0a1f1c;
  background-image:
    radial-gradient(ellipse 80% 60% at 50% 0%, rgba(16, 185, 129, 0.07) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 100%, rgba(16, 185, 129, 0.04) 0%, transparent 50%);
  background-attachment: fixed;
}

[data-theme="dark"] :deep(section),
[data-theme="dark"] :deep(.proposal-summary),
[data-theme="dark"] :deep(.process-methodology),
[data-theme="dark"] :deep(.proposal-closing) {
  background-color: transparent !important;
  box-shadow: none !important;
}

/* White & light backgrounds → dark (elevated for contrast) */
[data-theme="dark"] :deep(.bg-white) {
  background-color: #143d35 !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
}
[data-theme="dark"] :deep(.bg-esmerald\/5),
[data-theme="dark"] :deep(.bg-esmerald\/10) {
  background-color: #133832 !important;
}
[data-theme="dark"] :deep(.bg-gray-50) {
  background-color: #112e29 !important;
}

/* Yellow notice backgrounds (validity notice in ProposalClosing) */
[data-theme="dark"] :deep(.bg-yellow-50) {
  background-color: rgba(202, 138, 4, 0.28) !important;
}
[data-theme="dark"] :deep(.border-yellow-200) {
  border-color: rgba(202, 138, 4, 0.45) !important;
}
[data-theme="dark"] :deep(.text-yellow-600) {
  color: #fbbf24 !important;
}

/* Amber backgrounds (discount banners) */
[data-theme="dark"] :deep(.bg-amber-50),
[data-theme="dark"] :deep(.from-amber-50),
[data-theme="dark"] :deep(.to-orange-50) {
  background-color: rgba(217, 119, 6, 0.28) !important;
}
[data-theme="dark"] :deep(.border-amber-300) {
  border-color: rgba(217, 119, 6, 0.50) !important;
}

/* Green notice backgrounds (accepted state, recovery) */
[data-theme="dark"] :deep(.bg-green-50) {
  background-color: rgba(16, 185, 129, 0.22) !important;
}
[data-theme="dark"] :deep(.border-green-200) {
  border-color: rgba(16, 185, 129, 0.30) !important;
}

/* Esmerald text → light */
[data-theme="dark"] :deep(.text-esmerald) {
  color: #E6EFEF !important;
}
[data-theme="dark"] :deep(.text-esmerald\/80) {
  color: rgba(230, 239, 239, 0.8) !important;
}
[data-theme="dark"] :deep(.text-esmerald\/70) {
  color: rgba(230, 239, 239, 0.72) !important;
}
[data-theme="dark"] :deep(.text-esmerald\/60) {
  color: rgba(230, 239, 239, 0.62) !important;
}
[data-theme="dark"] :deep(.text-esmerald\/40) {
  color: rgba(230, 239, 239, 0.4) !important;
}

/* Esmerald-light text (used inside dark-bg asides) */
[data-theme="dark"] :deep(.text-esmerald-light) {
  color: #c8ddd8 !important;
}
[data-theme="dark"] :deep(.text-esmerald-light\/80) {
  color: rgba(200, 221, 216, 0.8) !important;
}

/* Green-light text */
[data-theme="dark"] :deep(.text-green-light) {
  color: #a0b8b2 !important;
}

/* Esmerald-light backgrounds (timeline duration box, icon badges) */
[data-theme="dark"] :deep(.bg-esmerald-light\/60) {
  background-color: rgba(16, 185, 129, 0.30) !important;
}

/* Borders — esmerald shades */
[data-theme="dark"] :deep(.border-esmerald\/10) {
  border-color: rgba(16, 185, 129, 0.18) !important;
}
[data-theme="dark"] :deep(.border-esmerald\/15) {
  border-color: rgba(16, 185, 129, 0.22) !important;
}
[data-theme="dark"] :deep(.border-esmerald\/20) {
  border-color: rgba(16, 185, 129, 0.28) !important;
}
[data-theme="dark"] :deep(.border-esmerald\/30) {
  border-color: rgba(16, 185, 129, 0.38) !important;
}

/* Borders — gray shades */
[data-theme="dark"] :deep(.border-gray-100) {
  border-color: rgba(230, 239, 239, 0.20) !important;
}
[data-theme="dark"] :deep(.border-gray-200) {
  border-color: rgba(230, 239, 239, 0.25) !important;
}

/* Borders — emerald shades (stages, methodology, timeline) */
[data-theme="dark"] :deep(.border-emerald-100) {
  border-color: rgba(16, 185, 129, 0.30) !important;
}
[data-theme="dark"] :deep(.border-emerald-200) {
  border-color: rgba(16, 185, 129, 0.40) !important;
}

/* Cards and surfaces — elevated with shadow + emerald glow */
[data-theme="dark"] :deep(.summary-card),
[data-theme="dark"] :deep(.gateway-card) {
  background-color: #16423a !important;
  border-color: rgba(16, 185, 129, 0.25) !important;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.6), 0 0 18px rgba(16, 185, 129, 0.14), inset 0 1px 0 rgba(16, 185, 129, 0.08) !important;
}

/* Gray text adjustments */
[data-theme="dark"] :deep(.text-gray-400) {
  color: rgba(230, 239, 239, 0.45) !important;
}
[data-theme="dark"] :deep(.text-gray-500),
[data-theme="dark"] :deep(.text-gray-600) {
  color: rgba(230, 239, 239, 0.55) !important;
}
[data-theme="dark"] :deep(.text-gray-700) {
  color: rgba(230, 239, 239, 0.65) !important;
}
[data-theme="dark"] :deep(.text-gray-800),
[data-theme="dark"] :deep(.text-gray-900) {
  color: rgba(230, 239, 239, 0.9) !important;
}

/* Lemon stays visible on dark */
[data-theme="dark"] :deep(.bg-lemon) {
  background-color: #F0FF3D !important;
}

/* Emerald backgrounds in sections */
[data-theme="dark"] :deep(.bg-emerald-50),
[data-theme="dark"] :deep(.bg-emerald-100) {
  background-color: rgba(16, 185, 129, 0.25) !important;
}

/* Client-action badges (ProcessMethodology "Tu aporte" pills) */
[data-theme="dark"] :deep(.bg-emerald-50.text-emerald-600) {
  background-color: rgba(16, 185, 129, 0.18) !important;
  color: #6ee7b7 !important;
  border: 1px solid rgba(16, 185, 129, 0.30);
}

/* Timeline, stages connectors */
[data-theme="dark"] :deep(.bg-emerald-200) {
  background-color: rgba(16, 185, 129, 0.40) !important;
}

/* Modals keep their own styling, override outer bg */
[data-theme="dark"] :deep(.fixed.inset-0 .bg-white) {
  background-color: #1a3d36 !important;
}

/* Welcome-back & reading-time popups */
[data-theme="dark"] :deep(.shadow-2xl.border.border-gray-100) {
  background-color: #16423a !important;
  border-color: rgba(16, 185, 129, 0.22) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.65), 0 0 24px rgba(16, 185, 129, 0.15) !important;
}

/* Overlay components (nav buttons, counters, badges) */
[data-theme="dark"] :deep(.bg-white\/80) {
  background-color: rgba(15, 43, 38, 0.8) !important;
}
[data-theme="dark"] :deep(.bg-white\/90) {
  background-color: rgba(15, 43, 38, 0.9) !important;
}
[data-theme="dark"] :deep(.bg-white\/95) {
  background-color: rgba(15, 43, 38, 0.95) !important;
}
[data-theme="dark"] :deep(.bg-white\/60) {
  background-color: rgba(15, 43, 38, 0.6) !important;
}

/* SectionCounter, PdfDownloadButton, ShareButton text in dark */
[data-theme="dark"] :deep(.text-emerald-600) {
  color: #6ee7b7 !important;
}
[data-theme="dark"] :deep(.text-emerald-700) {
  color: #6ee7b7 !important;
}

/* Nav buttons (SectionNavButtons uses scoped CSS with inline rgba) */
[data-theme="dark"] :deep(.nav-side) {
  background: rgba(15, 43, 38, 0.92) !important;
  color: #a0b8b2 !important;
  border-color: rgba(16, 185, 129, 0.3) !important;
}
[data-theme="dark"] :deep(.nav-side:hover) {
  background: rgba(15, 43, 38, 1) !important;
  color: #6ee7b7 !important;
}

/* Index panel in dark */
[data-theme="dark"] :deep(.index-panel) {
  background-color: rgba(10, 31, 28, 0.95) !important;
}
[data-theme="dark"] :deep(.index-toggle) {
  background-color: rgba(15, 43, 38, 0.9) !important;
}

/* Expiration badge dark variants */
[data-theme="dark"] :deep(.bg-emerald-50\/90) {
  background-color: rgba(16, 185, 129, 0.28) !important;
}
[data-theme="dark"] :deep(.bg-yellow-50\/90) {
  background-color: rgba(202, 138, 4, 0.28) !important;
}
[data-theme="dark"] :deep(.bg-orange-50\/90) {
  background-color: rgba(234, 88, 12, 0.28) !important;
}
[data-theme="dark"] :deep(.bg-red-50\/90) {
  background-color: rgba(220, 38, 38, 0.28) !important;
}

/* Share & PDF buttons */
[data-theme="dark"] :deep(.share-btn) {
  background-color: rgba(15, 43, 38, 0.9) !important;
  border-color: rgba(230, 239, 239, 0.15) !important;
}
[data-theme="dark"] :deep(.pdf-download) {
  background-color: rgba(15, 43, 38, 0.9) !important;
  border-color: rgba(230, 239, 239, 0.15) !important;
}

/* RawContentSection prose overrides */
[data-theme="dark"] :deep(.raw-content-card) {
  background-color: #143d35 !important;
  border-color: rgba(16, 185, 129, 0.22) !important;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.6), 0 0 18px rgba(16, 185, 129, 0.14), inset 0 1px 0 rgba(16, 185, 129, 0.08) !important;
}
[data-theme="dark"] :deep(.prose h1),
[data-theme="dark"] :deep(.prose h2),
[data-theme="dark"] :deep(.prose h3),
[data-theme="dark"] :deep(.prose h4) {
  color: #E6EFEF !important;
}
[data-theme="dark"] :deep(.prose p),
[data-theme="dark"] :deep(.prose ul),
[data-theme="dark"] :deep(.prose ol) {
  color: rgba(230, 239, 239, 0.7) !important;
}
[data-theme="dark"] :deep(.prose strong) {
  color: #E6EFEF !important;
}
[data-theme="dark"] :deep(.prose a) {
  color: #6ee7b7 !important;
}

/* FinalNote badge-card and note-content */
[data-theme="dark"] :deep(.badge-card) {
  background-color: #143d35 !important;
  border-color: rgba(16, 185, 129, 0.20) !important;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.6), 0 0 18px rgba(16, 185, 129, 0.14), inset 0 1px 0 rgba(16, 185, 129, 0.08) !important;
}
[data-theme="dark"] :deep(.note-content) {
  background-color: #143d35 !important;
  border-color: rgba(16, 185, 129, 0.20) !important;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.6), 0 0 18px rgba(16, 185, 129, 0.14), inset 0 1px 0 rgba(16, 185, 129, 0.08) !important;
}

/* ProposalIndex items in dark */
[data-theme="dark"] :deep(.bg-gray-200) {
  background-color: rgba(230, 239, 239, 0.18) !important;
}
[data-theme="dark"] :deep(.bg-gray-100) {
  background-color: rgba(230, 239, 239, 0.12) !important;
}
[data-theme="dark"] :deep(.hover\:bg-gray-50:hover) {
  background-color: rgba(230, 239, 239, 0.08) !important;
}

/* Box-shadows on interactive cards — dual layer: depth + emerald glow */
[data-theme="dark"] :deep(.overview-card),
[data-theme="dark"] :deep(.payment-option-card),
[data-theme="dark"] :deep(.step-card),
[data-theme="dark"] :deep(.contact-card) {
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.6), 0 0 18px rgba(16, 185, 129, 0.15), inset 0 1px 0 rgba(16, 185, 129, 0.08) !important;
}
[data-theme="dark"] :deep(.overview-card:hover),
[data-theme="dark"] :deep(.payment-option-card:hover),
[data-theme="dark"] :deep(.step-card:hover),
[data-theme="dark"] :deep(.contact-card:hover) {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.7), 0 0 28px rgba(16, 185, 129, 0.20), inset 0 1px 0 rgba(16, 185, 129, 0.12) !important;
  border-color: rgba(16, 185, 129, 0.35) !important;
}

/* Timeline phase cards get shadow */
[data-theme="dark"] :deep(.timeline-item .bg-white) {
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.6), 0 0 18px rgba(16, 185, 129, 0.14) !important;
}

/* DevelopmentStages cards */
[data-theme="dark"] :deep(.development-stages .border-emerald-100) {
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.55), 0 0 16px rgba(16, 185, 129, 0.12), inset 0 1px 0 rgba(16, 185, 129, 0.06) !important;
}

/* ProposalClosing recovery/notice cards */
[data-theme="dark"] :deep(.validity-notice) {
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.55), 0 0 16px rgba(16, 185, 129, 0.12) !important;
}

/* Blue recovery cards (ProposalClosing — "not the right time") */
[data-theme="dark"] :deep(.bg-blue-50) {
  background-color: rgba(59, 130, 246, 0.15) !important;
}
[data-theme="dark"] :deep(.border-blue-200) {
  border-color: rgba(59, 130, 246, 0.30) !important;
}

/* Purple recovery cards (ProposalClosing — "does not meet expectations") */
[data-theme="dark"] :deep(.bg-purple-50) {
  background-color: rgba(139, 92, 246, 0.15) !important;
}
[data-theme="dark"] :deep(.border-purple-200) {
  border-color: rgba(139, 92, 246, 0.30) !important;
}

/* Keep checkmark strokes dark inside lemon boxes */
[data-theme="dark"] :deep(.bg-lemon .text-esmerald) {
  color: #064e3b !important;
}
/* Keep text dark on lemon-bg elements (e.g. customize investment button) */
[data-theme="dark"] :deep(.bg-lemon.text-esmerald) {
  color: #064e3b !important;
}
[data-theme="dark"] :deep(button.bg-lemon) {
  background-color: #F0FF3D !important;
  color: #064e3b !important;
  box-shadow: 0 4px 16px rgba(240, 255, 61, 0.15), 0 0 12px rgba(240, 255, 61, 0.10) !important;
}

/* Pricing card — intensify shadow for premium feel */
[data-theme="dark"] :deep(.pricing-card) {
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.7), 0 0 32px rgba(16, 185, 129, 0.18) !important;
}

/* Value proposition dark-bg sections — subtle inner glow */
[data-theme="dark"] :deep(.bg-esmerald) {
  box-shadow: inset 0 0 60px rgba(0, 0, 0, 0.2), 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}

/* Section dividers — subtle gradient line between sections */
[data-theme="dark"] :deep(section + section)::before {
  content: '';
  display: block;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.20) 30%, rgba(16, 185, 129, 0.20) 70%, transparent);
  margin: 0 auto;
  width: 80%;
}

/* Nav buttons & overlays — stronger glass effect */
[data-theme="dark"] :deep(.nav-side) {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5) !important;
}

/* Index panel — deeper backdrop */
[data-theme="dark"] :deep(.index-panel) {
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.6) !important;
}

/* Share & PDF buttons — subtle glow on hover */
[data-theme="dark"] :deep(.share-btn:hover),
[data-theme="dark"] :deep(.pdf-download:hover) {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5), 0 0 12px rgba(16, 185, 129, 0.12) !important;
  border-color: rgba(16, 185, 129, 0.30) !important;
}
</style>
