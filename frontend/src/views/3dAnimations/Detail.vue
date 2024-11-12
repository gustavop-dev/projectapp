<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-md"
  >
    <div @click="hideModal" class="relative h-full w-full"></div>
    <div
      class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-full h-full max-w-7xl max-h-[90vh] p-4 bg-window-black bg-opacity-40 backdrop-blur-md rounded-xl"
    >
      <div class="relative flex gap-2 left-0">
        <div @click="hideModal" class="w-3 h-3 bg-red-600 rounded-full cursor-pointer"></div>
        <div @click="hideModal" class="w-3 h-3 bg-yellow-600 rounded-full cursor-pointer"></div>
        <div @click="hideModal" class="w-3 h-3 bg-gray-600 rounded-full cursor-pointer"></div>
      </div>

      <!-- Main content container for mobile version -->
      <div v-if="!isDesktop" class="relative h-full w-full flex justify-center items-center">
        <!-- Message for mobile -->
        <div class="relative w-full h-full py-4 flex flex-col gap-4 justify-center items-center">
          <CubeTransparentIcon class="text-esmerald-light h-40 w-40"></CubeTransparentIcon>
          <p class="text-2xl font-regular text-esmerald-light text-center">
            {{ messages.model_3d.mobile_message }}
          </p>
        </div>
      </div>

      <!-- Main content container for desktop version -->
      <div v-if="isDesktop" class="relative h-full w-full flex justify-center items-center">
        <!-- Loading animation -->
        <div v-show="isLoading" class="absolute inset-0 flex items-center justify-center">
          <Vue3Lottie
            :animationData="whiteAnimation"
            :height="500"
            :width="500"
            :loop="true"
            :autoplay="true"
          />
        </div>
        
        <!-- Main content (Dune) -->
        <div v-show="!isLoading" class="relative w-full h-full py-4 flex justify-center items-center">
          <Dune :spline="splineUrl" @loaded="onDuneLoad" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { Vue3Lottie } from "vue3-lottie";
import Dune from "@/components/spline/Backgrounds/Dune.vue";
import whiteAnimation from "@/assets/loading/white.json";
import { CubeTransparentIcon } from "@heroicons/vue/20/solid";
import { useMessages } from '@/composables/useMessages';

const { messages } = useMessages();

// Loading state
const isLoading = ref(true);
// Verification for the device
const isDesktop = ref(window.innerWidth >= 1024);

/**
 * Props received by the component:
 * - visible (Boolean): Controls whether the modal is visible.
 * - splineUrl (String): The URL of the Spline 3D model to display in the modal.
 */
const props = defineProps({
  visible: Boolean,
  splineUrl: String,
});

/**
 * Emits the 'update:visible' event to notify the parent component about visibility changes.
 */
const emit = defineEmits(["update:visible"]);

/**
 * Function to handle when the Dune component has fully loaded.
 * Sets isLoading to false, hiding the loading animation.
 */
const onDuneLoad = () => {
  isLoading.value = false; // Hide loading animation when Dune is loaded
};

/**
 * Hides the modal by emitting the 'update:visible' event with a false value.
 * This notifies the parent component to close the modal.
 */
const hideModal = () => {
  emit("update:visible", false);
};

/**
 * Watcher to reset loading state whenever the modal is opened.
 * Ensures the loading animation shows every time the modal opens.
 */
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      isLoading.value = true; // Reset loading state when modal becomes visible
    }
  }
);
</script>

<style scoped>
.overflow-auto {
  overflow-y: auto;
}
</style>


  
  