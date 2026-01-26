<template>
  <div
    :class="[
      'h-screen w-full relative overflow-hidden top-0 left-0 bg-[linear-gradient(40deg,var(--gradient-background-start),var(--gradient-background-end))]',
      containerClassName
    ]"
  >
    <svg class="hidden">
      <defs>
        <filter id="blurMe">
          <feGaussianBlur
            in="SourceGraphic"
            stdDeviation="10"
            result="blur"
          />
          <feColorMatrix
            in="blur"
            mode="matrix"
            values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -8"
            result="goo"
          />
          <feBlend in="SourceGraphic" in2="goo" />
        </filter>
      </defs>
    </svg>
    <div :class="className">
      <slot></slot>
    </div>
    <div
      :class="[
        'gradients-container h-full w-full blur-lg',
        isSafari ? 'blur-2xl' : '[filter:url(#blurMe)_blur(40px)]'
      ]"
    >
      <div
        :class="[
          'absolute [background:radial-gradient(circle_at_center,_var(--first-color)_0,_var(--first-color)_50%)_no-repeat]',
          '[mix-blend-mode:var(--blending-value)] w-[var(--size)] h-[var(--size)] top-[calc(50%-var(--size)/2)] left-[calc(50%-var(--size)/2)]',
          '[transform-origin:center_center]',
          'animate-first',
          'opacity-100'
        ]"
      ></div>
      <div
        :class="[
          'absolute [background:radial-gradient(circle_at_center,_rgba(var(--second-color),_0.8)_0,_rgba(var(--second-color),_0)_50%)_no-repeat]',
          '[mix-blend-mode:var(--blending-value)] w-[var(--size)] h-[var(--size)] top-[calc(50%-var(--size)/2)] left-[calc(50%-var(--size)/2)]',
          '[transform-origin:calc(50%-400px)]',
          'animate-second',
          'opacity-100'
        ]"
      ></div>
      <div
        :class="[
          'absolute [background:radial-gradient(circle_at_center,_rgba(var(--third-color),_0.8)_0,_rgba(var(--third-color),_0)_50%)_no-repeat]',
          '[mix-blend-mode:var(--blending-value)] w-[var(--size)] h-[var(--size)] top-[calc(50%-var(--size)/2)] left-[calc(50%-var(--size)/2)]',
          '[transform-origin:calc(50%+400px)]',
          'animate-third',
          'opacity-100'
        ]"
      ></div>
      <div
        :class="[
          'absolute [background:radial-gradient(circle_at_center,_rgba(var(--fourth-color),_0.8)_0,_rgba(var(--fourth-color),_0)_50%)_no-repeat]',
          '[mix-blend-mode:var(--blending-value)] w-[var(--size)] h-[var(--size)] top-[calc(50%-var(--size)/2)] left-[calc(50%-var(--size)/2)]',
          '[transform-origin:calc(50%-200px)]',
          'animate-fourth',
          'opacity-70'
        ]"
      ></div>
      <div
        :class="[
          'absolute [background:radial-gradient(circle_at_center,_rgba(var(--fifth-color),_0.8)_0,_rgba(var(--fifth-color),_0)_50%)_no-repeat]',
          '[mix-blend-mode:var(--blending-value)] w-[var(--size)] h-[var(--size)] top-[calc(50%-var(--size)/2)] left-[calc(50%-var(--size)/2)]',
          '[transform-origin:calc(50%-800px)_calc(50%+800px)]',
          'animate-fifth',
          'opacity-100'
        ]"
      ></div>

      <div
        v-if="interactive"
        ref="interactiveRef"
        @mousemove="handleMouseMove"
        :class="[
          'absolute [background:radial-gradient(circle_at_center,_rgba(var(--pointer-color),_0.8)_0,_rgba(var(--pointer-color),_0)_50%)_no-repeat]',
          '[mix-blend-mode:var(--blending-value)] w-full h-full -top-1/2 -left-1/2',
          'opacity-70'
        ]"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'

const props = defineProps({
  gradientBackgroundStart: {
    type: String,
    default: 'rgb(108, 0, 162)'
  },
  gradientBackgroundEnd: {
    type: String,
    default: 'rgb(0, 17, 82)'
  },
  firstColor: {
    type: String,
    default: '18, 113, 255'
  },
  secondColor: {
    type: String,
    default: '221, 74, 255'
  },
  thirdColor: {
    type: String,
    default: '100, 220, 255'
  },
  fourthColor: {
    type: String,
    default: '200, 50, 50'
  },
  fifthColor: {
    type: String,
    default: '180, 180, 50'
  },
  pointerColor: {
    type: String,
    default: '140, 100, 255'
  },
  size: {
    type: String,
    default: '80%'
  },
  blendingValue: {
    type: String,
    default: 'hard-light'
  },
  className: {
    type: String,
    default: ''
  },
  interactive: {
    type: Boolean,
    default: true
  },
  containerClassName: {
    type: String,
    default: ''
  }
})

const interactiveRef = ref(null)
const curX = ref(0)
const curY = ref(0)
const tgX = ref(0)
const tgY = ref(0)
const isSafari = ref(false)

onMounted(() => {
  document.body.style.setProperty('--gradient-background-start', props.gradientBackgroundStart)
  document.body.style.setProperty('--gradient-background-end', props.gradientBackgroundEnd)
  document.body.style.setProperty('--first-color', props.firstColor)
  document.body.style.setProperty('--second-color', props.secondColor)
  document.body.style.setProperty('--third-color', props.thirdColor)
  document.body.style.setProperty('--fourth-color', props.fourthColor)
  document.body.style.setProperty('--fifth-color', props.fifthColor)
  document.body.style.setProperty('--pointer-color', props.pointerColor)
  document.body.style.setProperty('--size', props.size)
  document.body.style.setProperty('--blending-value', props.blendingValue)

  isSafari.value = /^((?!chrome|android).)*safari/i.test(navigator.userAgent)
})

watch([tgX, tgY], () => {
  move()
})

function move() {
  if (!interactiveRef.value) {
    return
  }
  curX.value = curX.value + (tgX.value - curX.value) / 20
  curY.value = curY.value + (tgY.value - curY.value) / 20
  interactiveRef.value.style.transform = `translate(${Math.round(curX.value)}px, ${Math.round(curY.value)}px)`
}

function handleMouseMove(event) {
  if (interactiveRef.value) {
    const rect = interactiveRef.value.getBoundingClientRect()
    tgX.value = event.clientX - rect.left
    tgY.value = event.clientY - rect.top
  }
}
</script>
