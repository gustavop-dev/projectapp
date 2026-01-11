<template>
  <div class="overflow-hidden" itemscope itemtype="https://schema.org/WebPageElement">
    <!-- Section Title -->
    <div class="px-3 lg:px-32 mb-16 lg:mb-24">
      <div class="text-center lg:text-left">
        <h2 
          ref="sectionTitleRef"
          id="success-stories-title" 
          class="text-5xl lg:text-7xl font-light text-esmerald leading-tight" 
          itemprop="headline"
        >
          <span class="block">{{ messages?.section_4?.title || '' }}</span>
          <span class="block relative">
            {{ messages?.section_4?.subtitle || '' }}
            <div class="absolute -bottom-2 left-0 w-full h-3 bg-gradient-to-r from-pink-300/60 via-purple-300/60 to-blue-300/60 rounded-full transform -skew-y-1"></div>
          </span>
        </h2>
        <p 
          ref="descriptionRef"
          class="text-xl lg:text-2xl text-green-light mt-8 max-w-2xl lg:max-w-none"
        >
          {{ messages?.section_4?.description || '' }}
        </p>
      </div>
    </div>

    <!-- Project Selector -->
    <div class="px-3 lg:px-32 mb-8 lg:mb-12">
      <div class="flex justify-center gap-4">
        <button
          v-for="(project, index) in messages?.section_4?.projects || []"
          :key="index"
          @click="goToProject(index)"
          :class="[
            'px-6 py-3 rounded-full text-sm font-medium transition-all duration-300 border-2',
            index === activeProjectIndex 
              ? 'bg-esmerald text-white border-esmerald shadow-lg' 
              : 'bg-transparent text-esmerald border-esmerald/50 hover:border-esmerald hover:bg-esmerald/10'
          ]"
        >
          {{ project.client }}
        </button>
      </div>
    </div>

    <!-- Horizontal Scroll Container -->
    <div 
      ref="horizontalScrollContainer"
      class="relative overflow-hidden"
    >
      <!-- Projects Track -->
      <div 
        ref="projectsTrack"
        class="flex no-scrollbar"
        style="width: fit-content; will-change: transform;"
      >
        <!-- Project Card -->
        <article 
          v-for="(project, index) in messages?.section_4?.projects" 
          :key="index"
          ref="projectCards"
          class="flex-shrink-0 w-screen bg-white/5 backdrop-blur-sm border border-esmerald/20 p-8 lg:p-12"
          itemscope 
          itemtype="https://schema.org/CreativeWork"
        >
          <div class="max-w-7xl mx-auto grid lg:grid-cols-5 gap-8 lg:gap-12 items-center h-full">
            
            <!-- Project Content -->
            <div class="lg:col-span-2 space-y-6 lg:space-y-8">
              <!-- Client Title with Industry -->
              <div>
                <h3 class="text-4xl lg:text-6xl font-light text-esmerald mb-4" itemprop="name">
                  {{ project.client }}
                </h3>
                <div class="relative inline-block">
                  <p class="text-lg lg:text-xl text-green-light">
                    <span class="font-medium">{{ messages?.ui?.success_stories?.industry_label || 'Industry:' }}</span>
                    {{ project.industry }}
                  </p>
                  <div class="absolute -bottom-1 left-0 w-full h-2 bg-gradient-to-r from-green-300/50 to-teal-300/50 rounded-full"></div>
                </div>
              </div>

              <!-- Challenge -->
              <div>
                <h4 class="text-xl lg:text-2xl font-medium text-esmerald mb-3 relative">
                  {{ messages?.ui?.success_stories?.challenge_label || 'The Challenge:' }}
                  <div class="absolute -bottom-1 left-0 w-20 h-1 bg-gradient-to-r from-yellow-300/70 to-orange-300/70 rounded-full"></div>
                </h4>
                <p class="text-green-light leading-relaxed">{{ project.challenge }}</p>
              </div>

              <!-- What They Wanted -->
              <div>
                <h4 class="text-xl lg:text-2xl font-medium text-esmerald mb-3 relative">
                  {{ messages?.ui?.success_stories?.what_they_wanted_label || 'What They Wanted:' }}
                  <div class="absolute -bottom-1 left-0 w-24 h-1 bg-gradient-to-r from-purple-300/70 to-pink-300/70 rounded-full"></div>
                </h4>
                <p class="text-green-light leading-relaxed">{{ project.what_they_wanted }}</p>
              </div>

              <!-- Our Solution -->
              <div>
                <h4 class="text-xl lg:text-2xl font-medium text-esmerald mb-3 relative">
                  {{ messages?.ui?.success_stories?.our_solution_label || 'Our Solution:' }}
                  <div class="absolute -bottom-1 left-0 w-28 h-1 bg-gradient-to-r from-blue-300/70 to-cyan-300/70 rounded-full"></div>
                </h4>
                <p class="text-green-light leading-relaxed">{{ project.our_solution }}</p>
              </div>

              <!-- Technologies -->
              <div>
                <h4 class="text-lg font-medium text-esmerald mb-3">
                  {{ messages?.ui?.success_stories?.technologies_label || 'Technologies Used:' }}
                </h4>
                <div class="flex flex-wrap gap-2">
                  <span 
                    v-for="tech in project.technologies" 
                    :key="tech"
                    class="px-4 py-2 bg-gradient-to-r from-esmerald/20 to-green-light/20 text-esmerald text-sm rounded-full border border-esmerald/30"
                  >
                    {{ tech }}
                  </span>
                </div>
              </div>

              <!-- Action Buttons -->
              <div class="flex flex-col sm:flex-row gap-4 pt-4">
                <a 
                  :href="project.website_url" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  class="bg-esmerald text-white px-6 py-3 rounded-full text-lg font-medium transition-all duration-300 hover:bg-esmerald/90 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-esmerald/50 text-center"
                >
                  {{ project.view_site_text }}
                </a>
                <button 
                  @click="$emit('viewMoreProjects')"
                  class="bg-transparent border-2 border-esmerald text-esmerald px-6 py-3 rounded-full text-lg font-medium transition-all duration-300 hover:bg-esmerald hover:text-white hover:scale-105 focus:outline-none focus:ring-2 focus:ring-esmerald/50"
                >
                  {{ messages?.ui?.success_stories?.view_more_projects || 'View More Projects' }}
                </button>
              </div>
            </div>

            <!-- Project Media -->
            <div class="relative lg:col-span-3 lg:order-2">
              <div class="aspect-video bg-gradient-to-br from-esmerald/20 to-green-light/20 rounded-2xl overflow-hidden border border-esmerald/30">
                
                <!-- Video -->
                <video 
                  v-if="project.media_type === 'video'"
                  :src="`/src/assets/projects_resources/${project.media_file}`"
                  autoplay
                  muted
                  loop
                  playsinline
                  class="w-full h-full object-cover"
                  :alt="`${project.client} project showcase`"
                />
                
                <!-- Image -->
                <img 
                  v-else
                  :src="`/src/assets/projects_resources/${project.media_file}`"
                  :alt="`${project.client} project showcase`"
                  class="w-full h-full object-cover transition-transform duration-700 hover:scale-110"
                  loading="lazy"
                />
              </div>
            </div>

          </div>
        </article>
      </div>
    </div>

    

    <!-- Final CTA -->
    <div 
      ref="ctaSectionRef"
      class="text-center mt-20 lg:mt-32 px-3 lg:px-32"
    >
      <h3 class="text-3xl lg:text-4xl font-light text-esmerald mb-6">
        {{ messages?.ui?.success_stories?.cta_title || '' }}
      </h3>
      <p class="text-lg text-green-light mb-8 max-w-2xl mx-auto">
        {{ messages?.ui?.success_stories?.cta_description || '' }}
      </p>
      <button 
        @click="$emit('openContact')"
        class="bg-esmerald text-white px-8 py-4 rounded-full text-lg font-medium transition-all duration-300 hover:bg-esmerald/90 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-esmerald/50"
      >
        {{ messages?.ui?.success_stories?.cta_button || '' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useMessages } from '@/composables/useMessages'
import { useTextAnimations, textAnimationPresets } from '@/composables/useTextAnimations'

gsap.registerPlugin(ScrollTrigger)

const { messages } = useMessages()

// Animation composable
const {
  fadeInFromBottom,
  staggerFadeIn,
  scaleIn
} = useTextAnimations()

// Template refs
const sectionTitleRef = ref(null)
const descriptionRef = ref(null)
const horizontalScrollContainer = ref(null)
const projectsTrack = ref(null)
const projectCards = ref([])
const ctaSectionRef = ref(null)

// State
const activeProjectIndex = ref(0)

// Define emits
defineEmits(['openContact', 'viewMoreProjects'])

// Simple initialization
const setupNavigation = () => {
  if (projectsTrack.value) {
    gsap.set(projectsTrack.value, { x: 0 })
    activeProjectIndex.value = 0
  }
}

// Go to specific project (from selector buttons)
const goToProject = (index) => {
  if (!projectsTrack.value || !horizontalScrollContainer.value) return
  
  const track = projectsTrack.value
  const container = horizontalScrollContainer.value
  const trackWidth = track.scrollWidth
  const containerWidth = container.offsetWidth
  const maxDrag = trackWidth - containerWidth
  
  if (maxDrag <= 0) return
  
  const totalProjects = messages.value?.section_4?.projects?.length || 3
  const projectWidth = maxDrag / (totalProjects - 1)
  const targetX = -(index * projectWidth)
  
  // Simple smooth animation to target position
  gsap.to(track, {
    x: targetX,
    duration: 0.8,
    ease: "power2.inOut",
    onComplete: () => {
      activeProjectIndex.value = index
    }
  })
}



// Setup entrance animations
const setupEntranceAnimations = () => {
  // Animate section title with stagger
  if (sectionTitleRef.value) {
    const titleSpans = sectionTitleRef.value.querySelectorAll('span')
    staggerFadeIn(titleSpans, {
      ...textAnimationPresets.sectionTitle,
      stagger: 0.3,
      from: 'bottom',
      distance: 60
    })
  }
  
  // Animate description
  if (descriptionRef.value) {
    fadeInFromBottom(descriptionRef.value, {
      ...textAnimationPresets.paragraph,
      delay: 0.8
    })
  }
  
  // Animate project cards entrance
  if (projectCards.value.length > 0) {
    // Initial state for cards
    gsap.set(projectCards.value, {
      opacity: 0,
      y: 50,
      scale: 0.95
    })
    
    // Animate cards in sequence
    gsap.to(projectCards.value, {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: 0.8,
      stagger: 0.2,
      ease: "power3.out",
      scrollTrigger: {
        trigger: horizontalScrollContainer.value,
        start: "top 80%",
        toggleActions: "play none none reverse"
      }
    })
  }
  
  // Animate CTA section
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
}

// Cleanup function
const cleanup = () => {
  // Kill any remaining GSAP animations
  if (projectsTrack.value) {
    gsap.killTweensOf(projectsTrack.value)
  }
}

// Setup on mount
onMounted(async () => {
  await nextTick()
  
  // Small delay to ensure DOM is ready and layout calculated
  setTimeout(() => {
    setupEntranceAnimations()
    setupNavigation()
  }, 200)
  
  // Add resize listener
  window.addEventListener('resize', () => {
    setTimeout(setupNavigation, 100)
  })
})

// Cleanup on unmount
onBeforeUnmount(() => {
  cleanup()
  window.removeEventListener('resize', setupNavigation)
})
</script>

<style scoped>
/* Horizontal scroll container */
.overflow-hidden {
  overflow: hidden !important;
}

/* Asegurar que no aparezcan scrollbars en ningún lado */
* {
  scrollbar-width: none !important;
  -ms-overflow-style: none !important;
}

*::-webkit-scrollbar {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
}

/* Oculta scrollbars en navegadores modernos */
.no-scrollbar::-webkit-scrollbar {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
}
.no-scrollbar {
  -ms-overflow-style: none !important; /* IE and Edge */
  scrollbar-width: none !important; /* Firefox */
  overflow: visible !important;
}

/* Smooth transitions for track */
.no-scrollbar {
  transition: transform 0.3s ease-out;
  backface-visibility: hidden;
  transform-style: preserve-3d;
}

/* Project cards styling */
article {
  min-height: 70vh;
  backdrop-filter: blur(20px);
  border-left: none;
  border-right: none;
  border-top: 1px solid rgba(52, 211, 153, 0.2);
  border-bottom: 1px solid rgba(52, 211, 153, 0.2);
  transition: all 0.3s ease;
}

article:hover {
  border-top-color: rgba(52, 211, 153, 0.4);
  border-bottom-color: rgba(52, 211, 153, 0.4);
  background: rgba(255, 255, 255, 0.08);
  transform: scale(1.02);
}

/* Gradient underlines animation */
.relative div[class*="bg-gradient-to-r"] {
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s ease;
}

article:hover .relative div[class*="bg-gradient-to-r"],
.relative:hover div[class*="bg-gradient-to-r"] {
  transform: scaleX(1);
}

/* Main title gradient underline */
h2 span:last-child div {
  animation: expandUnderline 1s ease-out 0.5s both;
}

@keyframes expandUnderline {
  from {
    transform: scaleX(0) skewY(-1deg);
    opacity: 0;
  }
  to {
    transform: scaleX(1) skewY(-1deg);
    opacity: 1;
  }
}

/* Technology badges hover effect */
.bg-gradient-to-r.from-esmerald\/20 {
  transition: all 0.3s ease;
}

.bg-gradient-to-r.from-esmerald\/20:hover {
  background: linear-gradient(to right, rgba(52, 211, 153, 0.3), rgba(34, 197, 94, 0.3));
  transform: translateY(-2px);
}

/* Progress indicators */
.w-3.h-3 {
  cursor: pointer;
  transition: all 0.3s ease;
}

.w-3.h-3:hover {
  transform: scale(1.2);
}

/* Media container enhancements */
.aspect-video, .aspect-square {
  transition: all 0.3s ease;
}

.aspect-video:hover, .aspect-square:hover {
  transform: scale(1.02);
  border-color: rgba(52, 211, 153, 0.5);
}

/* Video and image effects */
video, img {
  transition: all 0.7s ease;
}

/* Button enhancements */
a, button {
  position: relative;
  overflow: hidden;
}

a::before, button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transition: left 0.5s ease;
}

a:hover::before, button:hover::before {
  left: 100%;
}

/* Smooth scroll behavior */
html {
  scroll-behavior: smooth;
}

/* Focus states for accessibility */
article:focus, a:focus, button:focus {
  outline: 2px solid theme('colors.esmerald');
  outline-offset: 4px;
}

/* Performance optimizations */
.will-change-transform {
  will-change: transform;
}

/* Mobile optimizations */
@media (max-width: 1024px) {
  /* Hide custom cursor on mobile */
  .custom-cursor {
    display: none !important;
  }
  
  /* Reset cursor on mobile */
  .cursor-grab {
    cursor: default;
  }
  
  article {
    min-height: auto;
  }
  
  .text-4xl {
    font-size: 2.5rem;
  }
  
  .text-6xl {
    font-size: 3.5rem;
  }
  
  /* Improve touch scrolling on mobile */
  .transition-transform {
    transition: transform 0.2s ease-out;
  }
}

/* Hide scrollbar but keep functionality */
.overflow-x-auto::-webkit-scrollbar {
  display: none;
}

.overflow-x-auto {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
