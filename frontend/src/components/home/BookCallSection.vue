<template>
  <section class="w-full mt-12 mb-40 px-6 lg:px-32 lg:mt-16">
    <div class="grid lg:grid-cols-2 gap-8 max-w-7xl mx-auto">
      
      <!-- Left Card - Book a Call -->
      <div class="bg-white rounded-3xl p-12 shadow-lg flex flex-col justify-between min-h-[400px]">
        <div>
          <div class="w-32 h-32 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center mb-8">
            <img 
              src="@/assets/images/call/seated-man.webp" 
              alt="Book a call"
              class="w-full h-full object-cover rounded-full"
            />
          </div>
          
          <h2 class="text-4xl lg:text-5xl font-bold text-esmerald mb-4">
            {{ messages?.book_call?.title || 'Book a 15-min intro call' }}
          </h2>
        </div>
        
        <button
          class="px-8 py-4 bg-esmerald text-bone rounded-full font-semibold text-lg hover:bg-esmerald-dark transition-all hover:scale-105 shadow-md hover:shadow-lg inline-flex items-center gap-2 w-fit"
          data-cal-link="projectapp/discovery-call-projectapp"
          data-cal-namespace="discovery-call-projectapp"
          data-cal-config='{"layout":"week_view","theme":"dark"}'
        >
          {{ messages?.book_call?.cta || "LET'S TALK" }}
          <span class="text-xl">•</span>
        </button>
      </div>

      <!-- Right Card - Image Background with Email CTA -->
      <div class="relative rounded-3xl overflow-hidden min-h-[400px] flex items-end p-12">
        <!-- Background Image -->
        <img 
          src="@/assets/images/call/card-book-a-call.webp" 
          alt="Book a call background"
          class="absolute inset-0 w-full h-full object-cover"
        />

        <!-- Email Badge -->
        <a 
          href="mailto:team@projectapp.com"
          class="relative z-10 bg-white rounded-full px-6 py-3 flex items-center gap-3 hover:scale-105 transition-transform shadow-lg"
        >
          <span class="text-3xl">👋</span>
          <div class="text-left">
            <p class="text-xs font-semibold text-esmerald">{{ messages?.book_call?.prefer_email || 'Prefer to email?' }}</p>
            <p class="text-sm font-bold text-esmerald">{{ messages?.book_call?.say_hi || 'Say hi!' }}</p>
          </div>
        </a>
      </div>

    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useLanguageStore } from '@/stores/language'

const languageStore = useLanguageStore()
const { messages: allMessages } = storeToRefs(languageStore)

const messages = computed(() => allMessages.value.home || {})
</script>
