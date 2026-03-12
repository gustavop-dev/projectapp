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

      <!-- ===== DESKTOP LAYOUT ===== -->
      <div class="hidden lg:block">
        <!-- TapTag Showcase: video poster + mockup overlapping -->
        <div class="taptag-showcase mb-20">
          <div class="relative grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
            <!-- Left: Overlapping images -->
            <div class="relative flex justify-center lg:justify-start">
              <div class="showcase-stack">
                <div class="showcase-card showcase-video" @click="openVideoModal">
                  <img :src="videoPoster" alt="TapTag Video" class="w-full h-full object-cover rounded-2xl" />
                  <div class="play-overlay">
                    <div class="play-btn">
                      <svg class="w-10 h-10 text-white ml-1" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                    </div>
                  </div>
                </div>
                <div class="showcase-card showcase-mockup">
                  <img :src="mockupTaptag" alt="TapTag Platform" class="w-full h-full object-cover rounded-2xl" />
                </div>
              </div>
            </div>
            <!-- Right: TapTag case info -->
            <div class="bg-white rounded-3xl p-8 lg:p-12 min-h-[300px] flex flex-col justify-between">
              <div>
                <h3 class="text-3xl lg:text-4xl font-bold text-esmerald mb-2">{{ messages?.study_cases?.taptag?.name || 'TapTag' }}</h3>
                <p class="text-base text-green-light mb-6">{{ messages?.study_cases?.taptag?.designation || 'NFC E-commerce · Full Platform' }}</p>
                <p class="text-lg lg:text-xl text-slate-600 leading-relaxed">{{ messages?.study_cases?.taptag?.quote || '' }}</p>
                <div class="flex flex-col items-start gap-3 mt-6">
                  <a v-if="messages?.study_cases?.taptag?.url" :href="messages.study_cases.taptag.url" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-2 text-esmerald font-medium text-base hover:gap-3 transition-all duration-300 group">
                    {{ messages?.study_cases?.visit_project || 'View full case' }}
                    <svg class="w-4 h-4 transition-transform duration-300 group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
                  </a>
                  <button @click="openVideoModal" class="inline-flex items-center gap-2 text-green-light font-medium text-base hover:text-esmerald transition-colors cursor-pointer">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                    {{ messages?.study_cases?.taptag?.watch_video || 'Watch video' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Animated Testimonials for remaining cases -->
        <ClientOnly>
          <AnimatedTestimonials
            :testimonials="caseStudies"
            :autoplay="true"
            :visit-project-text="messages?.study_cases?.visit_project || 'Visit Project'"
          />
        </ClientOnly>
      </div>

      <!-- ===== MOBILE LAYOUT: Unified carousel ===== -->
      <div class="lg:hidden">
        <ClientOnly>
          <swiper
            :modules="swiperModules"
            :slides-per-view="1.05"
            :space-between="12"
            :pagination="{ clickable: true }"
            class="study-cases-swiper"
          >
            <!-- TapTag slide -->
            <swiper-slide>
              <div class="bg-white rounded-2xl overflow-hidden">
                <div class="relative h-48 cursor-pointer" @click="openVideoModal">
                  <img :src="videoPoster" alt="TapTag Video" class="w-full h-full object-cover" />
                  <div class="absolute inset-0 bg-black/20 flex items-center justify-center">
                    <div class="w-14 h-14 rounded-full bg-esmerald/80 flex items-center justify-center">
                      <svg class="w-7 h-7 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                    </div>
                  </div>
                </div>
                <div class="p-6">
                  <h3 class="text-xl font-bold text-esmerald mb-1">{{ messages?.study_cases?.taptag?.name || 'TapTag' }}</h3>
                  <p class="text-sm text-green-light mb-3">{{ messages?.study_cases?.taptag?.designation || '' }}</p>
                  <p class="text-sm text-slate-600 leading-relaxed line-clamp-4">{{ messages?.study_cases?.taptag?.quote || '' }}</p>
                  <div class="flex flex-wrap items-center gap-3 mt-4">
                    <a v-if="messages?.study_cases?.taptag?.url" :href="messages.study_cases.taptag.url" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 text-esmerald font-medium text-sm">
                      {{ messages?.study_cases?.visit_project || 'View full case' }}
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
                    </a>
                  </div>
                </div>
              </div>
            </swiper-slide>

            <!-- Other case studies -->
            <swiper-slide v-for="(study, index) in caseStudies" :key="index">
              <div class="bg-white rounded-2xl overflow-hidden">
                <div class="relative h-48">
                  <img :src="study.src" :alt="study.name" class="w-full h-full object-cover" />
                </div>
                <div class="p-6">
                  <h3 class="text-xl font-bold text-esmerald mb-1">{{ study.name }}</h3>
                  <p class="text-sm text-green-light mb-3">{{ study.designation }}</p>
                  <p class="text-sm text-slate-600 leading-relaxed line-clamp-4">{{ study.quote }}</p>
                  <a v-if="study.url" :href="study.url" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 text-esmerald font-medium text-sm mt-4">
                    {{ messages?.study_cases?.visit_project || 'Visit Project' }}
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
                  </a>
                </div>
              </div>
            </swiper-slide>
          </swiper>
        </ClientOnly>
      </div>
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
import { Swiper, SwiperSlide } from 'swiper/vue'
import { Pagination } from 'swiper/modules'
import { useMessages } from '~/composables/useMessages'
import 'swiper/css'
import 'swiper/css/pagination'

import portfolioVideo from '~/assets/videos/portfolio/portfolio-showcase.mp4'
import videoPoster from '~/assets/images/home/hero/video-poster.jpg'
import mockupTaptag from '~/assets/images/home/hero/mockup-taptag.png'
import imgGM from '~/assets/images/studyCases/G&M-Platform.png'
import imgConstance from '~/assets/images/studyCases/Constance-Hotels.png'

const { messages } = useMessages()
const isVideoOpen = ref(false)
const swiperModules = [Pagination]

const openVideoModal = () => {
  isVideoOpen.value = true
}

const caseStudies = computed(() => {
  const cases = messages.value?.study_cases?.cases || []

  const imageMap = {
    'G&M Platform': imgGM,
    'Constance Hotels': imgConstance
  }

  return cases.map(caseItem => ({
    ...caseItem,
    src: imageMap[caseItem.name] || ''
  }))
})
</script>

<style scoped>
.showcase-stack {
  position: relative;
  width: 480px;
  height: 420px;
}

.showcase-card {
  position: absolute;
  width: 300px;
  height: 340px;
  border-radius: 1rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.18), 0 8px 24px -8px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.showcase-video {
  top: 0;
  left: 0;
  transform: rotate(-8deg);
  z-index: 2;
  cursor: pointer;
}

.showcase-video:hover {
  transform: rotate(-4deg) scale(1.03);
}

.showcase-mockup {
  top: 10%;
  right: 0;
  transform: rotate(6deg);
  z-index: 1;
}

.showcase-mockup:hover {
  transform: rotate(2deg) scale(1.03);
  z-index: 3;
}

.play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.25);
  transition: background 0.3s ease;
}

.showcase-video:hover .play-overlay {
  background: rgba(0, 0, 0, 0.4);
}

.play-btn {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(0, 41, 33, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease, background 0.3s ease;
}

.showcase-video:hover .play-btn {
  transform: scale(1.1);
  background: rgba(0, 41, 33, 0.95);
}

@media (max-width: 1023px) {
  .showcase-stack {
    width: 340px;
    height: 320px;
  }
  .showcase-card {
    width: 220px;
    height: 260px;
  }
}

@media (min-width: 1280px) {
  .showcase-stack {
    width: 540px;
    height: 460px;
  }
  .showcase-card {
    width: 340px;
    height: 380px;
  }
}
</style>
