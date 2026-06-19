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
          class="tech-icon tech-icon--webflow transition-transform hover:scale-110"
        />
        <img
          src="~/assets/images/icons/astro.svg"
          alt="Astro"
          class="tech-icon tech-icon--astro transition-transform hover:scale-110"
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
          class="tech-icon tech-icon--vue transition-transform hover:scale-110"
        />
        <img
          src="~/assets/images/icons/pngwing.com.png"
          alt="Django"
          class="tech-icon tech-icon--django transition-transform hover:scale-110"
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
  /* Base height is a variable (set responsively on .tech-bubble) so per-logo
     modifiers can scale relative to it and stay responsive. */
  height: var(--tech-icon-h, 28px);
  width: auto;
  object-fit: contain;
  flex-shrink: 0;
}

/* Per-logo size tweaks — logos have different artwork/whitespace, so a uniform
   height reads unevenly. Multipliers normalise the optical sizes. */
.tech-icon--webflow {
  height: calc(var(--tech-icon-h, 28px) * 0.85);
}
.tech-icon--astro {
  height: calc(var(--tech-icon-h, 28px) * 1.3);
}
.tech-icon--vue {
  height: calc(var(--tech-icon-h, 28px) * 1.25);
}
.tech-icon--django {
  height: calc(var(--tech-icon-h, 28px) * 2);
}

.tech-bubble {
  --tech-icon-h: 28px;
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
    --tech-icon-h: 32px;
    gap: 16px 28px;
    padding: 20px 32px;
    border-radius: 28px;
  }
}

@media (min-width: 1024px) {
  .tech-bubble {
    --tech-icon-h: 36px;
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
