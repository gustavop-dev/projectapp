<template>
  <div class="business-proposal bg-white">
    <PreloaderAnimation 
      :active="true" 
      @animationComplete="onAnimationComplete"
    />
    
    <div v-if="showContent" class="horizontal-scroll-wrapper">
      <div ref="scrollContainer" class="scroll-container">
        <div class="panels-wrapper">
          <div class="panel">
            <Greeting :clientName="clientName" />
          </div>
          <div class="panel">
            <ExecutiveSummary />
          </div>
          <div class="panel">
            <ContextDiagnostic />
          </div>
          <div class="panel">
            <ConversionStrategy />
          </div>
          <div class="panel">
            <DesignUX />
          </div>
          <div class="panel">
            <CreativeSupport />
          </div>
          <div class="panel panel--wide">
            <DevelopmentStages />
          </div>
          <div class="panel">
            <FunctionalRequirements />
          </div>
          <div class="panel">
            <Timeline />
          </div>
          <div class="panel">
            <Investment />
          </div>
          <div class="panel">
            <FinalNote />
          </div>
          <div class="panel">
            <NextSteps />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onBeforeUnmount, provide } from 'vue';
import { useRoute } from 'vue-router';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import PreloaderAnimation from '@/components/animations/PreloaderAnimation.vue';
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
  NextSteps
} from '@/components/BusinessProposal';

gsap.registerPlugin(ScrollTrigger);

const route = useRoute();
const clientSlug = computed(() => route.params.slug || 'juan-pablo');

const clientName = computed(() => {
  const slug = clientSlug.value;
  return slug.split('-').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');
});

const showContent = ref(false);
const scrollContainer = ref(null);

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
    }
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

.panel--wide {
  width: auto;
  min-width: 100vw;
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}
</style>
