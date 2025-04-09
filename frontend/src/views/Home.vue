<template>
  <div>
    <!-- Fixed navbar component at the top of the page -->
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar />
    </div>

    <!-- Render video components with lazy loading -->
    <Suspense>
      <template #default>
        <component :is="isDesktop ? InitialVideo : InitialVideoMobile" :play_text="isDesktop ? messages.video.text : undefined" />
      </template>
      <template #fallback>
        <div class="h-screen flex items-center justify-center bg-esmerald-light">
          <div class="w-12 h-12 border-4 border-esmerald rounded-full border-t-transparent animate-spin"></div>
        </div>
      </template>
    </Suspense>

    <!-- First section of the home page with a title -->
    <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52">
      <h2 class="block font-light text-4xl text-esmerald lg:pe-60 lg:text-6xl">
        {{ messages.section_1.title }}
      </h2>
    </section>

    <!-- Grid section with responsive text layout -->
    <section class="grid grid-cols-3">
      <div class="col-span-1">
        <h1 class="hidden font-light text-sm ms-32 text-esmerald lg:inline">{{ messages.section_2.software_house }}</h1>
      </div>
      <div class="col-span-3 lg:col-span-2">
        <div class="grid grid-cols-3 gap-12 lg:grid-cols-2">
          <div class="col-span-1 lg:hidden"></div>
          <div class="col-span-2 lg:col-span-1">
            <h1 class="bg-esmerald-light px-6 py-2 inline-block rounded-3xl text-esmerald text-sm">{{ messages.section_2.our_motto }}</h1>
            <h2 class="mt-20">
              <span class="text-esmerald font-regular text-lg">{{ messages.section_2.text.first }}</span>
              <span class="text-green-light text-lg font-regular">{{ messages.section_2.text.second }}<br><br>{{ messages.section_2.text.third }}</span>
            </h2>
          </div>
          <div class="col-span-3 lg:pe-4 lg:col-span-1">
            <!-- Video optimizado -->
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
            >
              <source src="@/assets/videos/home/cubic.mp4" type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
        </div>
      </div>
    </section>

    <!-- Third section of the home page with image and text content -->
    <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52">
      <h2 class="block font-light text-5xl mb-24 text-esmerald lg:mb-40 lg:text-6xl lg:text-end">
        {{ messages.section_3.title }}
      </h2>
      <div class="grid lg:grid-cols-2">
        <div class="h-80 order-2 mt-24 lg:mt-0 lg:order-1 lg:h-auto">
          <!-- Imagen optimizada con atributos nativos de lazy loading -->
          <img 
            ref="imageRef" 
            src="@/assets/images/home/cube_illusion.webp" 
            loading="lazy" 
            decoding="async"
            alt="Section 3" 
            width="800"
            height="600"
            fetchpriority="low"
            class="w-full h-full object-cover will-change-transform"
          />
        </div>
        <div class="order-1 lg:order-2 lg:ps-32">
          <h3 class="text-end text-4xl font-light text-esmerald">{{ messages.section_3.web_development.title }}</h3>
          <p class="text-end text-lg font-regular mt-8 text-green-light">{{ messages.section_3.web_development.text }}</p>
          <h3 class="text-end text-4xl font-light text-esmerald mt-24 lg:mt-32">{{ messages.section_3.custom_development.title }}</h3>
          <p class="text-end text-lg font-regular mt-8 text-green-light">{{ messages.section_3.custom_development.text }}</p>
        </div>
      </div>
    </section>

    <!-- Contact and Footer sections loaded lazily -->
    <LazyContactSection />
    <LazyFooterSection />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, defineAsyncComponent, shallowRef } from 'vue'
import Navbar from '@/components/layouts/Navbar.vue'
import { useMessages } from '@/composables/useMessages'
import { useFreeResources } from '@/composables/useFreeResources'

// Lazy load video components with Suspense
const InitialVideo = defineAsyncComponent(() => 
  import('@/components/home/InitialVideo.vue')
)
const InitialVideoMobile = defineAsyncComponent(() => 
  import('@/components/home/InitialVideoMobile.vue')
)

// Lazy load sections that are below the fold
const LazyContactSection = defineAsyncComponent(() => 
  import('./partials/ContactSection.vue')
)
const LazyFooterSection = defineAsyncComponent(() => 
  import('./partials/FooterSection.vue')
)

const { messages } = useMessages()

// State to determine if the screen is desktop size
const isDesktop = ref(window.innerWidth >= 1024)

// Referencias para liberación de recursos
const videoRef = ref(null)
const imageRef = ref(null)

// Liberar recursos cuando el componente se desmonta
useFreeResources({
  videos: [videoRef],
  images: [imageRef],
})

// Debounced resize handler with passive listener for better performance
let resizeTimeout
function handleResize() {
  clearTimeout(resizeTimeout)
  resizeTimeout = setTimeout(() => {
    isDesktop.value = window.innerWidth >= 1024
  }, 150)
}

// Add event listener for window resize with passive option for better performance
onMounted(() => {
  window.addEventListener('resize', handleResize, { passive: true })
})

// Remove event listener when component is destroyed
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  clearTimeout(resizeTimeout)
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