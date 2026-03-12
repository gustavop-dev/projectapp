<template>
  <section class="mt-12 mb-12 lg:mb-16 px-3 lg:px-32 lg:mt-16">
    <div class="max-w-7xl mx-auto">

      <!-- Title -->
      <h2
        ref="titleRef"
        class="block font-light text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl 2xl:text-7xl text-esmerald mb-12 lg:mb-16 opacity-0"
      >
        {{ messages?.painPoints?.title }}
      </h2>

      <!-- Editorial layout: stacked cards LEFT + bg image RIGHT -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <!-- Left: Desktop stacked cards -->
        <div class="hidden lg:flex flex-col gap-4 order-2 lg:order-1">
          <div
            v-for="(card, index) in messages?.painPoints?.cards"
            :key="index"
            ref="cardRefs"
            class="group bg-white rounded-2xl p-6 lg:p-8 hover:shadow-lg transition-all duration-300 opacity-0 flex gap-5 items-start"
          >
            <div class="flex-shrink-0 w-10 h-10 rounded-full bg-esmerald flex items-center justify-center">
              <span class="text-lemon font-bold text-sm">{{ String(index + 1).padStart(2, '0') }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="text-base lg:text-lg font-bold text-esmerald mb-2 leading-snug group-hover:text-esmerald/80 transition-colors">
                {{ card.title }}
              </h3>
              <p class="text-sm lg:text-base text-green-light leading-relaxed">
                {{ card.description }}
              </p>
            </div>
          </div>
        </div>

        <!-- Mobile: Swiper carousel for cards -->
        <div class="lg:hidden order-2">
          <ClientOnly>
            <swiper
              :modules="swiperModules"
              :slides-per-view="1.15"
              :space-between="12"
              :pagination="{ clickable: true }"
              class="pain-cards-swiper"
            >
              <swiper-slide v-for="(card, index) in messages?.painPoints?.cards" :key="index">
                <div class="bg-white rounded-2xl p-6 flex gap-4 items-start min-h-[160px]">
                  <div class="flex-shrink-0 w-10 h-10 rounded-full bg-esmerald flex items-center justify-center">
                    <span class="text-lemon font-bold text-sm">{{ String(index + 1).padStart(2, '0') }}</span>
                  </div>
                  <div class="flex-1 min-w-0">
                    <h3 class="text-base font-bold text-esmerald mb-2 leading-snug">{{ card.title }}</h3>
                    <p class="text-sm text-green-light leading-relaxed">{{ card.description }}</p>
                  </div>
                </div>
              </swiper-slide>
            </swiper>
          </ClientOnly>
        </div>

        <!-- Right: Background image card with bridge text overlay -->
        <div
          ref="imageRef"
          class="relative rounded-3xl overflow-hidden min-h-[280px] lg:min-h-[600px] bg-cover bg-center opacity-0 order-1 lg:order-2"
          :style="{ backgroundImage: `url(${bgImage})` }"
        >
          <div class="absolute bottom-0 left-0 right-0 p-6 lg:p-12">
            <p class="text-base sm:text-xl lg:text-2xl text-white leading-relaxed font-medium">
              {{ messages?.painPoints?.bridge }}
            </p>
          </div>
        </div>

      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useMessages } from '~/composables/useMessages'
import { Swiper, SwiperSlide } from 'swiper/vue'
import { Pagination } from 'swiper/modules'
import 'swiper/css'
import 'swiper/css/pagination'

import imgBg from '~/assets/images/home/services/contract/card-landing-design.webp'

const { messages } = useMessages()

const swiperModules = [Pagination]
const bgImage = imgBg
const titleRef = ref(null)
const imageRef = ref(null)
const cardRefs = ref([])

const setupAnimations = async () => {
  if (!import.meta.client) return

  const gsap = (await import('gsap')).default
  const { ScrollTrigger } = await import('gsap/ScrollTrigger')
  gsap.registerPlugin(ScrollTrigger)

  if (titleRef.value) {
    gsap.set(titleRef.value, { y: 30 })
    gsap.to(titleRef.value, {
      opacity: 1, y: 0, duration: 1, ease: 'power3.out',
      scrollTrigger: { trigger: titleRef.value, start: 'top 85%', toggleActions: 'play none none reverse' }
    })
  }

  if (imageRef.value) {
    gsap.set(imageRef.value, { y: 20, scale: 0.98 })
    gsap.to(imageRef.value, {
      opacity: 1, y: 0, scale: 1, duration: 0.8, ease: 'power3.out',
      scrollTrigger: { trigger: imageRef.value, start: 'top 85%', toggleActions: 'play none none reverse' }
    })
  }

  if (cardRefs.value.length > 0) {
    gsap.set(cardRefs.value, { x: -30 })
    gsap.to(cardRefs.value, {
      opacity: 1, x: 0, duration: 0.6, stagger: 0.12, ease: 'power3.out',
      scrollTrigger: { trigger: cardRefs.value[0], start: 'top 85%', toggleActions: 'play none none reverse' }
    })
  }
}

onMounted(async () => {
  await nextTick()
  setupAnimations()
})
</script>
