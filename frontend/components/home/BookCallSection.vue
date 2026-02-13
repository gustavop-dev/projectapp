<template>
  <section class="w-full mt-12 mb-12 lg:mb-16 px-3 lg:px-32 lg:mt-16">
    <div class="grid lg:grid-cols-2 gap-8 max-w-7xl mx-auto">
      
      <!-- Left Card - Book a Call -->
      <div class="bg-white rounded-3xl p-8 lg:p-12 flex flex-col justify-between min-h-[300px] lg:min-h-[400px]">
        <div>
          <div class="w-32 h-32 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center mb-8">
            <img 
              src="~/assets/images/call/seated-man.webp" 
              alt="Book a call"
              class="w-full h-full object-cover rounded-full"
            />
          </div>
          
          <h2 class="text-xl sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl font-bold text-esmerald mb-4">
            {{ messages?.book_call?.title || 'Book a 15-min intro call' }}
          </h2>
        </div>
        
        <button
          class="px-6 py-3 bg-lemon text-black rounded-full font-semibold text-base hover:bg-lemon/90 transition-all hover:scale-105 shadow-md hover:shadow-lg inline-flex items-center gap-2 w-fit"
          data-cal-link="projectapp/discovery-call-projectapp"
          data-cal-namespace="discovery-call-projectapp"
          data-cal-config='{"layout":"week_view","theme":"dark"}'
        >
          {{ messages?.book_call?.cta || "Let's Talk" }}
          <span class="text-xl">•</span>
        </button>
      </div>

      <!-- Right Card - Image Background with Email CTA -->
      <div class="relative rounded-3xl overflow-hidden min-h-[300px] lg:min-h-[400px] flex items-end p-8 lg:p-12">
        <!-- Background Image -->
        <img 
          src="~/assets/images/call/card-book-a-call.webp" 
          alt="Book a call background"
          class="absolute inset-0 w-full h-full object-cover"
        />

        <!-- Email Badge -->
        <button 
          @click="goToContact"
          class="relative z-10 bg-white rounded-full px-6 py-3 flex items-center gap-3 hover:scale-105 transition-transform shadow-lg cursor-pointer"
        >
          <span class="text-3xl">👋</span>
          <div class="text-left">
            <p class="text-xs font-semibold text-esmerald">{{ messages?.book_call?.prefer_email || 'Prefer to email?' }}</p>
            <p class="text-sm font-bold text-esmerald">{{ messages?.book_call?.say_hi || 'Say hi!' }}</p>
          </div>
        </button>
      </div>

    </div>
  </section>
</template>

<script setup>
import { useMessages } from '~/composables/useMessages'

const router = useRouter()
const localePath = useLocalePath()
const { messages } = useMessages()

const goToContact = () => {
  router.push(localePath('/contact'))
}
</script>
