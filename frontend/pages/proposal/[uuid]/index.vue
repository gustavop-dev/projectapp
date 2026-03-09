<template>
  <div class="business-proposal bg-white">
    <!-- Loading state -->
    <PreloaderAnimation
      v-if="!showContent && !loadError"
      :active="true"
      @animationComplete="onAnimationComplete"
    />

    <!-- Error state -->
    <div v-else-if="loadError === 'not_found'" class="min-h-screen flex items-center justify-center">
      <div class="text-center">
        <h1 class="text-4xl font-light text-gray-400 mb-4">404</h1>
        <p class="text-gray-500">{{ browserLang === 'es' ? 'Esta propuesta no fue encontrada.' : 'This proposal was not found.' }}</p>
      </div>
    </div>

    <!-- Expired state -->
    <ProposalExpired v-else-if="loadError === 'expired'" :proposal="proposal" />

    <!-- Main proposal view -->
    <div
      v-else-if="showContent && proposal"
      ref="proposalContainer"
      class="proposal-wrapper"
      @touchstart.passive="onTouchStart"
      @touchend.passive="onTouchEnd"
    >
      <!-- Preview mode banner -->
      <div v-if="isPreviewMode" class="fixed top-0 left-0 right-0 z-[9999] bg-amber-500 text-white text-center py-2 text-xs font-semibold tracking-wide shadow-md">
        👁 {{ pLang === 'es' ? 'MODO PREVIEW — El cliente no ve este banner' : 'PREVIEW MODE — The client does not see this banner' }}
        <button class="ml-4 underline text-white/80 hover:text-white" @click="exitPreview">{{ pLang === 'es' ? 'Volver al panel' : 'Back to panel' }}</button>
      </div>

      <!-- UX overlay elements -->
      <ProposalIndex
        :sections="displayPanels"
        :currentIndex="currentIndex"
        :visitedPanelIds="visitedPanelIds"
        @navigate="handleNavigate"
        @update:open="(val) => indexOpen = val"
      />
      <SectionCounter :current="currentIndex + 1" :total="totalSections" />
      <ExpirationBadge v-if="proposal.expires_at" :expiresAt="proposal.expires_at" />

      <!-- PDF download + Share -->
      <PdfDownloadButton />
      <ShareProposalButton
        v-if="proposal?.uuid"
        :proposalUuid="proposal.uuid"
        :language="proposal?.language || 'es'"
      />

      <!-- Onboarding tutorial tooltips -->
      <ProposalOnboarding ref="onboardingRef" :language="pLang" @complete="showReadingTimePopup" />


      <!-- Welcome-back overlay -->
      <Teleport to="body">
        <Transition name="fade-popup">
          <div v-if="welcomeBack" class="fixed inset-0 z-[10000] flex items-center justify-center p-6">
            <div class="absolute inset-0 bg-white/60 backdrop-blur-[3px]" />
            <div class="relative bg-white rounded-3xl shadow-2xl border border-gray-100 p-6 sm:p-8 max-w-sm w-full text-center">
              <div class="w-14 h-14 bg-emerald-50 rounded-2xl flex items-center justify-center mx-auto mb-5">
                <span class="text-3xl">👋</span>
              </div>
              <h3 class="text-lg font-bold text-esmerald mb-2">
                {{ pLang === 'es' ? 'Bienvenido de nuevo' : 'Welcome back' }}{{ welcomeBack.clientName ? ', ' + welcomeBack.clientName : '' }}.
              </h3>
              <p class="text-sm text-esmerald/70 font-light leading-relaxed mb-6">
                {{ pLang === 'es' ? 'La última vez llegaste hasta' : 'Last time you reached' }} <strong>{{ welcomeBack.sectionTitle }}</strong>. {{ pLang === 'es' ? '¿Quieres continuar?' : 'Want to continue?' }}
              </p>
              <div class="flex flex-col gap-2">
                <button
                  class="w-full px-6 py-3 bg-esmerald text-lemon rounded-xl font-bold text-sm
                         hover:bg-esmerald/90 transition-colors shadow-sm"
                  @click="navigateTo(welcomeBack.sectionIndex); welcomeBack = null"
                >
                  {{ pLang === 'es' ? 'Continuar donde lo dejé' : 'Continue where I left off' }}
                </button>
                <button
                  class="w-full px-6 py-3 text-gray-500 text-sm font-medium hover:text-gray-700 transition-colors"
                  @click="welcomeBack = null"
                >
                  {{ pLang === 'es' ? 'Empezar desde el inicio' : 'Start from the beginning' }}
                </button>
              </div>
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
              <h3 class="text-lg font-bold text-esmerald mb-2">{{ pLang === 'es' ? 'Tiempo de lectura: ~6 minutos' : 'Reading time: ~6 minutes' }}</h3>
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
            @navigateToRequirements="handleNavigateToRequirements"
          />
        </div>
      </Transition>
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
import ShareProposalButton from '~/components/BusinessProposal/ShareProposalButton.vue';

definePageMeta({ layout: false });

const route = useRoute();
const router = useRouter();
const proposalStore = useProposalStore();

const isPreviewMode = computed(() => route.query.preview === '1' || route.query.preview === 'true');
function exitPreview() {
  router.back();
}

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
  timeline: Timeline,
  investment: Investment,
  final_note: FinalNote,
  next_steps: NextSteps,
  proposal_summary: ProposalSummary,
  proposal_closing: ProposalClosing,
};

const proposal = computed(() => proposalStore.currentProposal);
const enabledSections = computed(() => proposalStore.enabledSections);

// Build display panels: skip next_steps (merged into final_note), no FR sub-panels
const displayPanels = computed(() => {
  const panels = [];
  for (const section of enabledSections.value) {
    // Skip next_steps — its content is merged into final_note
    if (section.section_type === 'next_steps') continue;
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
      title: pLang.value === 'es' ? '🤝 Próximos pasos' : '🤝 Next Steps',
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
const readingPopupVisible = ref(false);
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
      }));
    } catch (_e) { /* ignore */ }
  }
}, { immediate: true });

// Section engagement tracking
const proposalUuidRef = computed(() => proposal.value?.uuid || route.params.uuid);
useProposalTracking(proposalUuidRef, currentPanel);

function showReadingTimePopup() {
  readingPopupVisible.value = true;
}
// Extract WhatsApp link from next_steps section primaryCTA if it contains wa.me
const extractedWhatsappLink = computed(() => {
  const nextSteps = enabledSections.value.find(s => s.section_type === 'next_steps');
  const cta = nextSteps?.content_json?.primaryCTA;
  if (cta?.link && cta.link.includes('wa.me')) return cta.link;
  return '';
});

const configurableRequirementItems = computed(() => {
  const frSection = enabledSections.value.find(s => s.section_type === 'functional_requirements');
  if (!frSection) return [];
  const cj = frSection.content_json || {};
  const allGroups = [...(cj.groups || []), ...(cj.additionalModules || [])];
  const items = [];
  for (const group of allGroups) {
    for (const item of (group.items || [])) {
      if (item.price != null || item.is_required === false) {
        items.push({
          id: `fr-${group.id || group.title}-${item.name}`.replace(/\s+/g, '-').toLowerCase(),
          name: `${item.name}`,
          groupTitle: group.title,
          price: item.price ?? 0,
          included: true,
          is_required: item.is_required === true,
          _source: 'functional_requirements',
        });
      }
    }
  }
  return items;
});

function computeAllModuleIds() {
  const investmentSection = enabledSections.value.find(s => s.section_type === 'investment');
  if (!investmentSection) return [];
  const content = investmentSection.content_json || {};
  const investmentIds = (content.modules || []).map(m => m.id).filter(Boolean);
  const frIds = configurableRequirementItems.value.map(item => item.id);
  return [...investmentIds, ...frIds];
}

const prevPanelTitle = computed(() => {
  const prev = displayPanels.value[currentIndex.value - 1];
  return prev?.title || '';
});
const nextPanelTitle = computed(() => {
  const next = displayPanels.value[currentIndex.value + 1];
  return next?.title || '';
});

// --- Fetch proposal on mount ---
onMounted(async () => {
  const uuid = route.params.uuid;
  const result = await proposalStore.fetchPublicProposal(uuid);
  if (!result.success) {
    loadError.value = result.error;
  }
});

// --- Section props transformer ---
function getSectionProps(section) {
  const content = section.content_json || {};

  if (section.section_type === 'proposal_closing') {
    return {
      proposal: proposal.value,
      validityMessage: section._validityMessage || '',
      thankYouMessage: section._thankYouMessage || '',
      expiresAt: section._expiresAt || '',
      language: proposal.value?.language || 'es',
      whatsappLink: extractedWhatsappLink.value,
    };
  }

  if (section.section_type === 'greeting') {
    return {
      proposalTitle: content.proposalTitle || proposal.value?.title || '',
      clientName: content.clientName || proposal.value?.client_name || '',
      inspirationalQuote: content.inspirationalQuote,
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
    return {
      data: {
        ...content,
        groups,
        additionalModules: content.additionalModules || [],
      },
      language: proposal.value?.language || 'es',
    };
  }

  // For investment: inject discount data from proposal
  if (section.section_type === 'investment') {
    const investmentModules = (content.modules || []).map(m => ({ ...m, _source: 'investment' }));
    const allCalculatorItems = [...investmentModules, ...configurableRequirementItems.value];
    // Extract baseWeeks from timeline section's totalDuration
    const timelineSection = enabledSections.value.find(s => s.section_type === 'timeline');
    const totalDuration = timelineSection?.content_json?.totalDuration || '';
    const weeksMatch = totalDuration.match(/(\d+)\s*(semana|week)/i);
    const baseWeeks = weeksMatch ? parseInt(weeksMatch[1], 10) : 0;
    return {
      ...content,
      language: proposal.value?.language || 'es',
      discountPercent: proposal.value?.discount_percent || 0,
      discountedInvestment: proposal.value?.discounted_investment || '',
      expiresAt: proposal.value?.expires_at || '',
      modules: allCalculatorItems,
      proposalUuid: proposal.value?.uuid || '',
      whatsappLink: extractedWhatsappLink.value,
      baseWeeks,
    };
  }

  // For proposal_summary: inject proposal-level data
  if (section.section_type === 'proposal_summary') {
    const timelineSection = enabledSections.value.find(s => s.section_type === 'timeline');
    const timelineDuration = timelineSection?.content_json?.totalDuration || '';
    return {
      content,
      proposal: proposal.value,
      timelineDuration,
      language: proposal.value?.language || 'es',
    };
  }

  // For final_note: merge next_steps data as additional props
  if (section.section_type === 'final_note') {
    const nextStepsSection = enabledSections.value.find(s => s.section_type === 'next_steps');
    const nsContent = nextStepsSection?.content_json || {};
    return {
      ...content,
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
  // Clear stale module selections and pre-populate with "all selected" default
  try {
    const uuid = proposal.value?.uuid;
    if (uuid) {
      localStorage.removeItem(`proposal-${uuid}-modules`);
      const allIds = computeAllModuleIds();
      if (allIds.length) {
        localStorage.setItem(`proposal-${uuid}-modules`, JSON.stringify(allIds));
      }
    }
  } catch (_e) { /* ignore */ }
  showContent.value = true;
  window.addEventListener('keydown', handleKeydown);

  // Check for returning client (welcome-back)
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

  // Start onboarding tutorial after a short delay for elements to render
  nextTick(() => {
    onboardingRef.value?.start();
  });
};

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown);
});
</script>

<style scoped>
.business-proposal {
  background-color: white;
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
</style>
