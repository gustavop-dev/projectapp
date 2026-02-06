<template>
  <section class="unrepeatable-section mt-12 mb-12 px-3 lg:px-32 lg:mt-16">
    <div class="max-w-7xl mx-auto">
      <div class="flex flex-col sm:flex-row items-center justify-start gap-0 relative">
        
        <!-- Left side: Title all light -->
        <div class="flex-shrink-0 z-20">
          <h2 class="unrepeatable-title font-light leading-tight">
            {{ messages?.unrepeatable?.title || 'unrepeatable.' }}
          </h2>
        </div>

        <!-- Center: Image (larger and behind text) -->
        <div class="relative -mt-8 sm:-mt-0 sm:-ml-16 lg:-ml-24 z-10">
          <img 
            :src="beBoldImage" 
            alt="Unrepeatable design"
            class="w-56 sm:w-80 lg:w-[28rem] h-auto transform hover:scale-105 transition-transform duration-300"
          />
          
          <!-- Asterisk on top of image -->
          <span 
            ref="asterisk" 
            class="absolute -top-4 -right-4 sm:-top-8 sm:-right-8 font-black inline-block text-[6rem] sm:text-[9rem] lg:text-[12rem]"
            style="line-height: 1;"
          >
            *
          </span>
        </div>

      </div>

      <!-- Process Section -->
      <div class="process-section mt-12 lg:mt-20">
        <!-- Title -->
        <h3 class="mb-12 text-left">
          <span class="block font-light text-xl sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl 2xl:text-6xl text-esmerald">
            {{ messages?.unrepeatable?.processTitle1 || 'A Thoughtful Process Designed for' }}
          </span>
          <span class="inline-block font-light text-xl sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl 2xl:text-6xl text-black bg-lemon px-2">
            {{ messages?.unrepeatable?.processTitle2 || 'Outstanding Results' }}
          </span>
        </h3>

        <!-- Cards Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          
          <!-- Card 1: Kick Off -->
          <div 
            class="process-card rounded-3xl p-8 text-white relative overflow-hidden min-h-[320px] flex flex-col justify-between bg-cover bg-center"
            :style="{ backgroundImage: `url(${cardImage1})` }"
          >
            <div class="icon-wrapper mb-auto relative z-10 flex justify-center">
              <img :src="iconCoffee" alt="Coffee" class="w-16 h-16 object-contain" />
            </div>
            <div class="relative z-10">
              <h4 class="text-xl font-semibold mb-3">{{ messages?.unrepeatable?.card1Title || 'Architecture & Planning' }}</h4>
              <p class="text-sm text-gray-200 leading-relaxed">
                {{ messages?.unrepeatable?.card1Description || 'We define the complete project structure: site map, user flows, strategic CTAs, required forms, and necessary integrations to achieve your goals.' }}
              </p>
            </div>
          </div>

          <!-- Card 2: IA & Wireframes -->
          <div 
            class="process-card rounded-3xl p-8 text-white relative overflow-hidden min-h-[320px] flex flex-col justify-between bg-cover bg-center"
            :style="{ backgroundImage: `url(${cardImage2})` }"
          >
            <div class="icon-wrapper mb-auto relative z-10 flex justify-center">
              <img :src="iconNotebook" alt="Notebook" class="w-16 h-16 object-contain" />
            </div>
            <div class="relative z-10">
              <h4 class="text-xl font-semibold mb-3">{{ messages?.unrepeatable?.card2Title || 'UI/UX Design' }}</h4>
              <p class="text-sm text-gray-200 leading-relaxed">
                {{ messages?.unrepeatable?.card2Description || 'We create the complete design in Figma for all project views. We work in iterations with you until achieving final design approval.' }}
              </p>
            </div>
          </div>

          <!-- Card 3: Interaction & UI Design -->
          <div 
            class="process-card rounded-3xl p-8 text-white relative overflow-hidden min-h-[320px] flex flex-col justify-between bg-cover bg-center"
            :style="{ backgroundImage: `url(${cardImage3})` }"
          >
            <div class="icon-wrapper mb-auto relative z-10 flex justify-center">
              <img :src="iconPingPong" alt="Ping Pong" class="w-16 h-16 object-contain" />
            </div>
            <div class="relative z-10">
              <h4 class="text-xl font-semibold mb-3">{{ messages?.unrepeatable?.card3Title || 'Development & Implementation' }}</h4>
              <p class="text-sm text-gray-200 leading-relaxed">
                {{ messages?.unrepeatable?.card3Description || 'We implement the approved design, configure CMS if needed, integrate tools (CRM, WhatsApp, analytics), and apply basic technical SEO.' }}
              </p>
            </div>
          </div>

          <!-- Card 4: Client deliverables -->
          <div 
            class="process-card rounded-3xl p-8 text-white relative overflow-hidden min-h-[320px] flex flex-col justify-between bg-cover bg-center"
            :style="{ backgroundImage: `url(${cardImage4})` }"
          >
            <div class="icon-wrapper mb-auto relative z-10 flex justify-center">
              <img :src="iconRocket" alt="Rocket" class="w-16 h-16 object-contain" />
            </div>
            <div class="relative z-10">
              <h4 class="text-xl font-semibold mb-3">{{ messages?.unrepeatable?.card4Title || 'Deployment & Validation' }}</h4>
              <p class="text-sm text-gray-200 leading-relaxed">
                {{ messages?.unrepeatable?.card4Description || 'We publish the project on hosting, perform final tests on forms, integrations, tracking, and performance to ensure everything works perfectly.' }}
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMessages } from '@/composables/useMessages'
import gsap from 'gsap'

const { messages } = useMessages()

const asterisk = ref(null)
const beBoldImage = new URL('@/assets/images/home/services/process/be-bold.webp', import.meta.url).href
const cardImage1 = new URL('@/assets/images/home/services/process/card-be-bold-1.webp', import.meta.url).href
const cardImage2 = new URL('@/assets/images/home/services/process/card-be-bold-2.webp', import.meta.url).href
const cardImage3 = new URL('@/assets/images/home/services/process/card-be-bold-3.webp', import.meta.url).href
const cardImage4 = new URL('@/assets/images/home/services/process/card-be-bold-4.webp', import.meta.url).href
const iconCoffee = new URL('@/assets/images/home/services/process/coffee.webp', import.meta.url).href
const iconNotebook = new URL('@/assets/images/home/services/process/notebook.webp', import.meta.url).href
const iconPingPong = new URL('@/assets/images/home/services/process/ping-pong.webp', import.meta.url).href
const iconRocket = new URL('@/assets/images/home/services/process/rocket.webp', import.meta.url).href

onMounted(() => {
  if (asterisk.value) {
    gsap.to(asterisk.value, {
      rotation: 360,
      duration: 8,
      repeat: -1,
      ease: 'linear'
    })
  }
})
</script>

<style scoped>
.unrepeatable-section {
  position: relative;
  overflow: hidden;
}

.unrepeatable-title {
  color: #1a1a1a;
}

/* Responsive title sizes */
.unrepeatable-title {
  font-size: 2.5rem;
}

@media (min-width: 640px) {
  .unrepeatable-title {
    font-size: 3.5rem;
  }
}

@media (min-width: 768px) {
  .unrepeatable-title {
    font-size: 4rem;
  }
}

@media (min-width: 1024px) {
  .unrepeatable-title {
    font-size: 5rem;
  }
}

@media (min-width: 1280px) {
  .unrepeatable-title {
    font-size: 6rem;
  }
}

@media (min-width: 1536px) {
  .unrepeatable-title {
    font-size: 8rem;
  }
}
</style>
