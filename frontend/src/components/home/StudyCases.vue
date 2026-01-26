<template>
  <section class="w-full mt-12 mb-40 px-6 lg:px-32 lg:mt-16">
    <div class="max-w-7xl mx-auto">
      <!-- Section Header -->
      <div class="mb-16 -ml-8 lg:-ml-44">
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
  return messages.value?.study_cases?.cases || [
    {
      quote: "Top 3 SEO rankings achieved. 70% reduction in ad spend with increased organic traffic. Our photography studio now dominates local search results.",
      name: "Obsesd Photography Studio",
      designation: "Photography & Creative Services",
      src: "https://images.unsplash.com/photo-1542038784456-1ea8e935640e?q=80&w=3540&auto=format&fit=crop"
    },
    {
      quote: "+85% increase in direct bookings with optimized conversion funnel and precise targeting. Our luxury hotel brand now converts visitors into guests seamlessly.",
      name: "Constance Hotels",
      designation: "Luxury Hospitality",
      src: "https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=3540&auto=format&fit=crop"
    },
    {
      quote: "Modern e-commerce experience with +120% increase in online sales and improved customer retention. Our lighting business transformed into a digital powerhouse.",
      name: "Luminaire Authentik",
      designation: "E-commerce & Retail",
      src: "https://images.unsplash.com/photo-1524758631624-e2822e304c36?q=80&w=3540&auto=format&fit=crop"
    },
    {
      quote: "Complete digital transformation with custom CRM integration. Streamlined operations led to 60% faster project delivery and happier clients.",
      name: "BuildPro Construction",
      designation: "Construction & Real Estate",
      src: "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=3540&auto=format&fit=crop"
    },
    {
      quote: "Revolutionary booking platform that increased customer engagement by 200%. Our wellness center now manages appointments effortlessly with zero double-bookings.",
      name: "Zen Wellness Spa",
      designation: "Health & Wellness",
      src: "https://images.unsplash.com/photo-1540555700478-4be289fbecef?q=80&w=3540&auto=format&fit=crop"
    }
  ]
})
</script>
