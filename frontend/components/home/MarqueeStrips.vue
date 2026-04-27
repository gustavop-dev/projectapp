<template>
  <section class="marquee-section overflow-hidden">
    <div class="marquee-inner">
      <!-- Top strip: dark esmerald background, white text -->
      <div ref="ribbonTop" class="ribbon-wrapper ribbon-wrapper--top">
        <div class="ribbon bg-primary text-white">
          <div class="ribbon-track">
            <span
              v-for="n in 4"
              :key="`top-${n}`"
              class="ribbon-item"
            >
              <span class="asterisk">*</span> {{ messages?.marquee?.line1 || "Let's build something remarkable together!" }} <span class="asterisk">*</span> {{ messages?.marquee?.line2 || 'Creative tech for all.' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Bottom strip: lemon background, dark esmerald text -->
      <div ref="ribbonBottom" class="ribbon-wrapper ribbon-wrapper--bottom">
        <div class="ribbon bg-accent text-text-brand">
          <div class="ribbon-track ribbon-track--reverse">
            <span
              v-for="n in 4"
              :key="`bottom-${n}`"
              class="ribbon-item"
            >
              <span class="asterisk">*</span> {{ messages?.marquee?.line1 || "Let's build something remarkable together!" }} <span class="asterisk">*</span> {{ messages?.marquee?.line2 || 'Creative tech for all.' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMessages } from '~/composables/useMessages'

const { messages } = useMessages()

const ribbonTop = ref(null)
const ribbonBottom = ref(null)

onMounted(async () => {
  if (!import.meta.client) return
  const gsap = (await import('gsap')).default

  if (ribbonTop.value) {
    gsap.from(ribbonTop.value, {
      y: -80,
      opacity: 0,
      duration: 1.1,
      ease: 'power3.out'
    })
  }

  if (ribbonBottom.value) {
    gsap.from(ribbonBottom.value, {
      y: 80,
      opacity: 0,
      duration: 1.1,
      delay: 0.1,
      ease: 'power3.out'
    })
  }
})
</script>

<style scoped>
.marquee-section {
  position: relative;
  width: 100vw;
  padding: 6rem 0;
}

@media (min-width: 768px) {
  .marquee-section {
    padding: 10rem 0;
  }
}

.marquee-inner {
  position: relative;
  height: 0px;
}

.ribbon-wrapper {
  position: absolute;
  left: 50%;
  width: 130%;
  overflow: hidden;
  transform-origin: center center;
}

.ribbon-wrapper--top {
  top: 15%;
  height: 6rem;
  transform: translateX(-50%) rotate(-4deg);
  z-index: 5;
}

.ribbon-wrapper--bottom {
  top: 55%;
  height: 6rem;
  transform: translateX(-50%) rotate(4deg);
  z-index: 10;
}

.ribbon {
  position: relative;
  width: 100%;
}

.ribbon-track {
  display: inline-flex;
  white-space: nowrap;
  animation: ribbon-scroll 25s linear infinite;
}

.ribbon-track--reverse {
  animation-direction: reverse;
  animation-duration: 30s;
}

.ribbon-item {
  font-size: 3.5rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  padding: 0;
}

.asterisk {
  font-size: 6rem;
  font-weight: 700;
  display: inline-block;
  position: relative;
  margin: 0 0.5rem;
  line-height: 1;
  vertical-align: -0.35em;
}

@media (max-width: 768px) {
  .ribbon-item {
    font-size: 2rem;
  }
  
  .asterisk {
    font-size: 2.5rem;
  }
  
  .ribbon {
    padding: 0.75rem 0;
  }
}

@keyframes ribbon-scroll {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-50%);
  }
}
</style>
