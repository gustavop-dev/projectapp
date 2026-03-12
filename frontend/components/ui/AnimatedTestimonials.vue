<template>
  <div :class="['w-full mx-auto relative', className]" style="isolation: isolate; z-index: 0;" @mouseenter="handleMouseEnter" @mouseleave="handleMouseLeave">
    <div class="relative grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
      <!-- Images Section - Larger and Horizontal -->
      <div class="order-2 lg:order-1">
        <div class="relative w-full" style="aspect-ratio: 1905/995; isolation: isolate;">
          <div
            v-for="(testimonial, index) in testimonials"
            :key="index"
            ref="imageRefs"
            class="absolute inset-0 origin-bottom"
            :style="{
              zIndex: isActive(index) ? 40 : testimonials.length + 2 - index,
              opacity: isActive(index) ? 1 : 0.7
            }"
          >
            <!-- Special overlapping layout for items with video showcase -->
            <div
              v-if="testimonial.watchVideo && testimonial.mockupSrc"
              class="relative w-full h-full flex items-center justify-center"
            >
              <div class="showcase-stack">
                <div class="showcase-card showcase-video" @click="emit('watch-video')">
                  <img :src="testimonial.src" :alt="testimonial.name" class="w-full h-full object-cover rounded-2xl" />
                  <div class="play-overlay">
                    <div class="play-btn">
                      <svg class="w-10 h-10 text-white ml-1" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                    </div>
                  </div>
                </div>
                <div class="showcase-card showcase-mockup">
                  <img :src="testimonial.mockupSrc" :alt="testimonial.name + ' Platform'" class="w-full h-full object-cover rounded-2xl" />
                </div>
              </div>
            </div>
            <!-- Normal image or video -->
            <template v-else>
              <video
                v-if="testimonial.video"
                :src="testimonial.video"
                autoplay
                muted
                loop
                playsinline
                class="h-full w-full rounded-3xl object-cover object-center"
              />
              <img
                v-else
                :src="testimonial.src"
                :alt="testimonial.name"
                draggable="false"
                class="h-full w-full rounded-3xl object-cover object-center"
              />
            </template>
          </div>
        </div>
      </div>

      <!-- Content Section - White Card with Rounded Borders -->
      <div class="order-1 lg:order-2 bg-white rounded-3xl p-8 lg:p-12 min-h-[350px] lg:min-h-[400px] flex flex-col justify-between">
        <div ref="contentRef">
          <h3 class="text-3xl lg:text-4xl font-bold text-esmerald mb-2">
            {{ testimonials[active].name }}
          </h3>
          <p class="text-base text-green-light mb-6">
            {{ testimonials[active].designation }}
          </p>
          <p class="text-lg lg:text-xl text-slate-600 leading-relaxed">
            <span
              v-for="(word, index) in currentQuoteWords"
              :key="index"
              ref="wordRefs"
              class="inline-block"
            >
              {{ word }}&nbsp;
            </span>
          </p>
          
          <!-- Visit Project Button -->
          <div class="flex flex-col items-start gap-3 mt-6">
            <a 
              v-if="testimonials[active].url"
              :href="testimonials[active].url" 
              target="_blank" 
              rel="noopener noreferrer"
              class="inline-flex items-center gap-2 text-esmerald font-medium text-base hover:gap-3 transition-all duration-300 group"
            >
              {{ visitProjectText }}
              <svg class="w-4 h-4 transition-transform duration-300 group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/>
              </svg>
            </a>
            <button
              v-if="testimonials[active].watchVideo"
              @click="emit('watch-video')"
              class="inline-flex items-center gap-2 text-green-light font-medium text-base hover:text-esmerald transition-colors cursor-pointer"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
              {{ watchVideoText }}
            </button>
          </div>
        </div>

        <!-- Navigation Buttons -->
        <div class="flex gap-4 pt-8">
          <button
            @click="handlePrev"
            class="h-12 w-12 rounded-full bg-esmerald-light flex items-center justify-center group hover:bg-esmerald transition-colors"
          >
            <svg class="h-6 w-6 text-esmerald group-hover:text-bone group-hover:rotate-12 transition-all duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
          </button>
          <button
            @click="handleNext"
            class="h-12 w-12 rounded-full bg-esmerald-light flex items-center justify-center group hover:bg-esmerald transition-colors"
          >
            <svg class="h-6 w-6 text-esmerald group-hover:text-bone group-hover:-rotate-12 transition-all duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import gsap from 'gsap'

const props = defineProps({
  testimonials: {
    type: Array,
    required: true
  },
  autoplay: {
    type: Boolean,
    default: false
  },
  className: {
    type: String,
    default: ''
  },
  visitProjectText: {
    type: String,
    default: 'Visit Project'
  },
  watchVideoText: {
    type: String,
    default: 'Watch video'
  }
})

const emit = defineEmits(['watch-video'])

const active = ref(0)
const imageRefs = ref([])
const contentRef = ref(null)
const wordRefs = ref([])
const isHovered = ref(false)
let autoplayInterval = null

const currentQuoteWords = computed(() => {
  return props.testimonials[active.value].quote.split(' ')
})

const isActive = (index) => {
  return index === active.value
}

const randomRotateY = () => {
  return Math.floor(Math.random() * 21) - 10
}

const handleNext = () => {
  active.value = (active.value + 1) % props.testimonials.length
}

const handlePrev = () => {
  active.value = (active.value - 1 + props.testimonials.length) % props.testimonials.length
}

const startAutoplay = () => {
  if (props.autoplay && !autoplayInterval) {
    autoplayInterval = setInterval(() => {
      if (!isHovered.value) {
        handleNext()
      }
    }, 6000)
  }
}

const stopAutoplay = () => {
  if (autoplayInterval) {
    clearInterval(autoplayInterval)
    autoplayInterval = null
  }
}

const handleMouseEnter = () => {
  isHovered.value = true
}

const handleMouseLeave = () => {
  isHovered.value = false
}

const animateImages = () => {
  imageRefs.value.forEach((el, index) => {
    if (!el) return
    
    if (isActive(index)) {
      gsap.fromTo(el,
        {
          opacity: 0,
          scale: 0.9,
          rotateY: randomRotateY(),
          z: -100
        },
        {
          opacity: 1,
          scale: 1,
          rotateY: 0,
          z: 0,
          y: 0,
          duration: 0.4,
          ease: 'power2.out',
          onStart: () => {
            gsap.to(el, {
              y: -80,
              duration: 0.2,
              yoyo: true,
              repeat: 1,
              ease: 'power1.inOut'
            })
          }
        }
      )
    } else {
      gsap.to(el, {
        opacity: 0.7,
        scale: 0.95,
        z: -100,
        duration: 0.4,
        ease: 'power2.out'
      })
    }
  })
}

const animateContent = async () => {
  await nextTick()
  
  if (contentRef.value) {
    gsap.fromTo(contentRef.value,
      { y: 20, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.2, ease: 'power2.out' }
    )
  }
  
  if (wordRefs.value.length > 0) {
    wordRefs.value.forEach((word, index) => {
      if (word) {
        gsap.fromTo(word,
          {
            filter: 'blur(10px)',
            opacity: 0,
            y: 5
          },
          {
            filter: 'blur(0px)',
            opacity: 1,
            y: 0,
            duration: 0.2,
            delay: 0.02 * index,
            ease: 'power2.out'
          }
        )
      }
    })
  }
}

watch(active, () => {
  animateImages()
  animateContent()
})

onMounted(() => {
  animateImages()
  animateContent()
  startAutoplay()
})

onBeforeUnmount(() => {
  stopAutoplay()
})
</script>

<style scoped>
.showcase-stack {
  position: relative;
  width: 100%;
  height: 100%;
}

.showcase-card {
  position: absolute;
  width: 55%;
  height: 80%;
  border-radius: 1rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.18), 0 8px 24px -8px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.showcase-video {
  top: 5%;
  left: 5%;
  transform: rotate(-8deg);
  z-index: 2;
  cursor: pointer;
}

.showcase-video:hover {
  transform: rotate(-4deg) scale(1.03);
}

.showcase-mockup {
  top: 10%;
  right: 5%;
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
  .showcase-card {
    width: 60%;
    height: 75%;
  }
}
</style>
