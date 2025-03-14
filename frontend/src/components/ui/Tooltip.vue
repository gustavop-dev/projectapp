<template>
  <div class="inline-block relative">
    <!-- Trigger element -->
    <div 
      @mouseenter="showTooltip = true" 
      @mouseleave="showTooltip = false"
      class="cursor-help"
    >
      <slot name="trigger">
        <QuestionMarkCircleIcon class="w-5 h-5 text-green-light" />
      </slot>
    </div>

    <!-- Tooltip content with transition -->
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
          'absolute z-10 px-3 py-2 text-sm rounded-lg shadow-lg',
          backgroundColor,
          textColor,
          width,
          positionClasses // Dynamically computed classes
        ]"
      >
        <!-- Default slot for tooltip content -->
        <slot />
        
        <!-- Arrow indicator -->
        <div
          :class="[
            'absolute w-2 h-2 transform rotate-45',
            arrowPositionClasses, // Dynamically computed classes for arrow
            backgroundColor
          ]"
        ></div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { QuestionMarkCircleIcon } from '@heroicons/vue/24/solid'

// Define component props
const props = defineProps({
  position: {
    type: String,
    default: 'top',
    validator: (value) => ['top', 'bottom', 'left', 'right'].includes(value),
  },
  backgroundColor: {
    type: String,
    default: 'bg-esmerald',
  },
  textColor: {
    type: String,
    default: 'text-white',
  },
  width: {
    type: String,
    default: 'max-w-xs', // ~20rem (320px)
  },
})

// Reactive state to show/hide the tooltip
const showTooltip = ref(false)

/**
 * Computed classes for tooltip container based on the `position` prop.
 * - For top/bottom, we use `left-1/2 -translate-x-1/2` to center it horizontally over the trigger.
 * - For left/right, you can similarly adjust to center vertically.
 */
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

/**
 * Computed classes for the arrow based on the `position` prop.
 * - Positions the small square (rotated 45 degrees) so it points toward the trigger.
 */
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
