<template>
  <div itemscope itemtype="https://schema.org/WebPageElement">
    <!-- Section Title -->
    <div class="text-center mb-20 lg:mb-32">
      <h2 
        ref="sectionTitleRef"
        id="technologies-title" 
        class="text-5xl lg:text-6xl font-light text-esmerald mb-6" 
        itemprop="headline"
      >
        {{ messages?.section_7?.title || '' }}
        <span class="sr-only">by Project App.</span>
      </h2>
      <p 
        ref="subtitleRef"
        class="text-xl lg:text-2xl text-green-light font-light max-w-4xl mx-auto mb-6" 
        itemprop="description"
      >
        {{ messages?.section_7?.subtitle || '' }}
      </p>
      <p 
        ref="descriptionRef"
        class="text-lg text-green-light max-w-3xl mx-auto"
      >
        {{ messages?.section_7?.description || '' }}
      </p>
    </div>

    <!-- Technologies Categories -->
    <div 
      ref="categoriesContainerRef"
      class="grid gap-12 lg:gap-16 lg:grid-cols-2" 
      v-if="messages?.section_7?.categories"
    >
      <article 
        v-for="(category, index) in messages.section_7.categories" 
        :key="index"
        class="group"
        itemscope 
        itemtype="https://schema.org/ItemList"
      >
        <!-- Category Card -->
        <div class="bg-white/5 backdrop-blur-sm border border-esmerald/20 rounded-2xl p-8 h-full transition-all duration-300 group-hover:bg-white/10 group-hover:border-esmerald/40 group-hover:transform group-hover:scale-105">
          <!-- Category Title -->
          <h3 class="text-2xl lg:text-3xl font-light text-esmerald mb-8 text-center" itemprop="name">
            {{ category.title }}
          </h3>

          <!-- Technologies Grid -->
          <div class="grid grid-cols-2 gap-4">
            <div 
              v-for="(tech, techIndex) in category.technologies" 
              :key="techIndex"
              class="technology-item group/tech"
              itemprop="itemListElement"
              itemscope 
              itemtype="https://schema.org/SoftwareApplication"
            >
              <div class="bg-esmerald/10 border border-esmerald/20 rounded-xl p-4 text-center transition-all duration-300 hover:bg-esmerald/20 hover:border-esmerald/40 hover:scale-105 cursor-pointer">
                <!-- Technology Icon/Logo placeholder -->
                <div class="w-8 h-8 mx-auto mb-3 bg-esmerald/20 rounded-lg flex items-center justify-center">
                  <span class="text-esmerald text-xs font-bold">{{ tech.charAt(0) }}</span>
                </div>
                
                <!-- Technology Name -->
                <span class="text-sm font-medium text-green-light group-hover/tech:text-esmerald transition-colors duration-300" itemprop="name">
                  {{ tech }}
                </span>
              </div>
            </div>
          </div>

          <!-- Category Description -->
          <div class="mt-6 pt-6 border-t border-esmerald/20">
            <p class="text-sm text-green-light/80 text-center">
              <span v-if="index === 0">{{ messages?.ui?.technologies?.categories_descriptions?.frontend || '' }}</span>
              <span v-else-if="index === 1">{{ messages?.ui?.technologies?.categories_descriptions?.backend || '' }}</span>
              <span v-else-if="index === 2">{{ messages?.ui?.technologies?.categories_descriptions?.databases || '' }}</span>
              <span v-else>{{ messages?.ui?.technologies?.categories_descriptions?.cloud || '' }}</span>
            </p>
          </div>
        </div>
      </article>
    </div>

    <!-- Technology Highlights -->
    <div class="mt-20 lg:mt-32">
      <div 
        ref="highlightsRef"
        class="bg-gradient-to-r from-esmerald/5 to-green-light/5 rounded-3xl p-12 lg:p-16 border border-esmerald/10"
      >
        <div class="text-center mb-12">
          <h3 class="text-3xl lg:text-4xl font-light text-esmerald mb-6">
            {{ messages?.ui?.technologies?.why_title || '' }}
          </h3>
        </div>

        <div class="grid gap-8 lg:grid-cols-3">
          <!-- Performance -->
          <div class="text-center">
            <div class="w-16 h-16 bg-esmerald/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-8 h-8 text-esmerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
            </div>
            <h4 class="text-xl font-medium text-esmerald mb-3">{{ messages?.ui?.technologies?.performance_title || '' }}</h4>
            <p class="text-green-light">{{ messages?.ui?.technologies?.performance_description || '' }}</p>
          </div>

          <!-- Scalability -->
          <div class="text-center">
            <div class="w-16 h-16 bg-esmerald/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-8 h-8 text-esmerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3"></path>
              </svg>
            </div>
            <h4 class="text-xl font-medium text-esmerald mb-3">{{ messages?.ui?.technologies?.scalability_title || '' }}</h4>
            <p class="text-green-light">{{ messages?.ui?.technologies?.scalability_description || '' }}</p>
          </div>

          <!-- Security -->
          <div class="text-center">
            <div class="w-16 h-16 bg-esmerald/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-8 h-8 text-esmerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
              </svg>
            </div>
            <h4 class="text-xl font-medium text-esmerald mb-3">{{ messages?.ui?.technologies?.security_title || '' }}</h4>
            <p class="text-green-light">{{ messages?.ui?.technologies?.security_description || '' }}</p>
          </div>
        </div>

        <!-- CTA -->
        <div class="text-center mt-12">
          <button 
            @click="$emit('openContact')"
            class="bg-esmerald text-white px-8 py-4 rounded-full text-lg font-medium transition-all duration-300 hover:bg-esmerald/90 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-esmerald/50"
          >
            {{ messages?.ui?.technologies?.cta_button || '' }}
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
  typewriter
} = useTextAnimations()

// Template refs for animations
const sectionTitleRef = ref(null)
const subtitleRef = ref(null)
const descriptionRef = ref(null)
const categoriesContainerRef = ref(null)
const highlightsRef = ref(null)

// Define emits
defineEmits(['openContact'])

// Setup animations on mount
onMounted(async () => {
  await nextTick()
  
  // Animate section title with typewriter effect
  if (sectionTitleRef.value) {
    typewriter(sectionTitleRef.value, {
      duration: 2.5,
      delay: 0.3,
      triggerStart: "top 85%"
    })
  }
  
  // Animate subtitle and description
  if (subtitleRef.value) {
    fadeInFromBottom(subtitleRef.value, {
      ...textAnimationPresets.subtitle,
      delay: 0.8
    })
  }
  
  if (descriptionRef.value) {
    fadeInFromBottom(descriptionRef.value, {
      ...textAnimationPresets.paragraph,
      delay: 1
    })
  }
  
  // Animate technology categories alternating from sides
  if (categoriesContainerRef.value) {
    const categoryCards = categoriesContainerRef.value.querySelectorAll('article')
    if (categoryCards.length > 0) {
      categoryCards.forEach((card, index) => {
        const isEven = index % 2 === 0
        const animationFunc = isEven ? fadeInFromLeft : fadeInFromRight
        
        animationFunc(card, {
          ...textAnimationPresets.card,
          delay: 1.2 + (index * 0.3),
          distance: 100,
          duration: 1
        })
        
        // Animate technology items within each card
        setTimeout(() => {
          const techItems = card.querySelectorAll('.technology-item')
          if (techItems.length > 0) {
            staggerFadeIn(techItems, {
              stagger: 0.05,
              delay: 0.3,
              from: 'bottom',
              distance: 20,
              duration: 0.4
            })
          }
        }, (1200 + (index * 300)))
      })
    }
  }
  
  // Animate highlights section
  if (highlightsRef.value) {
    const highlightTitle = highlightsRef.value.querySelector('h3')
    const highlightCards = highlightsRef.value.querySelectorAll('.text-center')
    const ctaButton = highlightsRef.value.querySelector('button')
    
    if (highlightTitle) {
      fadeInFromBottom(highlightTitle, {
        ...textAnimationPresets.sectionTitle,
        delay: 2.5
      })
    }
    
    if (highlightCards.length > 0) {
      staggerFadeIn(highlightCards, {
        ...textAnimationPresets.card,
        stagger: 0.2,
        delay: 2.8,
        from: 'bottom'
      })
    }
    
    if (ctaButton) {
      scaleIn(ctaButton, {
        ...textAnimationPresets.button,
        delay: 3.4
      })
    }
  }
})
</script>

<style scoped>
/* Technology item hover effects */
.technology-item:hover {
  transform: translateY(-2px);
}

/* Group hover effects for category cards */
.group:hover {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

/* Focus states for accessibility */
button:focus {
  outline: 2px solid theme('colors.esmerald');
  outline-offset: 2px;
}

/* Animation for technology icons */
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
}

.technology-item:hover .group\/tech div {
  animation: float 2s ease-in-out infinite;
}
</style>
