<template>
  <section class="relative overflow-hidden bg-primary-soft min-h-screen flex flex-col">

    <!-- Arc Gallery (sits behind text, pushed down to overlap headline) -->
    <div
      class="absolute left-0 w-full z-0"
      :style="{ top: arcDimensions.topOffset + 'px', height: arcDimensions.radius * 1.1 + 'px' }"
    >
      <div class="absolute left-1/2 bottom-0 -translate-x-1/2">
        <div
          v-for="(src, i) in arcImages"
          :key="i"
          class="absolute opacity-0 arc-fade-in-up"
          :style="{
            width: arcDimensions.cardSize + 'px',
            left: `calc(50% + ${getArcX(i)}px)`,
            bottom: getArcY(i) + 'px',
            transform: 'translate(-50%, 50%)',
            animationDelay: i * 100 + 'ms',
            animationFillMode: 'forwards',
            zIndex: arcImages.length - i,
          }"
        >
          <div
            class="rounded-2xl shadow-xl overflow-hidden ring-1 ring-slate-200 bg-surface transition-transform hover:scale-105"
            :style="{ transform: `rotate(${getAngle(i) / 4}deg)` }"
          >
            <img
              :src="src"
              :alt="`App screenshot ${i + 1}`"
              class="block w-full h-auto"
              draggable="false"
              loading="lazy"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Hero Content (overlaps the arc — sits on top) -->
    <div class="relative z-10 flex-1 flex items-center justify-center px-6 pt-32 sm:pt-40 md:pt-48 lg:pt-56">
      <div ref="heroContentRef" class="text-center max-w-3xl" :class="{ 'hero-content-animate': isMounted }">

        <!-- Badge -->
        <span
          v-if="messages?.hero?.badge"
          class="inline-block mb-6 px-4 py-1.5 text-xs sm:text-sm font-medium tracking-wider text-slate-600 border border-slate-200 rounded-full"
        >
          {{ messages.hero.badge }}
        </span>

        <!-- Main Headline -->
        <h1 class="text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-bold text-slate-900 leading-tight">
          {{ messages?.hero?.title_part1 || 'Your App Ready' }}
          <span class="block text-text-brand mt-2">
            {{ messages?.hero?.title_part2 || 'in 30 Days.' }}
          </span>
        </h1>

        <!-- Subheadline -->
        <p
          class="mt-6 text-base sm:text-lg lg:text-xl text-slate-600 leading-relaxed max-w-2xl mx-auto"
          v-html="messages?.hero?.subtitle || 'We are mobile app developers specialized in creating apps people actually use.'"
        ></p>

        <!-- CTA Buttons -->
        <div class="flex flex-wrap justify-center gap-3 mt-8">
          <a
            v-if="messages?.hero?.cta_whatsapp_url"
            :href="messages.hero.cta_whatsapp_url"
            target="_blank"
            rel="noopener noreferrer"
            @click="trackWhatsAppClick()"
            class="px-6 py-3 bg-accent text-black rounded-full font-semibold text-sm sm:text-base hover:bg-lemon/90 transition-all hover:scale-105 shadow-md hover:shadow-lg"
          >
            {{ messages?.hero?.cta_primary || 'Get In Touch' }}
          </a>
          <button
            v-else
            @click="goToContact"
            class="px-6 py-3 bg-accent text-black rounded-full font-semibold text-sm sm:text-base hover:bg-lemon/90 transition-all hover:scale-105 shadow-md hover:shadow-lg"
          >
            {{ messages?.hero?.cta_primary || 'Get In Touch' }}
          </button>

          <button
            v-if="messages?.hero?.cta_book_call"
            class="px-6 py-3 bg-surface text-slate-900 rounded-full font-medium text-sm sm:text-base hover:bg-slate-50 transition-all flex items-center gap-2 shadow-sm"
            data-cal-link="projectapp/discovery-call-projectapp"
            data-cal-namespace="discovery-call-projectapp"
            data-cal-config='{"layout":"week_view","theme":"dark"}'
          >
            {{ messages.hero.cta_book_call }}
          </button>
        </div>

        <!-- Key Benefits -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-12 max-w-3xl w-full mx-auto">
          <div class="flex items-start gap-3 text-left">
            <svg class="w-6 h-6 text-text-brand flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            <div>
              <p class="text-sm sm:text-base font-semibold text-slate-900">{{ messages?.hero?.benefit1_title }}</p>
              <p class="text-xs sm:text-sm text-slate-600">{{ messages?.hero?.benefit1_text }}</p>
            </div>
          </div>

          <div class="flex items-start gap-3 text-left">
            <svg class="w-6 h-6 text-text-brand flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            <div>
              <p class="text-sm sm:text-base font-semibold text-slate-900">{{ messages?.hero?.benefit2_title }}</p>
              <p class="text-xs sm:text-sm text-slate-600">{{ messages?.hero?.benefit2_text }}</p>
            </div>
          </div>

          <div class="flex items-start gap-3 text-left">
            <svg class="w-6 h-6 text-text-brand flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            <div>
              <p class="text-sm sm:text-base font-semibold text-slate-900">{{ messages?.hero?.benefit3_title }}</p>
              <p class="text-xs sm:text-sm text-slate-600">{{ messages?.hero?.benefit3_text }}</p>
            </div>
          </div>

          <div class="flex items-start gap-3 text-left">
            <svg class="w-6 h-6 text-text-brand flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            <div>
              <p class="text-sm sm:text-base font-semibold text-slate-900">{{ messages?.hero?.benefit4_title }}</p>
              <p class="text-xs sm:text-sm text-slate-600">{{ messages?.hero?.benefit4_text }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Background Decorative Elements -->
    <div class="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden -z-10">
      <div class="absolute top-20 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-esmerald/5 rounded-full blur-3xl"></div>
      <div class="absolute bottom-10 right-1/4 w-72 h-72 bg-orange-200/15 rounded-full blur-3xl"></div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useMessages } from '~/composables/useMessages'
import { useGtagConversions } from '~/composables/useGtagConversions'

import app1 from '~/assets/images/home/hero/mobile-apps/app-1.webp'
import app2 from '~/assets/images/home/hero/mobile-apps/app-2.webp'
import app3 from '~/assets/images/home/hero/mobile-apps/app-3.webp'
import app4 from '~/assets/images/home/hero/mobile-apps/app-4.webp'
import app5 from '~/assets/images/home/hero/mobile-apps/app-5.webp'
import app6 from '~/assets/images/home/hero/mobile-apps/app-6.webp'
import app7 from '~/assets/images/home/hero/mobile-apps/app-7.webp'
import app8 from '~/assets/images/home/hero/mobile-apps/app-8.webp'
import app9 from '~/assets/images/home/hero/mobile-apps/app-9.webp'
import app10 from '~/assets/images/home/hero/mobile-apps/app-10.webp'
import app11 from '~/assets/images/home/hero/mobile-apps/app-11.webp'
import app12 from '~/assets/images/home/hero/mobile-apps/app-12.webp'

const { messages } = useMessages()
const router = useRouter()
const localePath = useLocalePath()
const { trackWhatsAppClick } = useGtagConversions()
const heroContentRef = ref(null)
const isMounted = ref(false)

const goToContact = () => {
  router.push(localePath('/contact'))
}

// --- Arc Gallery Config (wide flat arc behind text) ---
const startAngle = 5
const endAngle = 175
const radiusLg = 560
const radiusMd = 420
const radiusSm = 300
const cardSizeLg = 130
const cardSizeMd = 105
const cardSizeSm = 80
const topOffsetLg = 60
const topOffsetMd = 50
const topOffsetSm = 40

const arcImages = [app1, app2, app3, app4, app5, app6, app7, app8, app9, app10, app11, app12]

const arcDimensions = ref({ radius: radiusLg, cardSize: cardSizeLg, topOffset: topOffsetLg })

const count = Math.max(arcImages.length, 2)
const step = (endAngle - startAngle) / (count - 1)

function getAngle(i) {
  return startAngle + step * i
}
function getArcX(i) {
  const angleRad = (getAngle(i) * Math.PI) / 180
  return Math.cos(angleRad) * arcDimensions.value.radius
}
function getArcY(i) {
  const angleRad = (getAngle(i) * Math.PI) / 180
  return Math.sin(angleRad) * arcDimensions.value.radius
}

let resizeTimeout
function handleResize() {
  if (resizeTimeout) clearTimeout(resizeTimeout)
  resizeTimeout = setTimeout(() => {
    const w = window.innerWidth
    if (w < 640) {
      arcDimensions.value = { radius: radiusSm, cardSize: cardSizeSm, topOffset: topOffsetSm }
    } else if (w < 1024) {
      arcDimensions.value = { radius: radiusMd, cardSize: cardSizeMd, topOffset: topOffsetMd }
    } else {
      arcDimensions.value = { radius: radiusLg, cardSize: cardSizeLg, topOffset: topOffsetLg }
    }
  }, 100)
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    handleResize()
    window.addEventListener('resize', handleResize, { passive: true })
  }
  isMounted.value = true
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', handleResize)
  }
  if (resizeTimeout) clearTimeout(resizeTimeout)
})
</script>

<style scoped>
@keyframes arc-fade-in-up {
  from {
    opacity: 0;
    transform: translate(-50%, 60%);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 50%);
  }
}
@keyframes arc-fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.arc-fade-in-up {
  animation-name: arc-fade-in-up;
  animation-duration: 0.8s;
  animation-timing-function: ease-out;
}
.arc-fade-in {
  animation-name: arc-fade-in;
  animation-duration: 0.8s;
  animation-timing-function: ease-out;
}
.hero-content-animate {
  opacity: 0;
  animation: arc-fade-in 0.8s ease-out 800ms forwards;
}
</style>
