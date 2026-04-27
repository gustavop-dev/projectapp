<template>
  <div ref="rootEl" class="inline-block relative">
    <div
      @pointerenter="handlePointerEnter"
      @pointerleave="handlePointerLeave"
      @click.stop="handleClick"
      class="cursor-help"
    >
      <slot name="trigger">
        <QuestionMarkCircleIcon class="w-5 h-5 text-text-subtle" />
      </slot>
    </div>

    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform scale-95 opacity-0"
      enter-to-class="transform scale-100 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="transform scale-100 opacity-100"
      leave-to-class="transform scale-95 opacity-0"
    >
      <div
        v-if="showTooltip"
        :class="[
          'absolute z-10 px-3 py-2 text-sm rounded-lg shadow-lg whitespace-normal break-words',
          backgroundColor,
          textColor,
          width,
          minWidth,
          positionClasses,
        ]"
      >
        <slot />
        <div
          :class="[
            'absolute w-2 h-2 transform rotate-45',
            arrowPositionClasses,
            backgroundColor,
          ]"
        />
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { QuestionMarkCircleIcon } from '@heroicons/vue/24/outline'
import { onClickOutside } from '@vueuse/core'
import { oneOf } from './propValidators'

const props = defineProps({
  position: {
    type: String,
    default: 'top',
    validator: oneOf(['top', 'bottom', 'left', 'right']),
  },
  backgroundColor: {
    // Default reads as dark grey on light surfaces and stays legible on dark
    // ones. Override per-consumer for branded tooltips.
    type: String,
    default: 'bg-gray-800',
  },
  textColor: {
    type: String,
    default: 'text-white',
  },
  width: {
    type: String,
    default: 'max-w-2xl',
  },
  minWidth: {
    type: String,
    default: 'min-w-[260px] sm:min-w-[420px] lg:min-w-[560px]',
  },
})

const showTooltip = ref(false)
const rootEl = ref(null)
const touchActive = ref(false)

const handlePointerEnter = (e) => {
  if (e.pointerType !== 'touch') showTooltip.value = true
}

const handlePointerLeave = (e) => {
  if (e.pointerType !== 'touch') showTooltip.value = false
}

const handleClick = () => {
  touchActive.value = true
  showTooltip.value = !showTooltip.value
}

onClickOutside(rootEl, () => {
  if (touchActive.value && showTooltip.value) {
    showTooltip.value = false
    touchActive.value = false
  }
})

const positionClasses = computed(() => {
  switch (props.position) {
    case 'top':
      return 'bottom-full mb-2 left-1/2 -translate-x-1/2'
    case 'bottom':
      return 'top-full mt-2 left-1/2 -translate-x-1/2'
    case 'left':
      return 'right-full mr-2 top-1/2 -translate-y-1/2'
    case 'right':
      return 'left-full ml-2 top-1/2 -translate-y-1/2'
    default:
      return ''
  }
})

const arrowPositionClasses = computed(() => {
  switch (props.position) {
    case 'top':
      return 'bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2'
    case 'bottom':
      return 'top-0 left-1/2 -translate-x-1/2 -translate-y-1/2'
    case 'left':
      return 'right-0 top-1/2 -translate-y-1/2 translate-x-1/2'
    case 'right':
      return 'left-0 top-1/2 -translate-y-1/2 -translate-x-1/2'
    default:
      return ''
  }
})
</script>
