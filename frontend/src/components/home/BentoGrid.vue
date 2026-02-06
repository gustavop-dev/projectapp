<template>
  <section class="mt-12 px-3 lg:px-32 lg:mt-16">
    <!-- Section Header -->
    <div class="mb-16 text-right">
      <h2 class="block font-light text-6xl text-esmerald lg:text-8xl mb-8">
        {{ messages?.bentoGrid?.title1 || 'Design and code' }}<br>
        {{ messages?.bentoGrid?.title2 || 'made Simple' }}
      </h2>
      <p class="text-green-light text-xl lg:text-2xl font-light ml-auto max-w-3xl">
        {{ messages?.bentoGrid?.subtitle || 'Our team of experts is here to turn your vision into reality' }}
      </p>
    </div>

    <!-- Bento Grid Layout -->
    <div class="bento-grid grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-7xl mx-auto">
      
      <!-- Card 1: Portfolio - Large Left Card -->
      <div class="bento-card portfolio-card bg-white rounded-3xl p-8 lg:p-12 shadow-sm hover:shadow-lg transition-shadow">
        <div class="card-image-container mb-6">
          <!-- Portfolio Carousel -->
          <swiper
            :modules="modules"
            :slides-per-view="1.5"
            :space-between="20"
            :loop="true"
            :autoplay="{
              delay: 0,
              disableOnInteraction: false,
            }"
            :speed="3000"
            :breakpoints="{
              320: { slidesPerView: 1, spaceBetween: 15 },
              640: { slidesPerView: 1.3, spaceBetween: 20 },
              1024: { slidesPerView: 1.5, spaceBetween: 20 }
            }"
            class="portfolio-swiper rounded-2xl"
          >
            <swiper-slide v-for="(image, index) in portfolioImages" :key="index">
              <img 
                :src="image" 
                :alt="`Portfolio project ${index + 1}`"
                class="w-full h-64 object-cover rounded-xl"
              />
            </swiper-slide>
          </swiper>
        </div>
        
        <h3 class="text-3xl font-light text-gray-700 mb-3">
          {{ messages?.bentoGrid?.portfolio?.title || 'Portfolio' }}
        </h3>
        <p class="text-gray-500 mb-6">
          {{ messages?.bentoGrid?.portfolio?.description || 'Our team of experts is here to turn your vision into reality' }}
        </p>
        
        <!-- CTA Buttons -->
        <div class="flex gap-3">
          <button 
            @click="goToContact"
            class="cta-button-primary px-6 py-3 bg-lemon text-black rounded-full font-semibold text-base hover:bg-lemon/90 transition-all hover:scale-105 shadow-md hover:shadow-lg"
          >
            {{ messages?.bentoGrid?.portfolio?.ctaPrimary || 'Get in Touch' }}
          </button>
          <button 
            @click="goToPortfolio"
            class="cta-button-secondary px-6 py-3 bg-white text-slate-900 rounded-full font-medium text-base hover:bg-slate-50 transition-all shadow-sm"
          >
            {{ messages?.bentoGrid?.portfolio?.ctaSecondary || 'Go to Portfolio' }}
          </button>
        </div>

        <!-- Recent Work Section -->
        <div class="recent-work mt-8">
          <h4 class="text-sm font-semibold tracking-wider mb-4">
            {{ messages?.bentoGrid?.portfolio?.recentWork || 'RECENT WORK:' }}
          </h4>
          <div class="grid grid-cols-2 gap-4">
            <!-- Project 1: TapTag -->
            <a 
              :href="messages?.bentoGrid?.recentWork?.taptag?.url || 'https://taptag.com.co/'"
              target="_blank"
              rel="noopener noreferrer"
              class="project-item project-card bg-esmerald-light cursor-pointer"
            >
              <div class="project-icon mb-2">
                <img :src="taptag_icon" alt="TapTag" class="w-8 h-8 object-contain" />
              </div>
              <h5 class="font-semibold text-sm mb-1">{{ messages?.bentoGrid?.recentWork?.taptag?.name || 'TapTag' }}</h5>
              <div class="flex flex-wrap gap-2 text-xs">
                <span class="tag">{{ messages?.bentoGrid?.recentWork?.taptag?.tag1 || 'Design' }}</span>
                <span class="tag">{{ messages?.bentoGrid?.recentWork?.taptag?.tag2 || 'Vue.js' }}</span>
                <span class="tag">{{ messages?.bentoGrid?.recentWork?.taptag?.tag3 || 'MySQL' }}</span>
                <span class="tag">{{ messages?.bentoGrid?.recentWork?.taptag?.tag4 || 'Django' }}</span>
              </div>
            </a>
            
            <!-- Project 2: Andre Architecture -->
            <a 
              :href="messages?.bentoGrid?.recentWork?.andre?.url || 'https://www.andrearchitecture.com/'"
              target="_blank"
              rel="noopener noreferrer"
              class="project-item project-card bg-esmerald-light cursor-pointer"
            >
              <div class="project-icon mb-2">
                <img :src="andre_icon" alt="Andre Architecture" class="w-8 h-8 object-contain" />
              </div>
              <h5 class="font-semibold text-sm mb-1">{{ messages?.bentoGrid?.recentWork?.andre?.name || 'Andre Architecture' }}</h5>
              <div class="flex flex-wrap gap-2 text-xs">
                <span class="tag">{{ messages?.bentoGrid?.recentWork?.andre?.tag1 || 'Design' }}</span>
                <span class="tag">{{ messages?.bentoGrid?.recentWork?.andre?.tag2 || 'Webflow' }}</span>
                <span class="tag">{{ messages?.bentoGrid?.recentWork?.andre?.tag3 || 'React' }}</span>
                <span class="tag">{{ messages?.bentoGrid?.recentWork?.andre?.tag4 || 'Branding' }}</span>
              </div>
            </a>
          </div>
        </div>
      </div>

      <!-- Right Column: Two Stacked Cards -->
      <div class="flex flex-col gap-6">
        
        <!-- Card 2: UI/UX, websites, platforms & more -->
        <div class="relative">
          <!-- Tooltip always visible with 45deg rotation from top-right corner of the card -->
          <div
            @click="openVideoModal"
            class="asterisk-tooltip absolute bg-esmerald text-white px-4 py-2 rounded-lg whitespace-nowrap cursor-pointer hover:bg-esmerald/90 transition-colors"
            style="
              top: 20px;
              right: -40px;
              font-size: 0.9rem;
              transform: rotate(45deg);
              transform-origin: center;
              z-index: 50;
            "
          >
            {{ messages?.bentoGrid?.apps?.tooltip || 'Click here to see our presentation ;)'}}
          </div>
          
          <div class="bento-card apps-card bg-white rounded-3xl p-8 shadow-sm hover:shadow-lg transition-shadow">
            <div class="flex items-start justify-between">
            <div>
              <h3 class="text-3xl font-light text-gray-600 mb-2">
                {{ messages?.bentoGrid?.apps?.title || 'UI/UX, websites,' }}<br>
                {{ messages?.bentoGrid?.apps?.subtitle || 'platforms & more' }}
              </h3>
              <div class="flex gap-3 mt-4">
                <button 
                  class="cta-button px-6 py-3 bg-lemon text-black rounded-full font-semibold text-base hover:bg-lemon/90 transition-all hover:scale-105 shadow-md hover:shadow-lg"
                  data-cal-link="projectapp/discovery-call-projectapp"
                  data-cal-namespace="discovery-call-projectapp"
                  data-cal-config='{"layout":"week_view","theme":"dark"}'
                >
                  {{ messages?.bentoGrid?.apps?.cta || "Let's Talk" }}
                </button>
                <button 
                  @click="openVideoModal"
                  class="cta-button px-6 py-3 bg-white text-slate-900 rounded-full font-medium text-base hover:bg-slate-50 transition-all shadow-sm"
                >
                  {{ messages?.bentoGrid?.apps?.watchVideo || 'Watch Video' }}
                </button>
              </div>
            </div>
            <div class="icon-placeholder relative cursor-pointer w-48 h-48" @click="openVideoModal">
              <!-- Two rotating asterisks stacked diagonally -->
              <div class="asterisk-container relative w-full h-full">
                <!-- Black asterisk (larger, background) -->
                <span ref="asteriskBlack" class="font-black text-black absolute top-0 left-0" style="font-size: 12rem; line-height: 1;">*</span>
                <!-- Gradient asterisk (smaller, foreground, offset diagonally) -->
                <span ref="asteriskGradient" class="font-black absolute" style="font-size: 10rem; line-height: 1; top: 2rem; left: 2rem; background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">*</span>
              </div>
            </div>
          </div>
        </div>
        </div>

        <!-- Card 3: Web Development Services -->
        <div class="bento-card services-card bg-gradient-to-br from-orange-100 via-pink-100 to-purple-100 rounded-3xl p-8 shadow-sm hover:shadow-lg transition-shadow">
          <div class="services-icon-container flex items-center justify-center h-full">
            <!-- Phone mockup image -->
            <img 
              src="@/assets/images/home/services/portfolio/phone-ui.webp" 
              alt="Mobile UI Design"
              class="w-64 h-auto"
            />
          </div>
        </div>

      </div>
    </div>

    <!-- Video Modal -->
    <VideoModal
      :is-open="isVideoModalOpen"
      :video-src="videoSrc"
      @close="closeVideoModal"
    />
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useMessages } from '@/composables/useMessages'
import { useLanguageStore } from '@/stores/language'
import { Swiper, SwiperSlide } from 'swiper/vue'
import { Autoplay } from 'swiper/modules'
import gsap from 'gsap'
import VideoModal from '@/components/VideoModal.vue'
import 'swiper/css'

const { messages } = useMessages()
const router = useRouter()
const languageStore = useLanguageStore()
const { currentLocale } = storeToRefs(languageStore)

const goToContact = () => {
  const locale = currentLocale.value || 'es-co'
  router.push(`/${locale}/contact`)
}

const goToPortfolio = () => {
  const locale = currentLocale.value || 'es-co'
  router.push(`/${locale}/portfolio-works`)
}

// Swiper modules
const modules = [Autoplay]

// Asterisk refs
const asteriskBlack = ref(null)
const asteriskGradient = ref(null)

// Video modal state
const isVideoModalOpen = ref(false)
const videoSrc = '/videos/presentationComp.mp4'

const openVideoModal = () => {
  isVideoModalOpen.value = true
}

const closeVideoModal = () => {
  isVideoModalOpen.value = false
}

// Recent Work icons
const taptag_icon = new URL('@/assets/images/recentWork/taptag_icon.png', import.meta.url).href
const andre_icon = new URL('@/assets/images/recentWork/andrearchitecture.ico', import.meta.url).href

// Portfolio images
const portfolioImages = [
  new URL('@/assets/images/home/services/portfolio/694acfaa4f1b2711918596.png', import.meta.url).href,
  new URL('@/assets/images/home/services/portfolio/695cf890e9ff2789503598.jpg', import.meta.url).href,
  new URL('@/assets/images/home/services/portfolio/6963c75e567f7448307207.png', import.meta.url).href,
  new URL('@/assets/images/home/services/portfolio/6964b60076436116585408.jpg', import.meta.url).href,
  new URL('@/assets/images/home/services/portfolio/6965c223ea848976639794.jpg', import.meta.url).href,
  new URL('@/assets/images/home/services/portfolio/6966bda4d9d83553634207.jpg', import.meta.url).href,
  new URL('@/assets/images/home/services/portfolio/69451a2e10349788185764.png', import.meta.url).href,
  new URL('@/assets/images/home/services/portfolio/69666fb5c0f48936307233.jpg', import.meta.url).href
]

// Animate asterisks with GSAP in opposite directions
onMounted(() => {
  // Black asterisk rotates clockwise
  if (asteriskBlack.value) {
    gsap.to(asteriskBlack.value, {
      rotation: 360,
      duration: 4,
      repeat: -1,
      ease: 'linear'
    })
  }
  
  // Gradient asterisk rotates counter-clockwise
  if (asteriskGradient.value) {
    gsap.to(asteriskGradient.value, {
      rotation: -360,
      duration: 4,
      repeat: -1,
      ease: 'linear'
    })
  }
})
</script>

<style scoped>
.bento-card {
  position: relative;
  overflow: hidden;
}

.bento-card:hover {
  transform: translateY(-2px);
  transition: transform 0.3s ease;
}

.tag {
  display: inline-block;
  padding: 4px 8px;
  background: #f0f0f0;
  border-radius: 4px;
  color: #666;
  transition: background 0.2s ease;
}

.project-card {
  display: block;
  padding: 12px;
  border-radius: 12px;
  transition: all 0.3s ease;
  text-decoration: none;
  color: inherit;
}

.project-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.project-card:hover .tag {
  background: #d4e4e4;
}

.portfolio-swiper {
  overflow: visible;
}

.portfolio-swiper :deep(.swiper-wrapper) {
  transition-timing-function: linear;
}

/* Asterisk display */
.asterisk-container span {
  display: inline-block;
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .bento-grid {
    grid-template-columns: 1fr;
  }
}
</style>
