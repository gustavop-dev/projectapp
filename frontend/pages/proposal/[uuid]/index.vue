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
      <ProposalViewGateway
        v-if="!viewMode"
        :language="pLang"
        :clientName="proposal.client_name || ''"
        @select="handleViewModeSelect"
      />

      <!-- Proposal sections: shown after view mode is chosen -->
      <template v-if="viewMode">
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

        <!-- Dark mode toggle -->
        <button
          v-if="viewMode"
          class="fixed bottom-6 left-6 z-[9990] w-10 h-10 rounded-full shadow-lg flex items-center justify-center text-lg transition-all hover:scale-110"
          :class="proposalDarkMode ? 'bg-gray-700 text-yellow-300 hover:bg-gray-600' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'"
          :title="pLang === 'es' ? 'Cambiar tema' : 'Toggle theme'"
          @click="toggleProposalDarkMode"
        >
          {{ proposalDarkMode ? '☀️' : '🌙' }}
        </button>

        <!-- Onboarding tutorial tooltips -->
        <ProposalOnboarding ref="onboardingRef" :language="pLang" @complete="showReadingTimePopup" />



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
              <h3 class="text-lg font-bold text-esmerald mb-2">{{ pLang === 'es' ? `Tiempo de lectura: ~${viewMode === 'executive' ? '2' : '8'} minutos` : `Reading time: ~${viewMode === 'executive' ? '2' : '8'} minutes` }}</h3>
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
            @updateCalculatorModules="onCalculatorModulesUpdate"
            @switchToDetailed="handleSwitchToDetailed"
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
import WhatsAppFloatingButton from '~/components/BusinessProposal/WhatsAppFloatingButton.vue';
import ProposalViewGateway from '~/components/BusinessProposal/ProposalViewGateway.vue';
import { useProposalDarkMode } from '~/composables/useProposalDarkMode';

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
  timeline: Timeline,
  investment: Investment,
  final_note: FinalNote,
  next_steps: NextSteps,
  proposal_summary: ProposalSummary,
  proposal_closing: ProposalClosing,
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

const viewMode = ref(null); // null = gateway, 'executive', 'detailed'
const EXECUTIVE_SECTION_TYPES = new Set([
  'greeting', 'executive_summary', 'proposal_summary', 'investment', 'timeline', 'proposal_closing',
]);

// Build display panels: skip next_steps (merged into final_note), no FR sub-panels
// When viewMode is 'executive', filter to only executive section types
const displayPanels = computed(() => {
  const panels = [];
  const isExecutive = viewMode.value === 'executive';

  for (const section of enabledSections.value) {
    // Skip next_steps — its content is merged into final_note
    if (section.section_type === 'next_steps') continue;
    // In executive mode, skip sections not in the executive set
    if (isExecutive && !EXECUTIVE_SECTION_TYPES.has(section.section_type)) continue;
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
        lastVisitTimestamp: Date.now(),
      }));
    } catch (_e) { /* ignore */ }
  }
}, { immediate: true });

// Section engagement tracking
const proposalUuidRef = computed(() => proposal.value?.uuid || route.params.uuid);
useProposalTracking(proposalUuidRef, currentPanel, viewMode);

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

const configurableRequirementItems = computed(() => {
  const frSection = enabledSections.value.find(s => s.section_type === 'functional_requirements');
  if (!frSection) return [];
  const cj = frSection.content_json || {};
  const allGroups = [...(cj.groups || []), ...(cj.additionalModules || [])].filter(g => g.is_visible !== false);
  const items = [];
  for (const group of allGroups) {
    if (group.is_calculator_module) continue;
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

const calculatorModuleItems = computed(() => {
  const frSection = enabledSections.value.find(s => s.section_type === 'functional_requirements');
  if (!frSection) return [];
  const investmentSection = enabledSections.value.find(s => s.section_type === 'investment');
  const investContent = investmentSection?.content_json || {};
  const baseTotal = parseInt(String(investContent.totalInvestment || '').replace(/[^\d]/g, ''), 10) || 0;
  const cj = frSection.content_json || {};
  const allGroups = [...(cj.groups || []), ...(cj.additionalModules || [])].filter(g => g.is_visible !== false);
  const items = [];
  for (const group of allGroups) {
    if (!group.is_calculator_module) continue;
    const pricePercent = group.price_percent;
    const price = pricePercent != null ? Math.round(baseTotal * pricePercent / 100) : 0;
    items.push({
      id: `module-${group.id}`,
      name: `${group.icon || ''} ${group.title}`.trim(),
      groupId: group.id,
      price,
      included: true,
      is_required: false,
      default_selected: group.default_selected ?? false,
      is_invite: group.is_invite || false,
      invite_note: group.invite_note || '',
      _source: 'calculator_module',
      description: group.description || '',
      detailItems: group.items || [],
    });
  }
  return items;
});

const selectedCalculatorModuleIds = ref(new Set());

function computeAllModuleIds() {
  const investmentSection = enabledSections.value.find(s => s.section_type === 'investment');
  if (!investmentSection) return [];
  const content = investmentSection.content_json || {};
  const investmentIds = (content.modules || []).map(m => m.id).filter(Boolean);
  const frIds = configurableRequirementItems.value.map(item => item.id);
  const defaultSelectedCalcIds = calculatorModuleItems.value
    .filter(m => m.default_selected)
    .map(m => m.id);
  return [...investmentIds, ...frIds, ...defaultSelectedCalcIds];
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
const isExpired = ref(false);

onMounted(async () => {
  const uuid = route.params.uuid;
  const result = await proposalStore.fetchPublicProposal(uuid);
  if (!result.success) {
    loadError.value = result.error;
  } else if (result.expired) {
    isExpired.value = true;
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
    // Build a price map for calculator modules so FR cards can show price badges
    const investmentSection = enabledSections.value.find(s => s.section_type === 'investment');
    const investContent = investmentSection?.content_json || {};
    const baseTotal = parseInt(String(investContent.totalInvestment || '').replace(/[^\d]/g, ''), 10) || 0;
    const calcPriceMap = {};
    for (const g of [...(content.additionalModules || []), ...groups]) {
      if (g.is_calculator_module && g.price_percent != null) {
        calcPriceMap[g.id] = Math.round(baseTotal * g.price_percent / 100);
      }
    }
    return {
      data: {
        ...content,
        groups,
        additionalModules: content.additionalModules || [],
      },
      language: proposal.value?.language || 'es',
      selectedCalculatorModules: [...selectedCalculatorModuleIds.value],
      calculatorModulePrices: calcPriceMap,
      currency: investContent.currency || proposal.value?.currency || 'COP',
    };
  }

  // For investment: inject discount data from proposal
  if (section.section_type === 'investment') {
    const investmentModules = (content.modules || []).map(m => ({ ...m, _source: 'investment' }));
    const allCalculatorItems = [...investmentModules, ...configurableRequirementItems.value, ...calculatorModuleItems.value];
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
    return {
      ...content,
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
    };
  }

  // For proposal_summary: inject proposal-level data + investment info for calculator sync
  if (section.section_type === 'proposal_summary') {
    const timelineSection = enabledSections.value.find(s => s.section_type === 'timeline');
    const timelineDuration = timelineSection?.content_json?.totalDuration || '';
    const investmentSection = enabledSections.value.find(s => s.section_type === 'investment');
    const investContent = investmentSection?.content_json || {};
    const investmentModules = (investContent.modules || []).map(m => ({ ...m, _source: 'investment' }));
    const allCalculatorItems = [...investmentModules, ...configurableRequirementItems.value, ...calculatorModuleItems.value];
    // Use proposal.total_investment as source of truth (same as investment section override)
    const summaryTotal = Number(proposal.value?.total_investment || 0);
    const formattedSummaryTotal = summaryTotal > 0
      ? '$' + summaryTotal.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
      : investContent.totalInvestment || '';
    return {
      content,
      proposal: proposal.value,
      timelineDuration,
      language: proposal.value?.language || 'es',
      proposalUuid: proposal.value?.uuid || '',
      investmentModules: allCalculatorItems,
      rawTotalInvestment: formattedSummaryTotal,
      paymentOptions: investContent.paymentOptions || [],
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


function handleViewModeSelect(mode) {
  viewMode.value = mode;
  currentIndex.value = 0;
  // Persist choice for tracking
  if (proposal.value?.uuid) {
    try {
      localStorage.setItem(`proposal-${proposal.value.uuid}-viewMode`, mode);
    } catch (_e) { /* ignore */ }
  }
  // Show welcome-back toast if returning client, otherwise start onboarding
  if (welcomeBack.value) {
    // welcomeBack was pre-loaded on mount; now that viewMode is set, it will display
    return;
  }
  nextTick(() => {
    onboardingRef.value?.start();
  });
}

function handleSwitchToDetailed() {
  viewMode.value = 'detailed';
  currentIndex.value = 0;
  window.scrollTo({ top: 0, behavior: 'auto' });
  if (proposal.value?.uuid) {
    try {
      localStorage.setItem(`proposal-${proposal.value.uuid}-viewMode`, 'detailed');
    } catch (_e) { /* ignore */ }
  }
}

function onCalculatorModulesUpdate(selectedIds) {
  if (!selectedIds) return;
  const calcModIds = calculatorModuleItems.value.map(m => m.id);
  const selected = new Set(calcModIds.filter(id => selectedIds.includes(id)));
  selectedCalculatorModuleIds.value = selected;
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
  // Initialize calculator module selection so FR section shows default_selected modules immediately
  const defaultCalcIds = calculatorModuleItems.value
    .filter(m => m.default_selected)
    .map(m => m.id);
  if (defaultCalcIds.length) {
    selectedCalculatorModuleIds.value = new Set(defaultCalcIds);
  }
  showContent.value = true;
  nextTick(() => applyProposalTheme(false));
  window.addEventListener('keydown', handleKeydown);

  // Allow bypassing gateway via URL query param (used by E2E tests and direct links)
  const queryMode = route.query.mode;
  if (queryMode === 'executive' || queryMode === 'detailed') {
    viewMode.value = queryMode;
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
