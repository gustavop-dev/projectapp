<template>
  <div itemscope itemtype="https://schema.org/WebPageElement">
    <!-- Section Title -->
    <div class="text-center mb-20 lg:mb-32">
      <h2 
        ref="sectionTitleRef"
        id="why-choose-title" 
        class="text-5xl lg:text-6xl font-light text-esmerald mb-6" 
        itemprop="headline"
      >
        {{ messages?.section_8?.title || '' }}
        <span class="sr-only">Project App.</span>
      </h2>
      <p 
        ref="subtitleRef"
        class="text-xl lg:text-2xl text-green-light font-light max-w-4xl mx-auto" 
        itemprop="description"
      >
        {{ messages?.section_8?.subtitle || '' }}
      </p>
    </div>

    <!-- Reasons Grid -->
    <div 
      ref="reasonsContainerRef"
      class="grid gap-8 lg:gap-12 lg:grid-cols-2" 
      v-if="messages?.section_8?.reasons"
    >
      <article 
        v-for="(reason, index) in messages.section_8.reasons" 
        :key="index"
        class="group"
        itemscope 
        itemtype="https://schema.org/WebPageElement"
      >
        <!-- Reason Card -->
        <div class="bg-white/5 backdrop-blur-sm border border-esmerald/20 rounded-2xl p-8 h-full transition-all duration-300 group-hover:bg-white/10 group-hover:border-esmerald/40 group-hover:transform group-hover:scale-105">
          <!-- Icon & Title -->
          <div class="flex items-start mb-6">
            <div class="text-4xl mr-6 group-hover:scale-110 transition-transform duration-300 flex-shrink-0">
              {{ reason.icon }}
            </div>
            <div>
              <h3 class="text-2xl lg:text-3xl font-light text-esmerald mb-4" itemprop="name">
                {{ reason.title }}
              </h3>
              <p class="text-lg text-green-light leading-relaxed" itemprop="description">
                {{ reason.description }}
              </p>
            </div>
          </div>

          <!-- Subtle accent line -->
          <div class="w-full h-0.5 bg-gradient-to-r from-esmerald/30 via-esmerald/60 to-transparent"></div>
        </div>
      </article>
    </div>

    <!-- Stats Section -->
    <div class="mt-20 lg:mt-32">
      <div class="bg-gradient-to-r from-esmerald/10 to-green-light/10 rounded-3xl p-12 lg:p-16 border border-esmerald/10">
        <h3 class="text-3xl lg:text-4xl font-light text-esmerald mb-12 text-center">
          {{ messages?.ui?.why_choose?.track_record_title || '' }}
        </h3>

        <!-- Stats Grid -->
        <div 
          ref="statsContainerRef"
          class="grid grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12 mb-12"
        >
          <!-- Projects Completed -->
          <div class="text-center">
            <div class="stat-number text-4xl lg:text-5xl font-light text-esmerald mb-2">100+</div>
            <p class="stat-label text-green-light">{{ messages?.ui?.why_choose?.stats?.projects || '' }}</p>
          </div>

          <!-- Client Satisfaction -->
          <div class="text-center">
            <div class="stat-number text-4xl lg:text-5xl font-light text-esmerald mb-2">98%</div>
            <p class="stat-label text-green-light">{{ messages?.ui?.why_choose?.stats?.satisfaction || '' }}</p>
          </div>

          <!-- Years Experience -->
          <div class="text-center">
            <div class="stat-number text-4xl lg:text-5xl font-light text-esmerald mb-2">5+</div>
            <p class="stat-label text-green-light">{{ messages?.ui?.why_choose?.stats?.experience || '' }}</p>
          </div>

          <!-- Countries Served -->
          <div class="text-center">
            <div class="stat-number text-4xl lg:text-5xl font-light text-esmerald mb-2">15+</div>
            <p class="stat-label text-green-light">{{ messages?.ui?.why_choose?.stats?.countries || '' }}</p>
          </div>
        </div>

        <!-- Testimonial Preview -->
        <div 
          ref="testimonialRef"
          class="text-center"
        >
          <blockquote class="text-xl lg:text-2xl font-light text-green-light italic mb-6 max-w-4xl mx-auto">
            "{{ messages?.ui?.why_choose?.testimonial || '' }}"
          </blockquote>
          <cite class="text-esmerald font-medium">— {{ messages?.ui?.why_choose?.testimonial_author || '' }}</cite>
        </div>
      </div>
    </div>

    <!-- Final CTA -->
    <div class="mt-20 lg:mt-32 text-center">
      <div 
        ref="finalCtaRef"
        class="max-w-4xl mx-auto"
      >
        <h3 class="text-3xl lg:text-4xl font-light text-esmerald mb-6">
          {{ messages?.ui?.why_choose?.final_cta_title || '' }}
        </h3>
        <p class="text-lg text-green-light mb-8 max-w-2xl mx-auto">
          {{ messages?.ui?.why_choose?.final_cta_description || '' }}
        </p>
        
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <button 
            @click="$emit('openContact')"
            class="bg-esmerald text-white px-8 py-4 rounded-full text-lg font-medium transition-all duration-300 hover:bg-esmerald/90 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-esmerald/50"
          >
            {{ messages?.ui?.why_choose?.start_button || '' }}
          </button>
          <button 
            @click="$emit('viewPortfolio')"
            class="bg-transparent border-2 border-esmerald text-esmerald px-8 py-4 rounded-full text-lg font-medium transition-all duration-300 hover:bg-esmerald hover:text-white hover:scale-105 focus:outline-none focus:ring-2 focus:ring-esmerald/50"
          >
            {{ messages?.ui?.why_choose?.see_work_button || '' }}
          </button>
        </div>

        <!-- Contact Information -->
        <div class="mt-12 pt-8 border-t border-esmerald/20">
          <p class="text-green-light mb-4">
            {{ messages?.ui?.why_choose?.contact_description || '' }}
          </p>
          <div class="flex flex-col sm:flex-row gap-4 justify-center items-center text-esmerald">
            <a href="mailto:team@projectapp.co" class="hover:text-green-light transition-colors duration-300">
              team@projectapp.co
            </a>
            <span class="hidden sm:inline text-green-light">|</span>
            <a href="https://projectapp.co" class="hover:text-green-light transition-colors duration-300">
              projectapp.co
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useMessages } from '~/composables/useMessages'
import { useTextAnimations, textAnimationPresets } from '~/composables/useTextAnimations'

const { messages } = useMessages()

// Animation composable
const {
  fadeInFromBottom,
  fadeInFromLeft,
  fadeInFromRight,
  staggerFadeIn,
  scaleIn,
  counterAnimation,
  wordReveal
} = useTextAnimations()

// Template refs for animations
const sectionTitleRef = ref(null)
const subtitleRef = ref(null)
const reasonsContainerRef = ref(null)
const statsContainerRef = ref(null)
const testimonialRef = ref(null)
const finalCtaRef = ref(null)

// Define emits
defineEmits(['openContact', 'viewPortfolio'])

// Setup animations on mount
onMounted(async () => {
  await nextTick()
  
  // Animate section title with word reveal
  if (sectionTitleRef.value) {
    wordReveal(sectionTitleRef.value, {
      ...textAnimationPresets.sectionTitle,
      stagger: 0.08,
      duration: 1.5
    })
  }
  
  // Animate subtitle
  if (subtitleRef.value) {
    fadeInFromBottom(subtitleRef.value, textAnimationPresets.subtitle)
  }
  
  // Animate reason cards with stagger from different directions
  if (reasonsContainerRef.value) {
    const reasonCards = reasonsContainerRef.value.querySelectorAll('article')
    if (reasonCards.length > 0) {
      // Animate cards alternating from left and right
      reasonCards.forEach((card, index) => {
        const isEven = index % 2 === 0
        const animationFunc = isEven ? fadeInFromLeft : fadeInFromRight
        
        animationFunc(card, {
          ...textAnimationPresets.card,
          delay: 0.4 + (index * 0.1),
          distance: 60
        })
      })
    }
  }
  
  // Animate statistics with counter effect
  if (statsContainerRef.value) {
    const statNumbers = statsContainerRef.value.querySelectorAll('.stat-number')
    const statLabels = statsContainerRef.value.querySelectorAll('.stat-label')
    
    // Animate stat numbers with counter
    statNumbers.forEach((statElement, index) => {
      const originalText = statElement.textContent
      let targetValue = 100
      let suffix = '+'
      let prefix = ''
      
      // Extract number and suffix from text
      if (originalText.includes('%')) {
        targetValue = parseInt(originalText)
        suffix = '%'
      } else if (originalText.includes('+')) {
        targetValue = parseInt(originalText)
        suffix = '+'
      }
      
      counterAnimation(statElement, {
        targetValue,
        suffix,
        prefix,
        duration: 2,
        delay: 0.8 + (index * 0.1),
        triggerStart: "top 85%"
      })
    })
    
    // Animate stat labels
    if (statLabels.length > 0) {
      staggerFadeIn(statLabels, {
        ...textAnimationPresets.paragraph,
        stagger: 0.1,
        delay: 1.2,
        from: 'bottom'
      })
    }
  }
  
  // Animate testimonial
  if (testimonialRef.value) {
    fadeInFromBottom(testimonialRef.value, {
      ...textAnimationPresets.paragraph,
      delay: 1.5,
      duration: 1.2
    })
  }
  
  // Animate final CTA section
  if (finalCtaRef.value) {
    const ctaTitle = finalCtaRef.value.querySelector('h3')
    const ctaDescription = finalCtaRef.value.querySelector('p')
    const ctaButtons = finalCtaRef.value.querySelectorAll('button')
    
    if (ctaTitle) fadeInFromBottom(ctaTitle, { ...textAnimationPresets.sectionTitle, delay: 1.8 })
    if (ctaDescription) fadeInFromBottom(ctaDescription, { ...textAnimationPresets.paragraph, delay: 2 })
    if (ctaButtons.length > 0) {
      staggerFadeIn(ctaButtons, {
        ...textAnimationPresets.button,
        stagger: 0.1,
        delay: 2.2,
        from: 'bottom'
      })
    }
  }
})
</script>

<style scoped>
/* Enhanced hover effects for reason cards */
.group:hover {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

/* Icon animation on hover */
.group:hover .group-hover\:scale-110 {
  transform: scale(1.1);
}

/* Focus states for accessibility */
button:focus, a:focus {
  outline: 2px solid theme('colors.esmerald');
  outline-offset: 2px;
}

/* Stats animation */
@keyframes countUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.text-4xl, .text-5xl {
  animation: countUp 0.8s ease-out;
}

/* Gradient line animation */
@keyframes gradient-slide {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.bg-gradient-to-r {
  background-size: 200% 200%;
  animation: gradient-slide 6s ease infinite;
}
</style>
