<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-md"
  >
    <div @click="hideModal" class="relative h-full w-full"></div>
    <div
      class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-full h-full max-w-7xl max-h-[90vh] p-4 bg-window-black bg-opacity-40 backdrop-blur-md rounded-xl overflow-auto"
    >
      <div class="relative flex gap-2 left-0">
        <div
          @click="hideModal"
          class="w-3 h-3 bg-red-600 rounded-full cursor-pointer"
        ></div>
        <div
          @click="hideModal"
          class="w-3 h-3 bg-yellow-600 rounded-full cursor-pointer"
        ></div>
        <div
          @click="hideModal"
          class="w-3 h-3 bg-gray-600 rounded-full cursor-pointer"
        ></div>
      </div>
      <div class="relative pb-4 min-h-full flex align-center justify-center">
        <!-- Loading Animation -->
        <div
          v-show="isLoading"
          class="absolute inset-0 flex items-center justify-center"
        >
          <Vue3Lottie
            :animationData="whiteAnimation"
            :height="500"
            :width="500"
            :loop="true"
            :autoplay="true"
          />
        </div>
        
        <!-- Image Content -->
        <div v-show="!isLoading">
          <img
            @load="onImageLoad"
            :src="detailImageUrl"
            alt="Detail"
            class="mt-6 w-full h-auto object-contain rounded-xl"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { Vue3Lottie } from "vue3-lottie";
import whiteAnimation from "@/assets/loading/white.json";

// State to control loading
const isLoading = ref(true);

/**
 * Props received by the component:
 * - visible (Boolean): Controls whether the modal is visible.
 * - detailImageUrl (String): URL of the image to display in the modal.
 */
const props = defineProps({
  visible: Boolean,
  detailImageUrl: String,
});

/**
 * Emits the 'update:visible' event to notify the parent component about visibility changes.
 */
const emit = defineEmits(["update:visible"]);

/**
 * Function to handle when the image has fully loaded.
 */
const onImageLoad = () => {
  // Set isLoading to false immediately once the image has loaded
  isLoading.value = false;
};

/**
 * Hides the modal by emitting the 'update:visible' event with a false value.
 * This notifies the parent component to close the modal.
 */
const hideModal = () => {
  emit("update:visible", false); // Emit an event to hide the modal
};

/**
 * Watcher to reset loading state whenever the modal is opened.
 * This ensures the loading animation shows every time the modal opens.
 */
watch(() => props.visible, (newVal) => {
  if (newVal) {
    isLoading.value = true; // Reset loading state when modal becomes visible
  }
});
</script>

<style scoped>
.overflow-auto {
  overflow-y: auto;
}
</style>

