<template>
  <div class="overflow-x-hidden bg-esmerald-light" itemscope itemtype="https://schema.org/WebPage">
    <!-- Hero section -->
    <Hero />

    <!-- Tech Stack section -->
    <TechStack />

    <!-- Introduction section with main heading -->
    <section class="mt-12 mb-16 lg:mb-40 px-3 lg:px-32 lg:mt-16" aria-labelledby="main-intro-title" itemscope itemtype="https://schema.org/WebPageElement">
      <h1
        ref="mainTitleRef"
        id="main-intro-title"
        class="block font-light text-2xl sm:text-3xl md:text-4xl lg:text-4xl xl:text-5xl 2xl:text-6xl text-esmerald lg:pe-60"
        itemprop="headline"
      >
        {{ messages?.section_1?.title }}
        <span class="sr-only">Project App. - Professional Web Development</span>
      </h1>

      <!-- Services Cards -->
      <ServicesCards />
    </section>

    <!-- Study Cases Section -->
    <StudyCases />

    <!-- Bento Grid Section -->
    <BentoGrid />

    <!-- Unrepeatable Section -->
    <UnrepeatableSection />

    <!-- Contract Section -->
    <ContractSection />

    <!-- Contact Form Section -->
    <ContactFormSection />

    <!-- Marquee Strips Section -->
    <MarqueeStrips />

    <!-- Book a Call Section -->
    <BookCallSection />

    <!-- Contact and Footer sections -->
    <section aria-label="Contact Project App. for web design services" itemscope itemtype="https://schema.org/ContactPoint">
      <ContactSection />
    </section>

    <footer itemscope itemtype="https://schema.org/WPFooter">
      <FooterSection />
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useFreeResources } from '~/composables/useFreeResources'
import ContactSection from '~/views-legacy/partials/ContactSection.vue'
import FooterSection from '~/views-legacy/partials/FooterSection.vue'
import Hero from '~/components/home/Hero.vue'
import TechStack from '~/components/home/TechStack.vue'
import ServicesCards from '~/components/home/ServicesCards.vue'
import BentoGrid from '~/components/home/BentoGrid.vue'
import UnrepeatableSection from '~/components/home/UnrepeatableSection.vue'
import ContractSection from '~/components/home/ContractSection.vue'
import ContactFormSection from '~/components/home/ContactSection.vue'
import MarqueeStrips from '~/components/home/MarqueeStrips.vue'
import BookCallSection from '~/components/home/BookCallSection.vue'
import StudyCases from '~/components/home/StudyCases.vue'
import { useMessages } from '~/composables/useMessages'

// SEO Head
useSeoHead('landingWebDesign')

const { messages } = useMessages()

// Animation refs
const mainTitleRef = ref(null)

// State to determine if the screen is desktop size
const isDesktop = ref(false)

// Referencias para liberación de recursos
const videoRef = ref(null)
const imageRef = ref(null)

// Liberar recursos cuando el componente se desmonta
const { freeMediaResources } = useFreeResources({
  videos: [videoRef],
  images: [imageRef],
})

// Debounced resize handler with passive listener for better performance
let resizeTimeout
function handleResize() {
  if (resizeTimeout) {
    clearTimeout(resizeTimeout)
  }
  resizeTimeout = setTimeout(() => {
    isDesktop.value = window.innerWidth >= 1024
  }, 150)
}

// Setup animations (client-only)
const setupAnimations = async () => {
  if (!import.meta.client) return

  const { useTextAnimations, textAnimationPresets } = await import('~/composables/useTextAnimations')
  const { fadeInFromBottom } = useTextAnimations()

  // Main title animation with fade from bottom
  if (mainTitleRef.value) {
    fadeInFromBottom(mainTitleRef.value, {
      ...textAnimationPresets.sectionTitle,
      duration: 0.8,
      delay: 0,
      distance: 40,
      ease: 'power2.out',
      triggerStart: 'top 95%'
    })
  }
}

// Add event listener for window resize with passive option for better performance
onMounted(async () => {
  if (typeof window !== 'undefined') {
    isDesktop.value = window.innerWidth >= 1024
    window.addEventListener('resize', handleResize, { passive: true })
  }

  // Setup animations after next tick
  await nextTick()
  setupAnimations()
})

// Remove event listener when component is destroyed
onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', handleResize)
  }
  if (resizeTimeout) {
    clearTimeout(resizeTimeout)
  }
  freeMediaResources()
})
</script>

<style scoped>
/* Use CSS containment for improved rendering performance */
section {
  contain: content;
}

/* Define content-visibility for elements below the fold */
section:not(:first-child):not(:nth-child(2)) {
  content-visibility: auto;
  contain-intrinsic-size: 0 500px;
}
</style>
