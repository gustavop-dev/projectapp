<template>
  <section class="py-12 relative overflow-hidden">
    <div class="container mx-auto px-6 flex justify-center">
      <!-- Single Tech Bubble with all icons -->
      <div class="tech-bubble">
        <img 
          src="@/assets/images/icons/figma.svg" 
          alt="Figma"
          class="w-24 h-24 md:w-32 md:h-32 transition-transform hover:scale-110"
        />
        <img 
          src="@/assets/images/icons/webflow.svg" 
          alt="Webflow"
          class="w-24 h-24 md:w-32 md:h-32 transition-transform hover:scale-110"
        />
        <img 
          src="@/assets/images/icons/astro.svg" 
          alt="Astro"
          class="w-24 h-24 md:w-32 md:h-32 transition-transform hover:scale-110"
        />
        <img 
          src="@/assets/images/icons/stripe.svg" 
          alt="Stripe"
          class="w-24 h-24 md:w-32 md:h-32 transition-transform hover:scale-110"
        />
        <img 
          src="@/assets/images/icons/framer.svg" 
          alt="Framer"
          class="w-24 h-24 md:w-32 md:h-32 transition-transform hover:scale-110"
        />
        <img 
          src="@/assets/images/icons/vuejs_logo_icon_169247.svg" 
          alt="Vue.js"
          class="w-24 h-24 md:w-32 md:h-32 transition-transform hover:scale-110"
        />
        <img 
          src="@/assets/images/icons/pngwing.com.png" 
          alt="Technology"
          class="w-24 h-24 md:w-32 md:h-32 transition-transform hover:scale-110"
        />
      </div>
    </div>
  </section>
</template>

<script setup>
import { useMessages } from '@/composables/useMessages'

const { messages } = useMessages()
</script>

<style scoped>
.tech-bubble {
  display: flex;
  align-items: center;
  gap: 40px;
  padding: 36px 60px;
  background: #ffffff;
  border-radius: 80px;
  box-shadow: 
    0 8px 16px rgba(0, 0, 0, 0.08),
    0 4px 8px rgba(0, 0, 0, 0.06),
    inset 0 -2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  cursor: default;
}

.tech-bubble:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 12px 24px rgba(0, 0, 0, 0.1),
    0 6px 12px rgba(0, 0, 0, 0.08),
    inset 0 -2px 4px rgba(0, 0, 0, 0.05);
}

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
</style>
