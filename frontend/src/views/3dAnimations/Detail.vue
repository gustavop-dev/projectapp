<template>
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-md">
      <div @click="hideModal" class="relative h-full w-full"></div>
      <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-full h-full max-w-7xl max-h-[90vh] pt-4 px-8 bg-window-black bg-opacity-40 backdrop-blur-md rounded-xl">
        <div class="relative flex gap-2 left-0">
            <div @click="hideModal" class="w-3 h-3 bg-red-600 rounded-full cursor-pointer"></div>
            <div @click="hideModal" class="w-3 h-3 bg-yellow-600 rounded-full cursor-pointer"></div>
            <div @click="hideModal" class="w-3 h-3 bg-gray-600 rounded-full cursor-pointer"></div>
        </div>
        <Dune :spline="splineUrl" />
      </div>
    </div>
  </template>
  
  <script setup>
  import Dune from '@/components/spline/Backgrounds/Dune.vue'; // Import the Dune component (likely a 3D background)
  
  /**
   * Props received by the component:
   * - visible (Boolean): Controls whether the modal is visible.
   * - splineUrl (String): The URL of the Spline 3D model to display in the modal.
   */
  const props = defineProps({
    visible: Boolean,
    splineUrl: String
  });
  
  /**
   * Emits the 'update:visible' event to notify the parent component about visibility changes.
   */
  const emit = defineEmits(['update:visible']);
  
  /**
   * Hides the modal by emitting the 'update:visible' event with a false value.
   * This notifies the parent component to close the modal.
   */
  const hideModal = () => {
    emit('update:visible', false); // Emit an event to hide the modal
  };
  </script>
  
  