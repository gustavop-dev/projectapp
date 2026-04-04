<template>
  <section class="relative lg:min-h-screen flex items-center overflow-hidden">
    <div class="w-full pl-6 pr-0 lg:pl-12 xl:pl-16 pt-20 pb-8 lg:pt-28 lg:pb-0">
      <div class="flex flex-col lg:flex-row items-center gap-8 lg:gap-4">

        <!-- Left Column: Copy -->
        <div class="w-full lg:w-1/2 space-y-6 lg:space-y-10">
          <!-- Main Headline -->
          <h1 class="text-4xl sm:text-5xl md:text-5xl lg:text-5xl xl:text-6xl font-bold text-slate-900 leading-tight">
            {{ messages?.hero?.title_part1 || 'Your Trusted' }}
            <span class="block text-esmerald mt-2">
              {{ messages?.hero?.title_part2 || 'Web Design Partner' }}
            </span>
          </h1>

          <!-- Subheadline -->
          <p class="text-base sm:text-lg lg:text-xl text-slate-600 leading-relaxed max-w-xl" v-html="messages?.hero?.subtitle || 'We design high-converting websites that increase retention, boost SEO rankings, and drive measurable business growth.'">
          </p>

          <!-- CTA Buttons -->
          <div class="flex flex-wrap gap-2 sm:gap-3">
            <a
              v-if="messages?.hero?.cta_whatsapp_url"
              :href="messages.hero.cta_whatsapp_url"
              target="_blank"
              rel="noopener noreferrer"
              @click="trackWhatsAppClick()"
              class="px-4 py-2 sm:px-6 sm:py-3 bg-lemon text-black rounded-full font-semibold text-sm sm:text-base hover:bg-lemon/90 transition-all hover:scale-105 shadow-md hover:shadow-lg"
            >
              {{ messages?.hero?.cta_primary || 'Get In Touch' }}
            </a>
            <button v-else @click="goToContact" class="px-4 py-2 sm:px-6 sm:py-3 bg-lemon text-black rounded-full font-semibold text-sm sm:text-base hover:bg-lemon/90 transition-all hover:scale-105 shadow-md hover:shadow-lg">
              {{ messages?.hero?.cta_primary || 'Get In Touch' }}
            </button>

            <button
              v-if="messages?.hero?.cta_book_call"
              class="px-4 py-2 sm:px-6 sm:py-3 bg-white text-slate-900 rounded-full font-medium text-sm sm:text-base hover:bg-slate-50 transition-all flex items-center gap-2 shadow-sm"
              data-cal-link="projectapp/discovery-call-projectapp"
              data-cal-namespace="discovery-call-projectapp"
              data-cal-config='{"layout":"week_view","theme":"dark"}'
            >
              {{ messages.hero.cta_book_call }}
            </button>

            <button v-if="messages?.hero?.cta_email" @click="goToContact" class="px-4 py-2 sm:px-6 sm:py-3 bg-white text-slate-900 rounded-full font-medium text-sm sm:text-base hover:bg-slate-50 transition-all flex items-center gap-2 shadow-sm">
              <svg class="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
              {{ messages.hero.cta_email }}
            </button>

            <button v-if="!messages?.hero?.cta_whatsapp_url && messages?.hero?.cta_whatsapp" @click="goToWhatsApp" class="px-4 py-2 sm:px-6 sm:py-3 bg-white text-slate-900 rounded-full font-medium text-sm sm:text-base hover:bg-slate-50 transition-all flex items-center gap-2 shadow-sm">
              <svg class="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
              </svg>
              {{ messages.hero.cta_whatsapp }}
            </button>
          </div>

          <!-- Key Benefits Grid -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 pt-4 sm:pt-6">
            <div class="flex items-start gap-3">
              <svg class="w-6 h-6 text-esmerald flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              <div>
                <p class="text-sm sm:text-base font-semibold text-slate-900">{{ messages?.hero?.benefit1_title || 'Conversion-Optimized Design' }}</p>
                <p class="text-xs sm:text-sm text-slate-600">{{ messages?.hero?.benefit1_text || 'Every element designed to turn visitors into customers' }}</p>
              </div>
            </div>

            <div class="flex items-start gap-3">
              <svg class="w-6 h-6 text-esmerald flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              <div>
                <p class="text-sm sm:text-base font-semibold text-slate-900">{{ messages?.hero?.benefit2_title || 'Lightning-Fast Performance' }}</p>
                <p class="text-xs sm:text-sm text-slate-600">{{ messages?.hero?.benefit2_text || 'Optimized for Core Web Vitals and SEO rankings' }}</p>
              </div>
            </div>

            <div class="flex items-start gap-3">
              <svg class="w-6 h-6 text-esmerald flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              <div>
                <p class="text-sm sm:text-base font-semibold text-slate-900">{{ messages?.hero?.benefit3_title || 'Data-Driven UX' }}</p>
                <p class="text-xs sm:text-sm text-slate-600">{{ messages?.hero?.benefit3_text || 'User experience backed by analytics and testing' }}</p>
              </div>
            </div>

            <div class="flex items-start gap-3">
              <svg class="w-6 h-6 text-esmerald flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              <div>
                <p class="text-sm sm:text-base font-semibold text-slate-900">{{ messages?.hero?.benefit4_title || 'Mobile-First Approach' }}</p>
                <p class="text-xs sm:text-sm text-slate-600">{{ messages?.hero?.benefit4_text || 'Perfect experience on every device and screen size' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: Stacked Mockups -->
        <div class="hidden lg:flex w-full lg:w-[55%] xl:w-[58%] justify-end overflow-visible">
          <div class="mockups-container">
            <img
              src="~/assets/images/home/hero/mockup-taptag.png"
              alt="TapTag Platform"
              class="mockup mockup-1"
              loading="lazy"
            />
            <img
              src="~/assets/images/home/hero/mockup-nidatabba.png"
              alt="Nida Tabba E-Commerce"
              class="mockup mockup-2"
              loading="lazy"
            />
            <img
              src="~/assets/images/home/hero/mockup-kore.png"
              alt="Kore Dashboard"
              class="mockup mockup-3"
              loading="lazy"
            />
          </div>
        </div>

      </div>
    </div>

    <!-- Background Decorative Elements -->
    <div class="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden -z-10">
      <div class="absolute top-20 left-10 w-72 h-72 bg-esmerald/5 rounded-full blur-3xl"></div>
      <div class="absolute bottom-20 right-10 w-96 h-96 bg-orange-200/20 rounded-full blur-3xl"></div>
    </div>
  </section>
</template>

<script setup>
import { useMessages } from '~/composables/useMessages'
import { useGtagConversions } from '~/composables/useGtagConversions'

const { messages } = useMessages()
const router = useRouter()
const localePath = useLocalePath()
const { trackWhatsAppClick } = useGtagConversions()

const goToContact = () => {
  router.push(localePath('/contact'))
}

const goToWhatsApp = () => {
  trackWhatsAppClick()
  window.open('https://api.whatsapp.com/send/?phone=573238122373&text&type=phone_number&app_absent=0', '_blank')
}
</script>

<style scoped>
section {
  animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.mockups-container {
  position: relative;
  width: 700px;
  height: 700px;
}

.mockup {
  position: absolute;
  width: 520px;
  border-radius: 1.25rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.18), 0 8px 24px -8px rgba(0, 0, 0, 0.12);
  transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  object-fit: cover;
}

.mockup-1 {
  top: 0%;
  left: 5%;
  transform: rotate(-12deg);
  z-index: 3;
}

.mockup-2 {
  top: 28%;
  left: 25%;
  transform: rotate(8deg);
  z-index: 2;
}

.mockup-3 {
  top: 55%;
  left: 0%;
  transform: rotate(-5deg);
  z-index: 1;
}

.mockup:hover {
  transform: rotate(0deg) scale(1.05);
  z-index: 10;
  box-shadow: 0 30px 60px -12px rgba(0, 0, 0, 0.25);
}

@media (min-width: 1280px) {
  .mockups-container {
    width: 800px;
    height: 780px;
  }
  .mockup {
    width: 580px;
  }
}

@media (min-width: 1536px) {
  .mockups-container {
    width: 900px;
    height: 850px;
  }
  .mockup {
    width: 660px;
  }
}
</style>
