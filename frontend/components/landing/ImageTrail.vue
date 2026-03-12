<template>
  <div
    ref="containerRef"
    class="relative w-full h-full"
    @mousemove="onMouseMove"
    @touchmove="onTouchMove"
  >
    <div ref="trailRef" class="absolute inset-0 pointer-events-none overflow-hidden" />
    <slot />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

import imgApp1 from '~/assets/images/home/hero/mobile-apps/app-1.webp'
import imgApp2 from '~/assets/images/home/hero/mobile-apps/app-2.webp'
import imgApp3 from '~/assets/images/home/hero/mobile-apps/app-3.webp'
import imgApp4 from '~/assets/images/home/hero/mobile-apps/app-4.webp'
import imgApp5 from '~/assets/images/home/hero/mobile-apps/app-5.webp'
import imgApp6 from '~/assets/images/home/hero/mobile-apps/app-6.webp'
import imgApp7 from '~/assets/images/home/hero/mobile-apps/app-7.webp'
import imgApp8 from '~/assets/images/home/hero/mobile-apps/app-8.webp'

const props = defineProps({
  images: {
    type: Array,
    default: () => [imgApp1, imgApp2, imgApp3, imgApp4, imgApp5, imgApp6, imgApp7, imgApp8]
  },
  interval: { type: Number, default: 120 },
  rotationRange: { type: Number, default: 20 },
  imageSize: { type: Number, default: 140 }
})

const containerRef = ref(null)
const trailRef = ref(null)

let lastX = 0
let lastY = 0
let lastTime = 0
let currentIndex = 0
let gsapModule = null

const spawnImage = async (x, y) => {
  if (!trailRef.value || !gsapModule) return

  const gsap = gsapModule.default || gsapModule

  const rect = containerRef.value.getBoundingClientRect()
  const localX = x - rect.left
  const localY = y - rect.top

  const img = document.createElement('img')
  img.src = props.images[currentIndex % props.images.length]
  img.alt = ''
  img.draggable = false
  img.style.cssText = `
    position: absolute;
    left: ${localX - props.imageSize / 2}px;
    top: ${localY - props.imageSize / 2}px;
    width: ${props.imageSize}px;
    height: ${props.imageSize}px;
    object-fit: cover;
    border-radius: 16px;
    pointer-events: none;
    will-change: transform, opacity;
    z-index: ${currentIndex};
  `

  trailRef.value.appendChild(img)
  currentIndex++

  const rotation = (Math.random() - 0.5) * props.rotationRange * 2

  gsap.set(img, { scale: 0, rotation, opacity: 0 })

  gsap.to(img, {
    scale: 1,
    opacity: 1,
    duration: 0.25,
    ease: 'back.out(1.4)',
    onComplete: () => {
      gsap.to(img, {
        scale: 0,
        opacity: 0,
        duration: 0.5,
        delay: 0.4,
        ease: 'power2.in',
        onComplete: () => {
          if (img.parentNode) img.parentNode.removeChild(img)
        }
      })
    }
  })
}

const onMouseMove = (e) => {
  const now = Date.now()
  if (now - lastTime < props.interval) return

  const dx = e.clientX - lastX
  const dy = e.clientY - lastY
  const dist = Math.sqrt(dx * dx + dy * dy)

  if (dist < 20) return

  lastX = e.clientX
  lastY = e.clientY
  lastTime = now
  spawnImage(e.clientX, e.clientY)
}

const onTouchMove = (e) => {
  const touch = e.touches[0]
  if (!touch) return
  const now = Date.now()
  if (now - lastTime < props.interval) return

  const dx = touch.clientX - lastX
  const dy = touch.clientY - lastY
  const dist = Math.sqrt(dx * dx + dy * dy)

  if (dist < 20) return

  lastX = touch.clientX
  lastY = touch.clientY
  lastTime = now
  spawnImage(touch.clientX, touch.clientY)
}

onMounted(async () => {
  gsapModule = await import('gsap')
})

onBeforeUnmount(() => {
  if (trailRef.value) {
    trailRef.value.innerHTML = ''
  }
})
</script>
