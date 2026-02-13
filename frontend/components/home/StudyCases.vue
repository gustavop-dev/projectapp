<template>
  <section class="w-full mt-12 mb-16 lg:mb-40 px-3 lg:px-32 lg:mt-16">
    <div class="max-w-7xl mx-auto">
      <!-- Section Header -->
      <div class="mb-16">
        <h2 class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl 2xl:text-7xl font-light text-esmerald mb-6 leading-tight">
          {{ messages?.study_cases?.title || 'Design and code made Simple' }}
        </h2>
        <p class="text-xl lg:text-2xl text-green-light max-w-3xl">
          {{ messages?.study_cases?.subtitle || 'Our team of experts is here to turn your vision into reality' }}
        </p>
      </div>

      <!-- Animated Testimonials (client-only due to GSAP animations) -->
      <ClientOnly>
        <AnimatedTestimonials 
          :testimonials="caseStudies" 
          :autoplay="true"
          :visit-project-text="messages?.study_cases?.visit_project || 'Visit Project'"
        />
      </ClientOnly>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import AnimatedTestimonials from '~/components/ui/AnimatedTestimonials.vue'
import { useMessages } from '~/composables/useMessages'

import imgObsesd from '~/assets/images/studyCases/Obsesd-Portfolio.png'
import imgGM from '~/assets/images/studyCases/G&M-Platform.png'
import imgConstance from '~/assets/images/studyCases/Constance-Hotels.png'
import imgLuminaire from '~/assets/images/studyCases/Lights-Ecommerce.png'

const { messages } = useMessages()

const caseStudies = computed(() => {
  const cases = messages.value?.study_cases?.cases || []
  
  // Map images to each case
  const imageMap = {
    'OBSESD Photography Studio': imgObsesd,
    'G&M Platform': imgGM,
    'Constance Hotels': imgConstance,
    'Luminaire Authentik': imgLuminaire
  }
  
  return cases.map(caseItem => ({
    ...caseItem,
    src: imageMap[caseItem.name] || ''
  }))
})
</script>
