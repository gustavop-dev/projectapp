<template>
  <div itemscope itemtype="https://schema.org/Service">
    <!-- Section Title -->
    <div class="text-center mb-20 lg:mb-32">
      <h2 
        ref="sectionTitleRef"
        id="detailed-services-title" 
        class="text-5xl lg:text-6xl font-light text-esmerald mb-6" 
        itemprop="name"
      >
        {{ messages?.section_5?.title || '' }}
        <span class="sr-only">by Project App.</span>
      </h2>
      <p 
        ref="subtitleRef"
        class="text-xl lg:text-2xl text-green-light font-light max-w-4xl mx-auto" 
        itemprop="description"
      >
        {{ messages?.section_5?.subtitle || '' }}
      </p>
    </div>

    <!-- Services Grid -->
    <div 
      ref="servicesContainerRef"
      class="grid gap-12 lg:gap-16 lg:grid-cols-2" 
      v-if="messages?.section_5?.services"
    >
      <article 
        v-for="(service, index) in messages.section_5.services" 
        :key="index"
        class="group"
        itemscope 
        itemtype="https://schema.org/Service"
      >
        <!-- Service Card -->
        <div class="h-full">
          <!-- Icon & Title -->
          <div class="mb-8">
            <div class="text-6xl mb-6 group-hover:scale-110 transition-transform duration-300">
              {{ service.icon }}
            </div>
            <h3 class="text-3xl lg:text-4xl font-light text-esmerald mb-4" itemprop="name">
              {{ service.title }}
            </h3>
            <p class="text-lg text-green-light leading-relaxed" itemprop="description">
              {{ service.description }}
            </p>
          </div>

          <!-- Features List -->
          <div class="mb-8">
            <h4 class="text-lg font-medium text-esmerald mb-4">{{ messages?.ui?.detailed_services?.features_title || '' }}</h4>
            <ul class="space-y-3">
              <li 
                v-for="feature in service.features" 
                :key="feature"
                class="flex items-center text-green-light"
              >
                <svg class="w-5 h-5 text-esmerald mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                </svg>
                {{ feature }}
              </li>
            </ul>
          </div>

          <!-- CTA Button -->
          <button 
            @click="$emit('openContact', service.title)"
            class="w-full bg-transparent border-2 border-esmerald text-esmerald px-6 py-3 rounded-full font-medium transition-all duration-300 hover:bg-esmerald hover:text-white hover:scale-105 focus:outline-none focus:ring-2 focus:ring-esmerald/50"
          >
            {{ messages?.ui?.detailed_services?.learn_more || '' }} {{ service.title }}
          </button>
        </div>
      </article>
    </div>

    <!-- Bottom CTA Section -->
    <div class="mt-20 lg:mt-32 text-center">
      <div 
        ref="ctaSectionRef"
        class="bg-gradient-to-r from-esmerald/10 to-green-light/10 rounded-3xl p-12 lg:p-16"
      >
        <h3 class="text-3xl lg:text-4xl font-light text-esmerald mb-6">
          {{ messages?.ui?.detailed_services?.custom_solution_title || '' }}
        </h3>
        <p class="text-lg text-green-light mb-8 max-w-3xl mx-auto">
          {{ messages?.ui?.detailed_services?.custom_solution_description || '' }}
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <button 
            @click="$emit('openContact')"
            class="bg-esmerald text-white px-8 py-4 rounded-full text-lg font-medium transition-all duration-300 hover:bg-esmerald/90 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-esmerald/50"
          >
            {{ messages?.ui?.detailed_services?.discuss_button || '' }}
          </button>
          <button 
            @click="$emit('viewPortfolio')"
            class="bg-transparent border-2 border-esmerald text-esmerald px-8 py-4 rounded-full text-lg font-medium transition-all duration-300 hover:bg-esmerald hover:text-white hover:scale-105 focus:outline-none focus:ring-2 focus:ring-esmerald/50"
          >
            {{ messages?.ui?.detailed_services?.view_work_button || '' }}
          </button>
        </div>
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
const {
  fadeInFromBottom,
  fadeInFromLeft,
  fadeInFromRight,
  staggerFadeIn,
  scaleIn,
  wordReveal
} = useTextAnimations()

// Template refs for animations
const sectionTitleRef = ref(null)
const subtitleRef = ref(null)
const servicesContainerRef = ref(null)
const ctaSectionRef = ref(null)

// Define emits
defineEmits(['openContact', 'viewPortfolio'])

// Setup animations on mount
onMounted(async () => {
  await nextTick()
  
  // Animate section title with word reveal
  if (sectionTitleRef.value) {
    wordReveal(sectionTitleRef.value, {
      ...textAnimationPresets.sectionTitle,
      stagger: 0.06,
      duration: 1.5
    })
  }
  
  // Animate subtitle
  if (subtitleRef.value) {
    fadeInFromBottom(subtitleRef.value, textAnimationPresets.subtitle)
  }
  
  // Animate service cards alternating from left and right
  if (servicesContainerRef.value) {
    const serviceCards = servicesContainerRef.value.querySelectorAll('article')
    if (serviceCards.length > 0) {
      serviceCards.forEach((card, index) => {
        const isEven = index % 2 === 0
        const animationFunc = isEven ? fadeInFromLeft : fadeInFromRight
        
        animationFunc(card, {
          ...textAnimationPresets.card,
          delay: 0.4 + (index * 0.2),
          distance: 80,
          duration: 0.8
        })
      })
    }
  }
  
  // Animate CTA section elements
  if (ctaSectionRef.value) {
    const ctaTitle = ctaSectionRef.value.querySelector('h3')
    const ctaDescription = ctaSectionRef.value.querySelector('p')
    const ctaButtons = ctaSectionRef.value.querySelectorAll('button')
    
    if (ctaTitle) fadeInFromBottom(ctaTitle, { ...textAnimationPresets.sectionTitle, delay: 1.2 })
    if (ctaDescription) fadeInFromBottom(ctaDescription, { ...textAnimationPresets.paragraph, delay: 1.4 })
    if (ctaButtons.length > 0) {
      staggerFadeIn(ctaButtons, {
        ...textAnimationPresets.button,
        stagger: 0.15,
        delay: 1.6,
        from: 'bottom'
      })
    }
  }
})
</script>

<style scoped>
/* Enhanced hover effects for service cards */
.group:hover {
  transform: translateY(-4px);
  transition: transform 0.3s ease;
}

/* Smooth icon animations */
.group:hover .group-hover\:scale-110 {
  transform: scale(1.1);
}

/* Focus states for accessibility */
button:focus {
  outline: 2px solid theme('colors.esmerald');
  outline-offset: 2px;
}
</style>
