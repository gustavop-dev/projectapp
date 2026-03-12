<template>
  <section class="w-full mt-12 mb-16 lg:mb-40 px-3 lg:px-32 lg:mt-16">
    <div class="max-w-7xl mx-auto">
      <!-- Section Header -->
      <div class="mb-10 lg:mb-16">
        <h2 class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl 2xl:text-7xl font-light text-esmerald mb-4 lg:mb-6 leading-tight">
          {{ messages?.study_cases?.title || 'Design and code made Simple' }}
        </h2>
        <p class="text-lg lg:text-2xl text-green-light max-w-3xl">
          {{ messages?.study_cases?.subtitle || 'Our team of experts is here to turn your vision into reality' }}
        </p>
      </div>

      <!-- Unified AnimatedTestimonials carousel (TapTag + all cases) -->
      <ClientOnly>
        <AnimatedTestimonials
          :testimonials="allCaseStudies"
          :autoplay="true"
          :visit-project-text="messages?.study_cases?.visit_project || 'Visit Project'"
          :watch-video-text="messages?.study_cases?.taptag?.watch_video || 'Watch video'"
          @watch-video="openVideoModal"
        />
      </ClientOnly>
    </div>

    <!-- Video Modal (lazy: src only set when open) -->
    <VideoModal
      :is-open="isVideoOpen"
      :video-src="isVideoOpen ? portfolioVideo : ''"
      @close="isVideoOpen = false"
    />
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import AnimatedTestimonials from '~/components/ui/AnimatedTestimonials.vue'
import VideoModal from '~/components/VideoModal.vue'
import { useMessages } from '~/composables/useMessages'

import portfolioVideo from '~/assets/videos/portfolio/portfolio-showcase.mp4'
import videoPoster from '~/assets/images/home/hero/video-poster.jpg'
import imgGM from '~/assets/images/studyCases/G&M-Platform.png'
import imgConstance from '~/assets/images/studyCases/Constance-Hotels.png'

const { messages } = useMessages()
const isVideoOpen = ref(false)

const openVideoModal = () => {
  isVideoOpen.value = true
}

const allCaseStudies = computed(() => {
  const taptag = messages.value?.study_cases?.taptag
  const cases = messages.value?.study_cases?.cases || []

  const imageMap = {
    'G&M Platform': imgGM,
    'Constance Hotels': imgConstance
  }

  const taptagItem = taptag ? {
    name: taptag.name || 'TapTag',
    designation: taptag.designation || '',
    quote: taptag.quote || '',
    url: taptag.url || '',
    src: videoPoster,
    watchVideo: true
  } : null

  const otherCases = cases.map(caseItem => ({
    ...caseItem,
    src: imageMap[caseItem.name] || ''
  }))

  return taptagItem ? [taptagItem, ...otherCases] : otherCases
})
</script>

