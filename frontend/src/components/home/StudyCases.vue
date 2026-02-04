<template>
  <section class="w-full mt-12 mb-40 px-3 lg:px-32 lg:mt-16">
    <div class="max-w-7xl mx-auto">
      <!-- Section Header -->
      <div class="mb-16">
        <h2 class="text-5xl lg:text-7xl font-light text-esmerald mb-6 leading-tight">
          {{ messages?.study_cases?.title || 'Design and code made Simple' }}
        </h2>
        <p class="text-xl lg:text-2xl text-green-light max-w-3xl">
          {{ messages?.study_cases?.subtitle || 'Our team of experts is here to turn your vision into reality' }}
        </p>
      </div>

      <!-- Animated Testimonials -->
      <AnimatedTestimonials 
        :testimonials="caseStudies" 
        :autoplay="true"
        :visit-project-text="messages?.study_cases?.visit_project || 'Visit Project'"
      />
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useLanguageStore } from '@/stores/language'
import AnimatedTestimonials from '@/components/ui/AnimatedTestimonials.vue'

const languageStore = useLanguageStore()
const { messages: allMessages } = storeToRefs(languageStore)

const messages = computed(() => allMessages.value.home || {})

const caseStudies = computed(() => {
  const cases = messages.value?.study_cases?.cases || []
  
  // Map images to each case
  const imageMap = {
    'OBSESD Photography Studio': new URL('@/assets/images/studyCases/Obsesd-Portfolio.png', import.meta.url).href,
    'G&M Platform': new URL('@/assets/images/studyCases/G&M-Platform.png', import.meta.url).href,
    'Constance Hotels': new URL('@/assets/images/studyCases/Constance-Hotels.png', import.meta.url).href,
    'Luminaire Authentik': new URL('@/assets/images/studyCases/Lights-Ecommerce.png', import.meta.url).href
  }
  
  return cases.map(caseItem => ({
    ...caseItem,
    src: imageMap[caseItem.name] || ''
  }))
})
</script>
