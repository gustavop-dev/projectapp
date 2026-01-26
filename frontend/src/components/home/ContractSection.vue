<template>
  <section class="contract-section mt-12 mb-40 px-3 lg:px-32 lg:mt-16">
    <div class="max-w-7xl mx-auto">
      
      <!-- Grid: 3 columns, first empty, second and third merged -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <!-- Column 1: Video with Play Reel button -->
        <div class="hidden lg:block">
          <div class="relative rounded-3xl overflow-hidden h-full min-h-[500px] bg-esmerald">
            <!-- Video autoplay loop -->
            <video
              :src="videoMobile"
              autoplay
              loop
              muted
              playsinline
              preload="auto"
              data-no-optimize="true"
              class="absolute inset-0 w-full h-full object-cover"
            ></video>
            
            <!-- Play Reel Button -->
            <div class="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-10">
              <button
                @click="openVideoModal"
                class="bg-gray-400/40 backdrop-blur-md text-white px-6 py-3 rounded-full font-semibold hover:bg-gray-400/50 transition-all flex items-center gap-2"
              >
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"/>
                </svg>
                {{ messages?.contract?.playReel || 'Play Reel' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Columns 2-3: Card with background image -->
        <div class="lg:col-span-2">
          <div 
            class="contract-card rounded-3xl p-8 lg:p-12 relative overflow-hidden min-h-[500px] bg-cover bg-center"
            :style="{ backgroundImage: `url(${cardBgImage})` }"
          >
            <!-- Content -->
            <div class="relative z-10 text-white h-full flex flex-col justify-between">
              
              <!-- Header -->
              <div>
                <h2 class="text-5xl lg:text-7xl font-bold mb-4">
                  <span ref="typewriterText" class="inline-block typewriter-cursor"></span><br>
                  Design
                </h2>
                
                <!-- Price -->
                <div class="mb-8">
                  <span class="text-4xl lg:text-5xl font-bold">{{ messages?.contract?.price || '$999' }}</span>
                  <span class="text-2xl lg:text-3xl line-through opacity-70 ml-2">{{ messages?.contract?.oldPrice || '$1499' }}</span>
                  <p class="text-xl lg:text-2xl mt-2">{{ messages?.contract?.priceSubtitle || 'Single Price. All included.' }}</p>
                </div>
              </div>

              <!-- Features Box -->
              <div class="bg-white/10 backdrop-blur-sm rounded-2xl p-6 lg:p-8">
                <h3 class="text-lg font-semibold mb-6 opacity-90">{{ messages?.contract?.featuresTitle || 'Code Included' }}</h3>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <!-- Left column features -->
                  <div class="space-y-3">
                    <p class="text-sm lg:text-base">{{ messages?.contract?.feature1 || 'Landing UI Design' }}</p>
                    <p class="text-sm lg:text-base">{{ messages?.contract?.feature2 || 'Mobile Responsive Design' }}</p>
                    <p class="text-sm lg:text-base">{{ messages?.contract?.feature3 || 'Initial Consultation' }}</p>
                  </div>
                  
                  <!-- Right column features -->
                  <div class="space-y-3">
                    <p class="text-sm lg:text-base">{{ messages?.contract?.feature4 || 'Up to 3 rounds of revisions' }}</p>
                    <p class="text-sm lg:text-base">{{ messages?.contract?.feature5 || 'Timely Delivery (2-3 days)' }}</p>
                    <p class="text-sm lg:text-base">{{ messages?.contract?.feature6 || 'Cost-Effective' }}</p>
                  </div>
                </div>

                <!-- CTA Button -->
                <div class="mt-8 flex justify-end">
                  <button class="bg-black text-white px-8 py-3 rounded-full font-semibold hover:bg-gray-800 transition-colors flex items-center gap-2">
                    {{ messages?.contract?.cta || "LET'S TALK" }}
                    <span class="text-xl">•</span>
                  </button>
                </div>
              </div>

            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- Video Modal -->
    <VideoModal
      :is-open="isVideoModalOpen"
      :video-src="videoPresentation"
      @close="closeVideoModal"
    />
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMessages } from '@/composables/useMessages'
import VideoModal from '@/components/VideoModal.vue'
import gsap from 'gsap'
import { TextPlugin } from 'gsap/TextPlugin'

gsap.registerPlugin(TextPlugin)

const { messages } = useMessages()

const cardBgImage = new URL('@/assets/images/home/services/contract/card-landing-design.webp', import.meta.url).href
const videoMobile = new URL('@/assets/videos/presentationMobile.mp4', import.meta.url).href
const videoPresentation = new URL('@/assets/videos/presentationComp.mp4', import.meta.url).href

// Video modal state
const isVideoModalOpen = ref(false)

const openVideoModal = () => {
  isVideoModalOpen.value = true
}

const closeVideoModal = () => {
  isVideoModalOpen.value = false
}

// Typewriter animation usando GSAP TextPlugin
const typewriterText = ref(null)
const words = ['Landing', 'Store', 'Web', 'Platform']

const typewriterAnimation = () => {
  if (!typewriterText.value) return

  const tl = gsap.timeline({
    repeat: -1,
    repeatDelay: 0.5
  })

  words.forEach((word) => {
    // Escribir palabra (de izquierda a derecha)
    tl.to(typewriterText.value, {
      duration: word.length * 0.12,
      text: word,
      ease: 'none'
    })

    // Pausa con la palabra completa
    tl.to({}, { duration: 1 })

    // Borrar palabra de derecha a izquierda
    const proxy = { length: word.length }
    tl.to(proxy, {
      length: 0,
      duration: word.length * 0.08,
      ease: 'none',
      onUpdate() {
        const currentLength = Math.round(proxy.length)
        typewriterText.value.textContent = word.substring(0, currentLength)
      }
    })
  })
}

onMounted(() => {
  typewriterAnimation()
})
</script>

<style scoped>
.contract-section {
  position: relative;
}

/* Ensure text is readable on all screen sizes */
@media (max-width: 768px) {
  .contract-card {
    min-height: 600px;
  }
}

/* Blinking cursor animation using border */
.typewriter-cursor {
  border-right: 5px solid white;
  animation: blink 0.8s step-end infinite;
  padding-right: 2px;
}

@keyframes blink {
  0%, 100% {
    border-color: white;
  }
  50% {
    border-color: transparent;
  }
}
</style>
