<template>
  <div class="relative h-40">
    <!-- Lottie animation container -->
    <div v-show="isLoading" class="absolute inset-0 flex items-center justify-center">
      <Vue3Lottie 
        :animationData="selectedAnimation" 
        :height="500" 
        :width="500" 
        :loop="true" 
        :autoplay="true" 
      />
    </div>

    <!-- Image displayed once loaded -->
    <img
      v-show="!isLoading"
      :src="src"
      :alt="alt"
      @load="onImageLoad"
      class="w-full h-full object-cover rounded-lg"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { Vue3Lottie } from 'vue3-lottie';
import esmeraldAnimation from '~/assets/loading/esmerald.json';
import whiteAnimation from '~/assets/loading/white.json';

// Define props
const props = defineProps({
  src: {
    type: String,
    required: true
  },
  alt: {
    type: String,
    default: ''
  },
  animationType: {
    type: String,
    default: 'esmerald' // Default to 'esmerald' if no type is provided
  }
});

// State to control loading
const isLoading = ref(true);

// Select the animation based on the animationType prop
const selectedAnimation = computed(() => 
  props.animationType === 'white' ? whiteAnimation : esmeraldAnimation
);

/**
 * Stops the Lottie animation once the image has fully loaded.
 */
const onImageLoad = () => {
  // Set isLoading to false once the image has loaded
  isLoading.value = false;
};
</script>

