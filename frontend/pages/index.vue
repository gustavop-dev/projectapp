<template>
  <div class="overflow-x-hidden bg-esmerald-light" itemscope itemtype="https://schema.org/WebPage">
    <!-- S1: Hero + CTA WhatsApp -->
    <Hero />

    <!-- S1: Trust bar / Tech logos -->
    <TechStack />

    <!-- S1.5: ¿Qué desarrollamos? — interactive gradient banner -->
    <WhatWeBuild />

    <!-- S2: Agitación del dolor (4 pain cards) -->
    <PainPoints />

    <!-- S3: Tu Solución — Proceso en fases -->
    <UnrepeatableSection />

    <!-- Marquee visual separator -->
    <MarqueeStrips />

    <!-- S4: Prueba Social — Casos de éxito -->
    <StudyCases />
    
    <!-- S5: Formulario inline (ServicesCards tiene form + cards) -->
    <section class="mt-12 mb-16 lg:mb-40 px-3 lg:px-32 lg:mt-16" aria-labelledby="form-intro-title" itemscope itemtype="https://schema.org/WebPageElement">
      <h2
        ref="mainTitleRef"
        id="form-intro-title"
        class="block font-light text-2xl sm:text-3xl md:text-4xl lg:text-4xl xl:text-5xl 2xl:text-6xl text-esmerald lg:pe-60"
        itemprop="headline"
      >
        {{ messages?.section_1?.title }}
      </h2>
      <ServicesCards />
    </section>

    <!-- S6: FAQ -->
    <LandingFAQ />

    <!-- Book a Call Section -->
    <BookCallSection />

    <footer itemscope itemtype="https://schema.org/WPFooter">
      <FooterSection />
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useFreeResources } from '~/composables/useFreeResources'
import FooterSection from '~/components/sections/FooterSection.vue'
import Hero from '~/components/home/Hero.vue'
import TechStack from '~/components/home/TechStack.vue'
import ServicesCards from '~/components/home/ServicesCards.vue'
import UnrepeatableSection from '~/components/home/UnrepeatableSection.vue'
import MarqueeStrips from '~/components/home/MarqueeStrips.vue'
import BookCallSection from '~/components/home/BookCallSection.vue'
import StudyCases from '~/components/home/StudyCases.vue'
import PainPoints from '~/components/landing/PainPoints.vue'
import WhatWeBuild from '~/components/home/WhatWeBuild.vue'
import LandingFAQ from '~/components/landing/LandingFAQ.vue'
import { useMessages } from '~/composables/useMessages'
import { useServiceJsonLd } from '~/composables/useSeoJsonLd'

useSeoHead('landingSoftware')

const { locale } = useI18n()
const isEn = computed(() => locale.value.startsWith('en'))

useServiceJsonLd({
  name: computed(() => isEn.value
    ? 'Custom Software Development'
    : 'Desarrollo de Software a la Medida'
  ).value,
  description: computed(() => isEn.value
    ? 'We build custom software that transforms your manual processes into intelligent systems. Free diagnosis, weekly sprints, 100% your code.'
    : 'Desarrollamos software a la medida que transforma tus procesos manuales en sistemas inteligentes. Diagnóstico gratuito, sprints semanales, código 100% tuyo.'
  ).value,
  url: `/${locale.value}`,
})

const { messages } = useMessages()

const mainTitleRef = ref(null)
const isDesktop = ref(false)

const videoRef = ref(null)
const imageRef = ref(null)

const { freeMediaResources } = useFreeResources({
  videos: [videoRef],
  images: [imageRef],
})

let resizeTimeout
function handleResize() {
  if (resizeTimeout) clearTimeout(resizeTimeout)
  resizeTimeout = setTimeout(() => {
    isDesktop.value = window.innerWidth >= 1024
  }, 150)
}

const setupAnimations = async () => {
  if (!import.meta.client) return
  const { useTextAnimations, textAnimationPresets } = await import('~/composables/useTextAnimations')
  const { fadeInFromBottom } = useTextAnimations()

  if (mainTitleRef.value) {
    fadeInFromBottom(mainTitleRef.value, {
      ...textAnimationPresets.sectionTitle,
      duration: 0.8,
      delay: 0,
      distance: 40,
      ease: "power2.out",
      triggerStart: "top 95%"
    })
  }
}

onMounted(async () => {
  if (typeof window !== 'undefined') {
    isDesktop.value = window.innerWidth >= 1024
    window.addEventListener('resize', handleResize, { passive: true })
  }
  await nextTick()
  setupAnimations()
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', handleResize)
  }
  if (resizeTimeout) clearTimeout(resizeTimeout)
  freeMediaResources()
})
</script>

<style scoped>
</style>
