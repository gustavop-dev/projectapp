<template>
  <section class="w-full mt-12 mb-12 lg:mb-16 px-3 lg:px-32 lg:mt-16">
    <div class="max-w-4xl mx-auto">
      <h2
        ref="titleRef"
        class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl 2xl:text-7xl font-bold text-text-brand mb-12 lg:mb-16 leading-tight opacity-0"
      >
        {{ messages?.faq?.title }}
      </h2>

      <div class="space-y-4" ref="faqListRef">
        <details
          v-for="(item, index) in messages?.faq?.questions"
          :key="index"
          class="faq-item group bg-surface rounded-3xl overflow-hidden opacity-0"
          :itemscope="true"
          itemtype="https://schema.org/Question"
        >
          <summary class="flex items-center justify-between gap-4 p-6 lg:p-8 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden">
            <h3 class="text-lg lg:text-xl font-bold text-text-brand pr-4" itemprop="name">
              {{ item.q }}
            </h3>
            <div class="flex-shrink-0 w-10 h-10 rounded-full bg-primary flex items-center justify-center group-open:rotate-180 transition-transform duration-300">
              <svg class="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
              </svg>
            </div>
          </summary>
          <div class="px-6 lg:px-8 pb-6 lg:pb-8" itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
            <p class="text-base lg:text-lg text-green-light leading-relaxed" itemprop="text">
              {{ item.a }}
            </p>
          </div>
        </details>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useMessages } from '~/composables/useMessages'

const { messages } = useMessages()

const titleRef = ref(null)
const faqListRef = ref(null)

const setupAnimations = async () => {
  if (!import.meta.client) return

  const gsap = (await import('gsap')).default
  const { ScrollTrigger } = await import('gsap/ScrollTrigger')
  gsap.registerPlugin(ScrollTrigger)

  if (titleRef.value) {
    gsap.set(titleRef.value, { y: 40 })
    gsap.to(titleRef.value, {
      opacity: 1, y: 0, duration: 1, ease: 'power3.out',
      scrollTrigger: { trigger: titleRef.value, start: 'top 85%', toggleActions: 'play none none reverse' }
    })
  }

  if (faqListRef.value) {
    const items = faqListRef.value.querySelectorAll('.faq-item')
    gsap.set(items, { y: 20 })
    gsap.to(items, {
      opacity: 1, y: 0, duration: 0.6, stagger: 0.1, ease: 'power3.out',
      scrollTrigger: { trigger: faqListRef.value, start: 'top 85%', toggleActions: 'play none none reverse' }
    })
  }
}

onMounted(async () => {
  await nextTick()
  setupAnimations()
})
</script>

<style scoped>
details[open] summary {
  border-bottom: 1px solid rgba(0, 41, 33, 0.1);
}
</style>
