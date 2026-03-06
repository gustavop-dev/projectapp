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
        <p class="text-gray-500">Esta propuesta no fue encontrada.</p>
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
      <!-- UX overlay elements -->
      <ProposalIndex
        :sections="displayPanels"
        :currentIndex="currentIndex"
        @navigate="handleNavigate"
        @update:open="(val) => indexOpen = val"
      />
      <SectionCounter :current="currentIndex + 1" :total="totalSections" />
      <ExpirationBadge v-if="proposal.expires_at" :expiresAt="proposal.expires_at" />

      <!-- PDF download -->
      <PdfDownloadButton />

      <!-- Side navigation arrows (fixed, outside transition) -->
      <SectionNavButtons
        :prevTitle="prevPanelTitle"
        :nextTitle="nextPanelTitle"
        :isFirst="currentIndex === 0"
        :isLast="currentIndex === totalSections - 1"
        :hideLeft="indexOpen"
        @prev="goPrev"
        @next="goNext"
      />

      <!-- Single-panel view with transition -->
      <Transition :name="transitionName" mode="out-in">
        <div :key="currentPanel.id" class="panel-container">
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
          />
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, onMounted } from 'vue';
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
} from '~/components/BusinessProposal';
import ProposalIndex from '~/components/BusinessProposal/ProposalIndex.vue';
import SectionCounter from '~/components/BusinessProposal/SectionCounter.vue';
import ExpirationBadge from '~/components/BusinessProposal/ExpirationBadge.vue';
import ProposalExpired from '~/components/BusinessProposal/ProposalExpired.vue';
import PdfDownloadButton from '~/components/BusinessProposal/PdfDownloadButton.vue';
import RawContentSection from '~/components/BusinessProposal/RawContentSection.vue';
import ProposalClosing from '~/components/BusinessProposal/ProposalClosing.vue';
import SectionNavButtons from '~/components/BusinessProposal/SectionNavButtons.vue';

definePageMeta({ layout: false });

const route = useRoute();
const proposalStore = useProposalStore();

const sectionComponentMap = {
  greeting: Greeting,
  executive_summary: ExecutiveSummary,
  context_diagnostic: ContextDiagnostic,
  conversion_strategy: ConversionStrategy,
  design_ux: DesignUX,
  creative_support: CreativeSupport,
  development_stages: DevelopmentStages,
  functional_requirements: FunctionalRequirements,
  functional_requirements_group: FunctionalRequirementsGroup,
  timeline: Timeline,
  investment: Investment,
  final_note: FinalNote,
  next_steps: NextSteps,
  proposal_closing: ProposalClosing,
};

const proposal = computed(() => proposalStore.currentProposal);
const enabledSections = computed(() => proposalStore.enabledSections);

// Expand functional_requirements into intro + individual group panels
const displayPanels = computed(() => {
  const panels = [];
  for (const section of enabledSections.value) {
    if (section.section_type === 'functional_requirements') {
      // 1) Intro panel (overview)
      panels.push(section);
      // 2) One panel per group
      const content = section.content_json || {};
      let groups = content.groups || [];
      if (!groups.length) {
        const legacyGroups = proposal.value?.requirement_groups || [];
        groups = legacyGroups.map((g) => ({
          id: g.group_id,
          icon: g.title?.trim().split(' ')[0] || '🧩',
          title: g.title?.trim().split(' ').slice(1).join(' ') || g.title,
          description: g.description,
          items: (g.items || []).map((item) => ({
            icon: item.icon, name: item.name, description: item.description,
          })),
        }));
      }
      const additional = content.additionalModules || [];
      const allGroups = [...groups, ...additional].filter(g => g && (g.title || g.items?.length));
      const parentIndex = content.index || '7';
      allGroups.forEach((group, gIdx) => {
        panels.push({
          id: `${section.id}_group_${gIdx}`,
          section_type: 'functional_requirements_group',
          title: `${group.icon || '🧩'} ${group.title}`,
          _group: group,
          _subIndex: `${parentIndex}.${gIdx + 1}`,
        });
      });
    } else {
      panels.push(section);
    }
  }

  // Add closing panel (validity, thank-you, accept/reject) after all sections
  const finalNote = enabledSections.value.find(s => s.section_type === 'final_note');
  const fnContent = finalNote?.content_json || {};
  panels.push({
    id: 'proposal_closing',
    section_type: 'proposal_closing',
    title: '🤝 Cierre',
    _validityMessage: fnContent.validityMessage || '',
    _thankYouMessage: fnContent.thankYouMessage || '',
  });

  return panels;
});

const totalSections = computed(() => displayPanels.value.length);

const showContent = ref(false);
const loadError = ref(null);
const proposalContainer = ref(null);
const currentIndex = ref(0);
const transitionName = ref('slide-left');
const indexOpen = ref(false);

// Current panel and neighbors
const currentPanel = computed(() => displayPanels.value[currentIndex.value] || displayPanels.value[0]);
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
    };
  }

  if (section.section_type === 'greeting') {
    return {
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

  if (section.section_type === 'functional_requirements_group') {
    return {
      group: section._group,
      subIndex: section._subIndex,
    };
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
    };
  }

  // For development_stages, timeline, investment, final_note, next_steps
  // Spread content_json as individual props
  return content;
}

function isPastePanel(panel) {
  if (panel.section_type === 'functional_requirements_group') {
    return panel._group?._editMode === 'paste' && panel._group?.rawText;
  }
  return panel.content_json?._editMode === 'paste' && panel.content_json?.rawText;
}

function getPastePanelTitle(panel) {
  if (panel.section_type === 'functional_requirements_group') {
    return panel._group?.title || panel.title;
  }
  return panel.content_json?.title || panel.title;
}

function getPastePanelIndex(panel) {
  if (panel.section_type === 'functional_requirements_group') {
    return panel._subIndex || '';
  }
  return panel.content_json?.index || '';
}

function getPastePanelRawText(panel) {
  if (panel.section_type === 'functional_requirements_group') {
    return panel._group?.rawText || '';
  }
  return panel.content_json?.rawText || '';
}

// --- Navigation ---
function navigateTo(index) {
  if (index < 0 || index >= totalSections.value) return;
  transitionName.value = index > currentIndex.value ? 'slide-left' : 'slide-right';
  currentIndex.value = index;
  window.scrollTo({ top: 0, behavior: 'auto' });
}

function handleNavigate(index) {
  navigateTo(index);
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
  window.addEventListener('keydown', handleKeydown);
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

/* Slide left (navigating forward) */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: transform 0.35s ease;
}
.slide-left-enter-from {
  transform: translateX(60px);
}
.slide-left-leave-to {
  transform: translateX(-60px);
}

/* Slide right (navigating backward) */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.35s ease;
}
.slide-right-enter-from {
  transform: translateX(-60px);
}
.slide-right-leave-to {
  transform: translateX(60px);
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}
</style>
