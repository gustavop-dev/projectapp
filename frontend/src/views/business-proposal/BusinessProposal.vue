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
  }

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
      scrub: 1,
      anticipatePin: 1,
      invalidateOnRefresh: true,
      end: () => `+=${getTotalScroll()}`,
    }
  });

  horizontalTweenRef.value = horizontalTween;

  ScrollTrigger.refresh();
};

onBeforeUnmount(() => {
  if (horizontalTween) {
    horizontalTween.scrollTrigger?.kill();
    horizontalTween.kill();
    horizontalTween = null;
  }

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
