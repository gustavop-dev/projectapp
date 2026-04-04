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
      :video-src="isVideoOpen ? currentVideo : ''"
      @close="isVideoOpen = false"
    />
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import AnimatedTestimonials from '~/components/ui/AnimatedTestimonials.vue'
import VideoModal from '~/components/VideoModal.vue'
import { useMessages } from '~/composables/useMessages'

import videoPoster from '~/assets/images/home/hero/video-poster.jpg'
import mockupTaptag from '~/assets/images/home/hero/mockup-taptag.png'
import imgGMPoster from '~/assets/images/studyCases/gm-platform-video-poster.webp'
import imgGMPlatform from '~/assets/images/studyCases/gm-platform-testimonial.webp'
import imgConstance from '~/assets/images/studyCases/Constance-Hotels.png'

const { messages } = useMessages()
const isVideoOpen = ref(false)
const currentVideo = ref('')

const openVideoModal = async (testimonial) => {
  try {
    if (testimonial?.name === 'G&M Platform') {
      const mod = await import('~/assets/videos/studyCases/gm-platform-testimonial.webm')
      currentVideo.value = mod.default
    } else {
      const mod = await import('~/assets/videos/portfolio/portfolio-showcase.mp4')
      currentVideo.value = mod.default
    }
  } catch (e) {
    console.error('Error loading video:', e)
    return
  }
  isVideoOpen.value = true
}

const allCaseStudies = computed(() => {
  const taptag = messages.value?.study_cases?.taptag
  const gm = messages.value?.study_cases?.cases?.find(c => c.name === 'G&M Platform')
  const otherCases = (messages.value?.study_cases?.cases || []).filter(c => c.name !== 'G&M Platform')

  const imageMap = {
    'Constance Hotels': imgConstance
  }

  const taptagItem = taptag ? {
    name: taptag.name || 'TapTag',
    designation: taptag.designation || '',
    quote: taptag.quote || '',
    url: taptag.url || '',
    src: videoPoster,
    mockupSrc: mockupTaptag,
    watchVideo: true,
    watchVideoText: taptag.watch_video || 'Watch video'
  } : null

  const gmItem = gm ? {
    name: gm.name || 'G&M Platform',
    designation: gm.designation || '',
    quote: gm.quote || '',
    url: gm.url || '',
    src: imgGMPoster,
    mockupSrc: imgGMPlatform,
    watchVideo: true,
    watchVideoText: gm.watch_video || 'Watch video'
  } : null

  const mappedOther = otherCases.map(caseItem => ({
    ...caseItem,
    src: imageMap[caseItem.name] || ''
  }))

  return [taptagItem, gmItem, ...mappedOther].filter(Boolean)
})
</script>

