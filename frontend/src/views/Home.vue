<template>
  <div itemscope itemtype="https://schema.org/WebPage">
    <!-- Fixed navbar component at the top of the page -->
    <header class="fixed top-0 left-0 w-full z-50">
      <Navbar />
    </header>

    <!-- Hero video with lazy loading -->
    <Suspense>
      <template #default>
        <component 
          :is="isDesktop ? InitialVideo : InitialVideoMobile" 
          :play_text="messages?.video?.text || 'Play'" 
          aria-label="Project App web design and development company showcase" 
          itemscope itemtype="https://schema.org/VideoObject"
        />
      </template>
      <template #fallback>
        <div class="h-screen flex items-center justify-center bg-esmerald-light" aria-live="polite" role="status">
          <div class="w-12 h-12 border-4 border-esmerald rounded-full border-t-transparent animate-spin"></div>
          <span class="sr-only">Loading Project App. hero video</span>
        </div>
      </template>
    </Suspense>

    <!-- Introduction section with main heading -->
    <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52" aria-labelledby="main-intro-title" itemscope itemtype="https://schema.org/WebPageElement">
      <h1 
        ref="mainTitleRef"
        id="main-intro-title" 
        class="block font-light text-4xl text-esmerald lg:pe-60 lg:text-6xl" 
        itemprop="headline"
      >
        {{ messages?.section_1?.title || '' }}
        <span class="sr-only">Project App. - Professional Web Development</span>
      </h1>
    </section>

    <!-- About our web design company section -->
    <section class="grid grid-cols-3" aria-labelledby="about-section-title" itemscope itemtype="https://schema.org/AboutPage">
      <div class="col-span-1">
        <h2 
          ref="softwareHouseRef"
          id="about-section-title" 
          class="hidden font-light text-sm ms-32 text-esmerald lg:inline" 
          itemprop="name"
        >
          {{ messages?.section_2?.software_house || '' }}
          <span class="sr-only">Project App.</span>
        </h2>
      </div>
      <div class="col-span-3 lg:col-span-2">
        <div class="grid grid-cols-3 gap-12 lg:grid-cols-2">
          <div class="col-span-1 lg:hidden"></div>
          <div class="col-span-2 lg:col-span-1">
            <h3 
              ref="mottoRef"
              class="bg-esmerald-light px-6 py-2 inline-block rounded-3xl text-esmerald text-sm"
            >
              {{ messages?.section_2?.our_motto || '' }}
              <span class="sr-only">Project App.</span>
            </h3>
            <div ref="aboutTextRef" class="mt-20" itemprop="description">
              <p>
                <span class="text-esmerald font-regular text-lg">{{ messages?.section_2?.text?.first || '' }}</span>
                <span class="text-green-light text-lg font-regular">{{ messages?.section_2?.text?.second || '' }}</span>
                <span class="sr-only">Project App. services</span>
              </p>
              <p class="text-green-light text-lg font-regular mt-4">
                {{ messages?.section_2?.text?.third || '' }}
                <span class="sr-only">Project App. solutions</span>
              </p>
            </div>
          </div>
          <div 
            ref="videoContainerRef"
            class="col-span-3 lg:pe-4 lg:col-span-1" 
            itemscope 
            itemtype="https://schema.org/VideoObject"
          >
            <!-- Optimized video with descriptive elements -->
            <video 
              ref="videoRef" 
              autoplay 
              muted 
              loop 
              playsinline
              preload="metadata"
              width="640"
              height="360"
              class="w-full h-auto will-change-transform"
              aria-label="Web design and development showcase animation"
              itemprop="contentUrl"
            >
              <source src="@/assets/videos/home/cubic.mp4" type="video/mp4" />
              <p class="sr-only">Animated cube showcasing Project App. web design services and expertise</p>
            </video>
            <meta itemprop="name" content="Project App. Web Design Services Animation">
          </div>
        </div>
      </div>
    </section>

    <!-- Web development services section -->
    <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52" aria-labelledby="services-section-title" itemscope itemtype="https://schema.org/Service">
      <h2 
        ref="servicesTitleRef"
        id="services-section-title" 
        class="block font-light text-5xl mb-24 text-esmerald lg:mb-40 lg:text-6xl lg:text-end" 
        itemprop="name"
      >
        {{ messages?.section_3?.title || '' }}
        <span class="sr-only">by Project App.</span>
      </h2>
      <div class="grid lg:grid-cols-2">
        <div 
          ref="imageContainerRef"
          class="h-80 order-2 mt-24 lg:mt-0 lg:order-1 lg:h-auto" 
          itemscope 
          itemtype="https://schema.org/ImageObject"
        >
          <!-- Optimized image with proper alt text -->
          <img 
            ref="imageRef" 
            src="@/assets/images/home/cube_illusion.webp"
            loading="lazy" 
            decoding="async"
            alt="Cube illusion representing Project App.'s innovative web design approach"
            width="800"
            height="600"
            fetchpriority="low"
            class="w-full h-full object-cover will-change-transform"
            itemprop="contentUrl"
          />
          <meta itemprop="name" content="Project App. innovative web design approach">
        </div>
        <article 
          ref="servicesContentRef"
          class="order-1 lg:order-2 lg:ps-32" 
          itemprop="description"
        >
          <h3 class="text-end text-4xl font-light text-esmerald">
            {{ messages?.section_3?.web_development?.title || '' }}
            <span class="sr-only">Project App.</span>
          </h3>
          <p class="text-end text-lg font-regular mt-8 text-green-light">
            {{ messages?.section_3?.web_development?.text || '' }}
            <span class="sr-only">by Project App.</span>
          </p>
          <h3 class="text-end text-4xl font-light text-esmerald mt-24 lg:mt-32">
            {{ messages?.section_3?.custom_development?.title || '' }}
            <span class="sr-only">Project App.</span>
          </h3>
          <p class="text-end text-lg font-regular mt-8 text-green-light">
            {{ messages?.section_3?.custom_development?.text || '' }}
            <span class="sr-only">by Project App.</span>
          </p>
        </article>
      </div>
    </section>

    <!-- Success Stories section -->
    <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52" aria-labelledby="success-stories-title" itemscope itemtype="https://schema.org/WebPageElement">
      <LazySuccessStoriesSection />
    </section>

    <!-- Detailed Services section -->
    <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52" aria-labelledby="detailed-services-title" itemscope itemtype="https://schema.org/Service">
      <LazyDetailedServicesSection />
    </section>

    <!-- Our Process section -->
    <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52" aria-labelledby="process-title" itemscope itemtype="https://schema.org/WebPageElement">
      <LazyProcessSection />
    </section>

    <!-- Technologies section -->
    <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52" aria-labelledby="technologies-title" itemscope itemtype="https://schema.org/WebPageElement">
      <LazyTechnologiesSection />
    </section>

    <!-- Why Choose Us section -->
    <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52" aria-labelledby="why-choose-title" itemscope itemtype="https://schema.org/WebPageElement">
      <LazyWhyChooseSection />
    </section>

    <!-- Contact and Footer sections loaded lazily -->
    <section aria-label="Contact Project App. for web design services" itemscope itemtype="https://schema.org/ContactPoint">
      <LazyContactSection />
    </section>
    
    <footer itemscope itemtype="https://schema.org/WPFooter">
      <LazyFooterSection />
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, defineAsyncComponent, nextTick } from 'vue'
import Navbar from '@/components/layouts/Navbar.vue'
import { useMessages } from '@/composables/useMessages'
import { useFreeResources } from '@/composables/useFreeResources'
import { useTextAnimations, textAnimationPresets } from '@/composables/useTextAnimations'

// Lazy load video components with Suspense
const InitialVideo = defineAsyncComponent(() => 
  import('@/components/home/InitialVideo.vue')
)
const InitialVideoMobile = defineAsyncComponent(() => 
  import('@/components/home/InitialVideoMobile.vue')
)

// Lazy load sections that are below the fold
const LazySuccessStoriesSection = defineAsyncComponent(() => 
  import('./partials/SuccessStoriesSection.vue')
)
const LazyDetailedServicesSection = defineAsyncComponent(() => 
  import('./partials/DetailedServicesSection.vue')
)
const LazyProcessSection = defineAsyncComponent(() => 
  import('./partials/ProcessSection.vue')
)
const LazyTechnologiesSection = defineAsyncComponent(() => 
  import('./partials/TechnologiesSection.vue')
)
const LazyWhyChooseSection = defineAsyncComponent(() => 
  import('./partials/WhyChooseSection.vue')
)
const LazyContactSection = defineAsyncComponent(() => 
  import('./partials/ContactSection.vue')
)
const LazyFooterSection = defineAsyncComponent(() => 
  import('./partials/FooterSection.vue')
)

const { messages } = useMessages()

// Animation composable
const {
  fadeInFromBottom,
  fadeInFromLeft,
  fadeInFromRight,
  scaleIn,
  wordReveal,
  staggerFadeIn
} = useTextAnimations()

// State to determine if the screen is desktop size
const isDesktop = ref(false)

// Referencias para liberación de recursos
const videoRef = ref(null)
const imageRef = ref(null)

// Referencias para animaciones
const mainTitleRef = ref(null)
const softwareHouseRef = ref(null)
const mottoRef = ref(null)
const aboutTextRef = ref(null)
const videoContainerRef = ref(null)
const servicesTitleRef = ref(null)
const imageContainerRef = ref(null)
const servicesContentRef = ref(null)

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

// Add event listener for window resize with passive option for better performance
onMounted(async () => {
  // Asegurar que isDesktop tenga un valor inicial
  if (typeof window !== 'undefined') {
    isDesktop.value = window.innerWidth >= 1024
    window.addEventListener('resize', handleResize, { passive: true })
  }
  
  // Setup animations after next tick
  await nextTick()
  setupAnimations()
})

// Setup all animations for the main home content
const setupAnimations = () => {
  // Main title animation with fade from bottom - SIN delay inicial
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
  
  // Software house label from left - delay mínimo
  if (softwareHouseRef.value) {
    fadeInFromLeft(softwareHouseRef.value, {
      delay: 0.1,
      duration: 0.6,
      distance: 30,
      triggerStart: "top 95%"
    })
  }
  
  // Motto badge scale in - delay mínimo
  if (mottoRef.value) {
    scaleIn(mottoRef.value, {
      ...textAnimationPresets.button,
      delay: 0.2,
      scale: 0.9,
      ease: "back.out(1.4)"
    })
  }
  
  // About text paragraphs stagger - delay mínimo
  if (aboutTextRef.value) {
    const paragraphs = aboutTextRef.value.querySelectorAll('p')
    if (paragraphs.length > 0) {
      staggerFadeIn(paragraphs, {
        ...textAnimationPresets.paragraph,
        stagger: 0.1,
        delay: 0.3,
        from: 'bottom'
      })
    }
  }
  
  // Video container from right - delay mínimo
  if (videoContainerRef.value) {
    fadeInFromRight(videoContainerRef.value, {
      delay: 0.4,
      duration: 0.8,
      distance: 40,
      ease: "power2.out"
    })
  }
  
  // Services section title from right (matching text alignment)
  if (servicesTitleRef.value) {
    fadeInFromRight(servicesTitleRef.value, {
      ...textAnimationPresets.sectionTitle,
      delay: 0,
      distance: 50,
      triggerStart: "top 85%"
    })
  }
  
  // Image container scale in
  if (imageContainerRef.value) {
    scaleIn(imageContainerRef.value, {
      delay: 0.1,
      duration: 0.8,
      scale: 0.95,
      ease: "power2.out",
      triggerStart: "top 85%"
    })
  }
  
  // Services content from right (staggered)
  if (servicesContentRef.value) {
    const serviceElements = servicesContentRef.value.querySelectorAll('h3, p')
    if (serviceElements.length > 0) {
      staggerFadeIn(serviceElements, {
        stagger: 0.1,
        delay: 0.2,
        from: 'right',
        distance: 30,
        triggerStart: "top 85%",
        duration: 0.8
      })
    }
  }
}

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