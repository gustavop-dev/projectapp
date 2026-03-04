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
    <div v-else-if="showContent && proposal" class="horizontal-scroll-wrapper">
      <!-- UX overlay elements -->
      <ProposalIndex
        :sections="enabledSections"
        :currentIndex="currentIndex"
        @navigate="handleNavigate"
      />
      <SectionCounter :current="currentIndex + 1" :total="totalSections" />
      <ExpirationBadge v-if="proposal.expires_at" :expiresAt="proposal.expires_at" />

      <!-- PDF download + Accept/Reject buttons -->
      <PdfDownloadButton :clientName="proposal.client_name" :scrollContainer="scrollContainer" />
      <ProposalResponseButtons :proposal="proposal" />

      <!-- Horizontal scroll container -->
      <div ref="scrollContainer" class="scroll-container">
        <div class="panels-wrapper">
          <div
            v-for="(section, idx) in enabledSections"
            :key="section.id"
            class="panel"
          >
            <component
              :is="sectionComponentMap[section.section_type]"
              v-bind="getSectionProps(section)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onBeforeUnmount, provide, onMounted } from 'vue';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ScrollToPlugin } from 'gsap/ScrollToPlugin';
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
  Timeline,
  Investment,
  FinalNote,
  NextSteps,
} from '~/components/BusinessProposal';
import ProposalIndex from '~/components/BusinessProposal/ProposalIndex.vue';
import SectionCounter from '~/components/BusinessProposal/SectionCounter.vue';
import ExpirationBadge from '~/components/BusinessProposal/ExpirationBadge.vue';
import ProposalExpired from '~/components/BusinessProposal/ProposalExpired.vue';
import ProposalResponseButtons from '~/components/BusinessProposal/ProposalResponseButtons.vue';
import PdfDownloadButton from '~/components/BusinessProposal/PdfDownloadButton.vue';

gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

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
  timeline: Timeline,
  investment: Investment,
  final_note: FinalNote,
  next_steps: NextSteps,
};

const proposal = computed(() => proposalStore.currentProposal);
const enabledSections = computed(() => proposalStore.enabledSections);
const totalSections = computed(() => proposalStore.totalSections);

const showContent = ref(false);
const loadError = ref(null);
const scrollContainer = ref(null);
const currentIndex = ref(0);

const horizontalTweenRef = ref(null);
provide('horizontalTweenRef', horizontalTweenRef);

let horizontalTween = null;
let panelVerticalScrollTriggers = [];
let activeScrollablePanel = null;
let panelsWrapperEl = null;
let horizontalScrollTrigger = null;
let isHorizontalLocked = false;
let lockedHorizontalScrollPos = null;
let lastIntentDeltaY = 0;
const HORIZONTAL_SCRUB_DURATION = 1;
let touchStartY = 0;

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

// --- Navigation handler ---
function handleNavigate(index) {
  if (!horizontalScrollTrigger || !panelsWrapperEl) {
    currentIndex.value = index;
    return;
  }

  const panels = Array.from(panelsWrapperEl.querySelectorAll('.panel'));
  if (!panels[index]) return;

  const totalScroll = Math.max(0, panelsWrapperEl.scrollWidth - window.innerWidth);
  if (totalScroll <= 0) return;

  // Calculate target scroll position based on panel offset
  const panelLeft = panels[index].offsetLeft;
  const progress = Math.min(panelLeft / totalScroll, 1);
  const targetWindowScroll = horizontalScrollTrigger.start
    + progress * (horizontalScrollTrigger.end - horizontalScrollTrigger.start);

  gsap.to(window, {
    scrollTo: { y: targetWindowScroll },
    duration: 0.8,
    ease: 'power2.inOut',
  });
}

// --- Horizontal scroll logic (from legacy BusinessProposal.vue) ---
const shouldConsumeVerticalScroll = (el, deltaY) => {
  if (!el) return false;
  const maxScrollTop = el.scrollHeight - el.clientHeight;
  if (maxScrollTop <= 0) return false;
  if (deltaY > 0) return el.scrollTop < maxScrollTop;
  if (deltaY < 0) return el.scrollTop > 0;
  return false;
};

const handleGlobalWheel = (e) => {
  if (!activeScrollablePanel) return;
  const deltaY = e.deltaY ?? 0;
  if (!deltaY) return;
  lastIntentDeltaY = deltaY;
  if (shouldConsumeVerticalScroll(activeScrollablePanel, deltaY)) {
    e.preventDefault();
    activeScrollablePanel.scrollTop += deltaY;
  }
};

const handleGlobalTouchStart = (e) => {
  touchStartY = e.touches?.[0]?.clientY ?? 0;
};

const handleGlobalTouchMove = (e) => {
  if (!activeScrollablePanel) return;
  const currentY = e.touches?.[0]?.clientY;
  if (typeof currentY !== 'number') return;
  const deltaY = touchStartY - currentY;
  touchStartY = currentY;
  if (!deltaY) return;
  lastIntentDeltaY = deltaY;
  if (shouldConsumeVerticalScroll(activeScrollablePanel, deltaY)) {
    e.preventDefault();
    activeScrollablePanel.scrollTop += deltaY;
  }
};

const handleGlobalScroll = () => {
  if (!isHorizontalLocked || !horizontalScrollTrigger || !activeScrollablePanel) return;
  if (lockedHorizontalScrollPos === null) return;
  if (!lastIntentDeltaY) return;
  if (!shouldConsumeVerticalScroll(activeScrollablePanel, lastIntentDeltaY)) return;
  const current = horizontalScrollTrigger.scroll();
  if (Math.abs(current - lockedHorizontalScrollPos) < 1) return;
  horizontalScrollTrigger.scroll(lockedHorizontalScrollPos);
  horizontalScrollTrigger.update();
};

const attachGlobalScrollInterceptors = () => {
  window.addEventListener('wheel', handleGlobalWheel, { passive: false });
  window.addEventListener('touchstart', handleGlobalTouchStart, { passive: true });
  window.addEventListener('touchmove', handleGlobalTouchMove, { passive: false });
  window.addEventListener('scroll', handleGlobalScroll, { passive: true });
};

const detachGlobalScrollInterceptors = () => {
  window.removeEventListener('wheel', handleGlobalWheel);
  window.removeEventListener('touchstart', handleGlobalTouchStart);
  window.removeEventListener('touchmove', handleGlobalTouchMove);
  window.removeEventListener('scroll', handleGlobalScroll);
};

const lockHorizontalToPanel = (panel) => {
  if (!horizontalScrollTrigger || !panelsWrapperEl || !panel) return;
  const totalScroll = Math.max(0, panelsWrapperEl.scrollWidth - window.innerWidth);
  if (totalScroll <= 0) return;
  const desiredScrollX = panel.offsetLeft + panel.offsetWidth / 2 - window.innerWidth / 2;
  const scrollX = Math.min(totalScroll, Math.max(0, desiredScrollX));
  const progress = scrollX / totalScroll;
  const targetScroll = horizontalScrollTrigger.start + progress * (horizontalScrollTrigger.end - horizontalScrollTrigger.start);
  horizontalScrollTrigger.scroll(targetScroll);
  horizontalScrollTrigger.update();
};

const setHorizontalScrubDuration = (duration) => {
  if (!horizontalScrollTrigger) return;
  if (typeof horizontalScrollTrigger.scrubDuration !== 'function') return;
  horizontalScrollTrigger.scrubDuration(duration);
};

const killPanelVerticalScrollTriggers = () => {
  panelVerticalScrollTriggers.forEach((t) => t.kill());
  panelVerticalScrollTriggers = [];
  activeScrollablePanel = null;
  lockedHorizontalScrollPos = null;
  lastIntentDeltaY = 0;
  setHorizontalScrubDuration(HORIZONTAL_SCRUB_DURATION);
  isHorizontalLocked = false;
};

const initPanelVerticalScroll = (containerTween) => {
  killPanelVerticalScrollTriggers();
  detachGlobalScrollInterceptors();
  if (!scrollContainer.value || !containerTween) return;

  const wrapper = scrollContainer.value.querySelector('.panels-wrapper');
  if (!wrapper) return;

  const panels = Array.from(wrapper.querySelectorAll('.panel'));
  if (panels.length === 0) return;

  panels.forEach((panel) => {
    panel.classList.remove('panel--vertical-scroll');

    const update = (isActive) => {
      const isScrollable = panel.scrollHeight > panel.clientHeight + 1;
      panel.classList.toggle('panel--vertical-scroll', Boolean(isActive && isScrollable));

      if (isActive && isScrollable) {
        activeScrollablePanel = panel;
        lockHorizontalToPanel(panel);
        setHorizontalScrubDuration(0);
        lockedHorizontalScrollPos = horizontalScrollTrigger?.scroll?.() ?? null;
        isHorizontalLocked = true;
        return;
      }

      if (activeScrollablePanel === panel) {
        activeScrollablePanel = null;
      }

      if (!activeScrollablePanel && isHorizontalLocked) {
        setHorizontalScrubDuration(HORIZONTAL_SCRUB_DURATION);
        isHorizontalLocked = false;
        lockedHorizontalScrollPos = null;
      }
    };

    const st = ScrollTrigger.create({
      trigger: panel,
      containerAnimation: containerTween,
      start: 'center center',
      end: 'right left',
      onToggle: (self) => update(self.isActive),
      onRefresh: (self) => update(self.isActive),
    });

    panelVerticalScrollTriggers.push(st);
  });
};

const onAnimationComplete = () => {
  if (loadError.value) return;
  showContent.value = true;
  nextTick(() => {
    initHorizontalScroll();
  });
};

const initHorizontalScroll = () => {
  if (!scrollContainer.value) return;

  if (horizontalTween) {
    horizontalTween.scrollTrigger?.kill();
    horizontalTween.kill();
    horizontalTween = null;
    horizontalScrollTrigger = null;
    panelsWrapperEl = null;
  }

  killPanelVerticalScrollTriggers();

  const wrapper = scrollContainer.value.querySelector('.panels-wrapper');
  if (!wrapper) return;

  const panels = Array.from(wrapper.querySelectorAll('.panel'));
  if (panels.length === 0) return;

  const getTotalScroll = () => Math.max(0, wrapper.scrollWidth - window.innerWidth);

  gsap.set(wrapper, { x: 0 });

  horizontalTween = gsap.to(wrapper, {
    x: () => -getTotalScroll(),
    ease: 'none',
    scrollTrigger: {
      trigger: scrollContainer.value,
      pin: true,
      scrub: HORIZONTAL_SCRUB_DURATION,
      anticipatePin: 1,
      invalidateOnRefresh: true,
      end: () => `+=${getTotalScroll()}`,
      onUpdate: (self) => {
        // Track current section index based on scroll progress
        const panelCount = panels.length;
        if (panelCount > 0) {
          const idx = Math.round(self.progress * (panelCount - 1));
          currentIndex.value = Math.min(idx, panelCount - 1);
        }
      },
    },
  });

  horizontalTweenRef.value = horizontalTween;
  panelsWrapperEl = wrapper;
  horizontalScrollTrigger = horizontalTween.scrollTrigger;

  initPanelVerticalScroll(horizontalTween);
  attachGlobalScrollInterceptors();

  ScrollTrigger.refresh();
};

onBeforeUnmount(() => {
  if (horizontalTween) {
    horizontalTween.scrollTrigger?.kill();
    horizontalTween.kill();
    horizontalTween = null;
  }

  killPanelVerticalScrollTriggers();
  detachGlobalScrollInterceptors();

  horizontalScrollTrigger = null;
  panelsWrapperEl = null;
  horizontalTweenRef.value = null;
});
</script>

<style scoped>
.business-proposal {
  background-color: white;
  overflow-x: hidden;
}

.horizontal-scroll-wrapper {
  opacity: 0;
  animation: fadeIn 0.8s ease-in forwards;
}

.scroll-container {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.panels-wrapper {
  display: flex;
  flex-wrap: nowrap;
  height: 100vh;
  width: max-content;
  will-change: transform;
}

.panel {
  width: 100vw;
  height: 100vh;
  flex-shrink: 0;
  overflow-y: hidden;
  overflow-x: hidden;
}

.panel--vertical-scroll {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.panel--vertical-scroll::-webkit-scrollbar {
  width: 0;
  height: 0;
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}
</style>
