<template>
  <div itemscope itemtype="https://schema.org/WebPageElement">
    <!-- Section Title -->
    <div class="text-center mb-20 lg:mb-32">
      <h2 
        ref="sectionTitleRef"
        id="process-title" 
        class="text-5xl lg:text-6xl font-light text-esmerald mb-6" 
        itemprop="headline"
      >
        {{ messages?.section_6?.title || '' }}
        <span class="sr-only">by Project App.</span>
      </h2>
      <p 
        ref="subtitleRef"
        class="text-xl lg:text-2xl text-green-light font-light max-w-4xl mx-auto mb-6" 
        itemprop="description"
      >
        {{ messages?.section_6?.subtitle || '' }}
      </p>
      <p 
        ref="descriptionRef"
        class="text-lg text-green-light max-w-3xl mx-auto"
      >
        {{ messages?.section_6?.description || '' }}
      </p>
    </div>

    <!-- Process Steps -->
    <div class="relative" v-if="messages?.section_6?.steps">
      <!-- Process Line (hidden on mobile) -->
      <div class="hidden lg:block absolute left-1/2 transform -translate-x-1/2 w-0.5 bg-gradient-to-b from-esmerald/30 via-esmerald/60 to-esmerald/30 h-full"></div>
      
      <!-- Steps Grid -->
      <div 
        ref="stepsContainerRef"
        class="space-y-16 lg:space-y-24"
      >
        <article 
          v-for="(step, index) in messages.section_6.steps" 
          :key="index"
          class="group"
          itemscope 
          itemtype="https://schema.org/HowToStep"
        >
          <div class="grid lg:grid-cols-2 gap-8 lg:gap-16 items-center">
            <!-- Step Content (Left on even, Right on odd for desktop) -->
            <div :class="index % 2 === 0 ? 'lg:order-1' : 'lg:order-2'">
              <div class="bg-white/5 backdrop-blur-sm border border-esmerald/20 rounded-2xl p-8 transition-all duration-300 group-hover:bg-white/10 group-hover:border-esmerald/40">
                <!-- Step Number -->
                <div class="flex items-center mb-6">
                  <span class="text-3xl lg:text-4xl font-light text-esmerald bg-esmerald/10 rounded-full w-16 h-16 lg:w-20 lg:h-20 flex items-center justify-center mr-4" itemprop="position">
                    {{ step.number }}
                  </span>
                  <h3 class="text-2xl lg:text-3xl font-light text-esmerald" itemprop="name">
                    {{ step.title }}
                  </h3>
                </div>

                <!-- Step Description -->
                <p class="text-lg text-green-light leading-relaxed mb-6" itemprop="text">
                  {{ step.description }}
                </p>

                <!-- Duration -->
                <div class="flex items-center text-esmerald">
                  <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  <span class="text-sm font-medium">{{ messages?.ui?.process?.duration_label || '' }} {{ step.duration }}</span>
                </div>
              </div>
            </div>

            <!-- Step Visual (Right on even, Left on odd for desktop) -->
            <div :class="index % 2 === 0 ? 'lg:order-2' : 'lg:order-1'" class="relative">
              <!-- Central Circle for desktop -->
              <div class="hidden lg:flex absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 w-4 h-4 bg-esmerald rounded-full border-4 border-white z-10"></div>
              
              <!-- Step Illustration -->
              <div class="flex justify-center">
                <div class="w-48 h-48 lg:w-64 lg:h-64 bg-gradient-to-br from-esmerald/20 to-green-light/20 rounded-full flex items-center justify-center transition-all duration-300 group-hover:scale-105">
                  <!-- Step Icon -->
                  <div class="text-6xl lg:text-7xl opacity-50 group-hover:opacity-70 transition-opacity duration-300">
                    <!-- Dynamic icons based on step -->
                    <span v-if="index === 0">🔍</span>
                    <span v-else-if="index === 1">🎨</span>
                    <span v-else-if="index === 2">⚙️</span>
                    <span v-else>🚀</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </article>
      </div>
    </div>

    <!-- Bottom CTA -->
    <div class="mt-20 lg:mt-32 text-center">
      <div 
        ref="ctaSectionRef"
        class="bg-gradient-to-r from-esmerald/5 to-green-light/5 rounded-3xl p-12 lg:p-16 border border-esmerald/10"
      >
        <h3 class="text-3xl lg:text-4xl font-light text-esmerald mb-6">
          {{ messages?.ui?.process?.cta_title || '' }}
        </h3>
        <p class="text-lg text-green-light mb-8 max-w-2xl mx-auto">
          {{ messages?.ui?.process?.cta_description || '' }}
        </p>
        <button 
          @click="$emit('openContact')"
          class="bg-esmerald text-white px-8 py-4 rounded-full text-lg font-medium transition-all duration-300 hover:bg-esmerald/90 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-esmerald/50"
        >
          {{ messages?.ui?.process?.cta_button || '' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useMessages } from '@/composables/useMessages'
import { useTextAnimations, textAnimationPresets } from '@/composables/useTextAnimations'

const { messages } = useMessages()

// Animation composable
const { fadeInFromBottom, staggerFadeIn, scaleIn } = useTextAnimations()

// Template refs
const sectionTitleRef = ref(null)
const subtitleRef = ref(null)
const descriptionRef = ref(null)
const stepsContainerRef = ref(null)
const ctaSectionRef = ref(null)

// Define emits
defineEmits(['openContact'])

// Setup animations
onMounted(async () => {
  await nextTick()
  
  if (sectionTitleRef.value) fadeInFromBottom(sectionTitleRef.value, textAnimationPresets.sectionTitle)
  if (subtitleRef.value) fadeInFromBottom(subtitleRef.value, textAnimationPresets.subtitle)
  if (descriptionRef.value) fadeInFromBottom(descriptionRef.value, textAnimationPresets.paragraph)
  
  if (stepsContainerRef.value) {
    const stepCards = stepsContainerRef.value.querySelectorAll('article')
    if (stepCards.length > 0) {
      staggerFadeIn(stepCards, {
        ...textAnimationPresets.card,
        stagger: 0.3,
        delay: 0.6,
        from: 'bottom'
      })
    }
  }
  
  if (ctaSectionRef.value) {
    const ctaElements = ctaSectionRef.value.querySelectorAll('h3, p, button')
    if (ctaElements.length > 0) {
      staggerFadeIn(ctaElements, {
        stagger: 0.2,
        delay: 1.2,
        from: 'bottom'
      })
    }
  }
})
</script>

<style scoped>
/* Smooth animations for step cards */
.group:hover {
  transform: translateY(-2px);
  transition: transform 0.3s ease;
}

/* Enhanced focus states */
button:focus {
  outline: 2px solid theme('colors.esmerald');
  outline-offset: 2px;
}

/* Process line gradient animation */
@keyframes pulse-line {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

.process-line {
  animation: pulse-line 3s ease-in-out infinite;
}
</style>
