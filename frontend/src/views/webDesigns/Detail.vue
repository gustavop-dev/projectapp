<template>
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-md">
        <div @click="hideModal" class="relative h-full w-full"></div>
          <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-full h-full max-w-7xl max-h-[90vh] pt-4 px-8 bg-window-black bg-opacity-40 backdrop-blur-md rounded-xl overflow-auto">
          <div class="relative flex gap-2 left-0">
              <div @click="hideModal" class="w-3 h-3 bg-red-600 rounded-full cursor-pointer"></div>
              <div @click="hideModal" class="w-3 h-3 bg-yellow-600 rounded-full cursor-pointer"></div>
              <div @click="hideModal" class="w-3 h-3 bg-gray-600 rounded-full cursor-pointer"></div>
          </div>
          <div class="flex align-center justify-center">
            <img :src="detailImageUrl" alt="Detail" class="mt-6 w-full h-auto object-contain rounded-xl" />
          </div>
        </div>
    </div>
  </template>
  
  <script setup>
  /**
   * Props received by the component:
   * - visible (Boolean): Controls whether the modal is visible.
   * - detailImageUrl (String): URL of the image to display in the modal.
   */
  const props = defineProps({
    visible: Boolean,
    detailImageUrl: String
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
  
  
<style scoped>
  .overflow-auto {
    overflow-y: auto;
  }
</style>
  