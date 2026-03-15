<template>
  <section class="py-6 sm:py-8 lg:py-12 relative overflow-hidden">
    <div class="container mx-auto px-6 flex justify-center">
      <!-- Single Tech Bubble with all icons -->
      <div class="tech-bubble">
        <img 
          src="~/assets/images/icons/figma.svg" 
          alt="Figma"
          class="tech-icon transition-transform hover:scale-110"
        />
        <img 
          src="~/assets/images/icons/webflow.svg" 
          alt="Webflow"
          class="tech-icon transition-transform hover:scale-110"
        />
        <img 
          src="~/assets/images/icons/astro.svg" 
          alt="Astro"
          class="tech-icon transition-transform hover:scale-110"
        />
        <img 
          src="~/assets/images/icons/stripe.svg" 
          alt="Stripe"
          class="tech-icon transition-transform hover:scale-110"
        />
        <img 
          src="~/assets/images/icons/framer.svg" 
          alt="Framer"
          class="tech-icon transition-transform hover:scale-110"
        />
        <img 
          src="~/assets/images/icons/vuejs_logo_icon_169247.svg" 
          alt="Vue.js"
          class="tech-icon transition-transform hover:scale-110"
        />
        <img 
          src="~/assets/images/icons/pngwing.com.png" 
          alt="Technology"
          class="tech-icon transition-transform hover:scale-110"
        />
      </div>
    </div>
  </section>
</template>

<script setup>
import { useMessages } from '~/composables/useMessages'

const { messages } = useMessages()
</script>

<style scoped>
.tech-icon {
  height: 28px;
  width: auto;
  object-fit: contain;
  flex-shrink: 0;
}

@media (min-width: 640px) {
  .tech-icon {
    height: 32px;
  }
}

@media (min-width: 1024px) {
  .tech-icon {
    height: 36px;
  }
}

.tech-bubble {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: center;
  gap: 16px 20px;
  padding: 16px 20px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 
    0 8px 16px rgba(0, 0, 0, 0.08),
    0 4px 8px rgba(0, 0, 0, 0.06),
    inset 0 -2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  cursor: default;
}

@media (min-width: 640px) {
  .tech-bubble {
    gap: 16px 28px;
    padding: 20px 32px;
    border-radius: 28px;
  }
}

@media (min-width: 1024px) {
  .tech-bubble {
    flex-wrap: nowrap;
    gap: 32px;
    padding: 20px 48px;
    border-radius: 60px;
  }
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
