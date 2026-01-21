<template>
  <section class="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br from-slate-50 via-white to-slate-100">
    <div class="container mx-auto px-6 lg:px-16 py-20 lg:py-0">
      <div class="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
        
        <!-- Left Column - Copy -->
        <div class="space-y-8 lg:space-y-10">
          <!-- Main Headline -->
          <h1 class="text-5xl lg:text-7xl font-bold text-slate-900 leading-tight">
            {{ messages?.hero?.title_part1 || 'Your Trusted' }}
            <span class="block text-esmerald mt-2">
              {{ messages?.hero?.title_part2 || 'Web Design Partner' }}
            </span>
          </h1>

          <!-- Subheadline -->
          <p class="text-xl lg:text-2xl text-slate-600 leading-relaxed max-w-xl" v-html="messages?.hero?.subtitle || 'We design high-converting websites that increase retention, boost SEO rankings, and drive measurable business growth.'">
          </p>

          <!-- CTA Buttons -->
          <div class="flex flex-wrap gap-3 lg:gap-4">
            <!-- Get In Touch - Yellow Primary -->
            <button class="px-6 py-3 bg-lemon text-black rounded-full font-semibold text-base hover:bg-lemon/90 transition-all hover:scale-105 shadow-md hover:shadow-lg">
              {{ messages?.hero?.cta_primary || 'Get In Touch' }}
            </button>
            
            <!-- Book a Call - Transparent with border connected to Cal.com -->
            <button
              class="px-6 py-3 bg-transparent text-esmerald border-2 border-esmerald-light rounded-full font-medium text-base hover:bg-esmerald-light/30 transition-all flex items-center gap-2"
              data-cal-link="projectapp/discovery-call-projectapp"
              data-cal-namespace="discovery-call-projectapp"
              data-cal-config='{"layout":"week_view","theme":"dark"}'
            >
              {{ messages?.hero?.cta_book_call || 'Book a Call' }}
            </button>
            
            <!-- Email - Transparent with border -->
            <button class="px-6 py-3 bg-transparent text-esmerald border-2 border-esmerald-light rounded-full font-medium text-base hover:bg-esmerald-light/30 transition-all flex items-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
              {{ messages?.hero?.cta_email || 'Email' }}
            </button>
            
            <!-- WhatsApp - Transparent with border -->
            <button class="px-6 py-3 bg-transparent text-esmerald border-2 border-esmerald-light rounded-full font-medium text-base hover:bg-esmerald-light/30 transition-all flex items-center gap-2">
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
              </svg>
              {{ messages?.hero?.cta_whatsapp || 'WhatsApp' }}
            </button>
          </div>

          <!-- Key Benefits List -->
          <div class="space-y-4 pt-6">
            <div class="flex items-start gap-3">
              <svg class="w-6 h-6 text-esmerald flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              <div>
                <p class="text-lg font-semibold text-slate-900">{{ messages?.hero?.benefit1_title || 'Conversion-Optimized Design' }}</p>
                <p class="text-slate-600">{{ messages?.hero?.benefit1_text || 'Every element designed to turn visitors into customers' }}</p>
              </div>
            </div>

            <div class="flex items-start gap-3">
              <svg class="w-6 h-6 text-esmerald flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              <div>
                <p class="text-lg font-semibold text-slate-900">{{ messages?.hero?.benefit2_title || 'Lightning-Fast Performance' }}</p>
                <p class="text-slate-600">{{ messages?.hero?.benefit2_text || 'Optimized for Core Web Vitals and SEO rankings' }}</p>
              </div>
            </div>

            <div class="flex items-start gap-3">
              <svg class="w-6 h-6 text-esmerald flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              <div>
                <p class="text-lg font-semibold text-slate-900">{{ messages?.hero?.benefit3_title || 'Data-Driven UX' }}</p>
                <p class="text-slate-600">{{ messages?.hero?.benefit3_text || 'User experience backed by analytics and testing' }}</p>
              </div>
            </div>

            <div class="flex items-start gap-3">
              <svg class="w-6 h-6 text-esmerald flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              <div>
                <p class="text-lg font-semibold text-slate-900">{{ messages?.hero?.benefit4_title || 'Mobile-First Approach' }}</p>
                <p class="text-slate-600">{{ messages?.hero?.benefit4_text || 'Perfect experience on every device and screen size' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column - Success Stories Carousel -->
        <div class="relative lg:block">
          <!-- Swiper Container -->
          <swiper
            :modules="modules"
            :slides-per-view="1"
            :space-between="20"
            :pagination="{ clickable: true }"
            :autoplay="{ delay: 5000, disableOnInteraction: false }"
            class="success-stories-swiper"
          >
            <!-- Slide 1: Obsesd -->
            <swiper-slide>
              <div class="bg-white rounded-2xl shadow-lg overflow-hidden border border-slate-100 mx-auto max-w-2xl">
                <div class="h-full flex flex-col">
                  <!-- Image -->
                  <div class="h-96 overflow-hidden">
                    <picture>
                      <source media="(min-width: 1024px)" srcset="@/assets/images/hero/Obsesd-Desk.jpg">
                      <img 
                        src="@/assets/images/hero/Obsesd-Mob.jpg" 
                        alt="Obsesd Photography Studio"
                        class="w-full h-full object-cover"
                      />
                    </picture>
                  </div>
                  
                  <!-- Content -->
                  <div class="p-8 flex flex-col justify-between flex-grow bg-white">
                    <div class="space-y-5">
                      <h3 class="text-xl font-light text-esmerald tracking-wide">{{ messages?.hero?.carousel?.obsesd?.title || 'Obsesd' }}</h3>
                      
                      <!-- Before -->
                      <div>
                        <p class="inline-block text-sm font-medium text-esmerald px-2 py-1 bg-lemon/30 mb-2">
                          {{ messages?.hero?.carousel?.before || 'Before' }}
                        </p>
                        <p class="text-slate-600 text-sm leading-relaxed">{{ messages?.hero?.carousel?.obsesd?.before || 'High ad spend with poor SEO visibility. Difficult for customers to find organically.' }}</p>
                      </div>
                      
                      <!-- After -->
                      <div>
                        <p class="inline-block text-sm font-medium text-esmerald px-2 py-1 bg-lemon/30 mb-2">
                          {{ messages?.hero?.carousel?.after || 'After' }}
                        </p>
                        <p class="text-slate-600 text-sm leading-relaxed">{{ messages?.hero?.carousel?.obsesd?.after || 'Top 3 SEO rankings. 70% reduction in ad spend with increased organic traffic.' }}</p>
                      </div>
                    </div>
                    
                    <!-- Visit Resource Link -->
                    <a href="https://www.obsesd.dk/" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-2 text-esmerald text-sm font-light hover:gap-3 transition-all group mt-6">
                      {{ messages?.hero?.carousel?.visit_resource || 'Visit Resource' }}
                      <svg class="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/>
                      </svg>
                    </a>
                  </div>
                </div>
              </div>
            </swiper-slide>

            <!-- Slide 2: Constance Hotels -->
            <swiper-slide>
              <div class="bg-white rounded-2xl shadow-lg overflow-hidden border border-slate-100 mx-auto max-w-2xl">
                <div class="h-full flex flex-col">
                  <!-- Image -->
                  <div class="h-96 overflow-hidden">
                    <picture>
                      <source media="(min-width: 1024px)" srcset="@/assets/images/hero/Constance-Hotels-Desk.jpg">
                      <img 
                        src="@/assets/images/hero/Constance-Hotels-Mob.jpg" 
                        alt="Constance Hotels"
                        class="w-full h-full object-cover"
                      />
                    </picture>
                  </div>
                  
                  <!-- Content -->
                  <div class="p-8 flex flex-col justify-between flex-grow bg-white">
                    <div class="space-y-5">
                      <h3 class="text-xl font-light text-esmerald tracking-wide">{{ messages?.hero?.carousel?.constance?.title || 'Constance Hotels' }}</h3>
                      
                      <!-- Before -->
                      <div>
                        <p class="inline-block text-sm font-medium text-esmerald px-2 py-1 bg-lemon/30 mb-2">
                          {{ messages?.hero?.carousel?.before || 'Before' }}
                        </p>
                        <p class="text-slate-600 text-sm leading-relaxed">{{ messages?.hero?.carousel?.constance?.before || 'Low conversion rates, poorly targeted audience, and minimal direct bookings.' }}</p>
                      </div>
                      
                      <!-- After -->
                      <div>
                        <p class="inline-block text-sm font-medium text-esmerald px-2 py-1 bg-lemon/30 mb-2">
                          {{ messages?.hero?.carousel?.after || 'After' }}
                        </p>
                        <p class="text-slate-600 text-sm leading-relaxed">{{ messages?.hero?.carousel?.constance?.after || '+85% increase in direct bookings with optimized conversion funnel and precise targeting.' }}</p>
                      </div>
                    </div>
                    
                    <!-- Visit Resource Link -->
                    <a href="https://www.constancehotels.com/en/" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-2 text-esmerald text-sm font-light hover:gap-3 transition-all group mt-6">
                      {{ messages?.hero?.carousel?.visit_resource || 'Visit Resource' }}
                      <svg class="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/>
                      </svg>
                    </a>
                  </div>
                </div>
              </div>
            </swiper-slide>

            <!-- Slide 3: Luminaire Authentik -->
            <swiper-slide>
              <div class="bg-white rounded-2xl shadow-lg overflow-hidden border border-slate-100 mx-auto max-w-2xl">
                <div class="h-full flex flex-col">
                  <!-- Image -->
                  <div class="h-96 overflow-hidden">
                    <picture>
                      <source media="(min-width: 1024px)" srcset="@/assets/images/hero/Luminaire-Authentik-Desk.jpg">
                      <img 
                        src="@/assets/images/hero/Luminaire-Authentik-Mob.jpg" 
                        alt="Luminaire Authentik"
                        class="w-full h-full object-cover"
                      />
                    </picture>
                  </div>
                  
                  <!-- Content -->
                  <div class="p-8 flex flex-col justify-between flex-grow bg-white">
                    <div class="space-y-5">
                      <h3 class="text-xl font-light text-esmerald tracking-wide">{{ messages?.hero?.carousel?.luminaire?.title || 'Luminaire Authentik' }}</h3>
                      
                      <!-- Before -->
                      <div>
                        <p class="inline-block text-sm font-medium text-esmerald px-2 py-1 bg-lemon/30 mb-2">
                          {{ messages?.hero?.carousel?.before || 'Before' }}
                        </p>
                        <p class="text-slate-600 text-sm leading-relaxed">{{ messages?.hero?.carousel?.luminaire?.before || 'Outdated e-commerce platform with poor user experience and low sales conversion.' }}</p>
                      </div>
                      
                      <!-- After -->
                      <div>
                        <p class="inline-block text-sm font-medium text-esmerald px-2 py-1 bg-lemon/30 mb-2">
                          {{ messages?.hero?.carousel?.after || 'After' }}
                        </p>
                        <p class="text-slate-600 text-sm leading-relaxed">{{ messages?.hero?.carousel?.luminaire?.after || 'Modern e-commerce experience with +120% increase in online sales and improved customer retention.' }}</p>
                      </div>
                    </div>
                    
                    <!-- Visit Resource Link -->
                    <a href="https://luminaireauthentik.com/" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-2 text-esmerald text-sm font-light hover:gap-3 transition-all group mt-6">
                      {{ messages?.hero?.carousel?.visit_resource || 'Visit Resource' }}
                      <svg class="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/>
                      </svg>
                    </a>
                  </div>
                </div>
              </div>
            </swiper-slide>
          </swiper>
        </div>

      </div>
    </div>

    <!-- Background Decorative Elements -->
    <div class="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden">
      <div class="absolute top-20 left-10 w-72 h-72 bg-esmerald/5 rounded-full blur-3xl"></div>
      <div class="absolute bottom-20 right-10 w-96 h-96 bg-orange-200/20 rounded-full blur-3xl"></div>
    </div>
  </section>
</template>

<script setup>
import { Swiper, SwiperSlide } from 'swiper/vue'
import { Pagination, Autoplay } from 'swiper/modules'
import 'swiper/css'
import 'swiper/css/pagination'
import { useMessages } from '@/composables/useMessages'

const { messages } = useMessages()

// Swiper modules
const modules = [Pagination, Autoplay]
</script>

<style scoped>
/* Smooth animations */
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

/* Swiper customization */
.success-stories-swiper {
  padding-bottom: 50px;
}

:deep(.swiper-pagination-bullet) {
  background: #cbd5e1;
  opacity: 1;
  width: 8px;
  height: 8px;
  transition: all 0.3s ease;
}

:deep(.swiper-pagination-bullet-active) {
  background: #002921;
  width: 24px;
  border-radius: 4px;
}
</style>
