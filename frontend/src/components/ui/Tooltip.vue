<!-- components/ui/Tooltip.vue -->
<template>
    <div class="inline-block relative">
      <!-- Trigger element with mouseover/mouseout events -->
      <div 
        @mouseenter="showTooltip = true" 
        @mouseleave="showTooltip = false" 
        class="cursor-help"
      >
        <slot name="trigger">
          <QuestionMarkCircleIcon class="w-5 h-5 text-green-light" />
        </slot>
      </div>
      
      <!-- Tooltip content with transition animation -->
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
            position === 'top' ? 'bottom-full mb-2' : 
            position === 'bottom' ? 'top-full mt-2' : 
            position === 'left' ? 'right-full mr-2' : 
            'left-full ml-2',
            'absolute z-10 px-3 py-2 text-sm rounded-lg shadow-lg',
            width, // Usamos la prop width aquí
            backgroundColor,
            textColor
          ]"
        >
          <!-- Content slot -->
          <slot></slot>
          
          <!-- Arrow indicator -->
          <div 
            :class="[
              'absolute w-2 h-2 transform rotate-45',
              position === 'top' ? 'bottom-0 translate-y-1/2' : 
              position === 'bottom' ? 'top-0 -translate-y-1/2' : 
              position === 'left' ? 'right-0 translate-x-1/2' : 
              'left-0 -translate-x-1/2',
              backgroundColor
            ]"
            :style="{ left: position === 'top' || position === 'bottom' ? '50%' : '', 
                     top: position === 'left' || position === 'right' ? '50%' : '' }"
          ></div>
        </div>
      </transition>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  import { QuestionMarkCircleIcon } from '@heroicons/vue/24/solid';
  
  // Component props with defaults
  const props = defineProps({
    position: {
      type: String,
      default: 'top',
      validator: (value) => ['top', 'bottom', 'left', 'right'].includes(value)
    },
    backgroundColor: {
      type: String,
      default: 'bg-esmerald'
    },
    textColor: {
      type: String,
      default: 'text-white'
    },
    width: {
      type: String,
      default: 'max-w-xs' // Por defecto es 20rem (320px)
    }
  });
  
  // Reactive state
  const showTooltip = ref(false);
  </script>