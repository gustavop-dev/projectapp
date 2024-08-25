<template>
  <div>
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar></Navbar>
    </div>
    <section>
      <div class="h-screen p-3">
        <div class="w-full h-full grid rounded-xl overflow-hidden lg:grid-cols-2">
          <div class="bg-brown flex items-center px-16 order-2 py-24">
            <h1>
              <span class="text-4xl font-light text-white lg:text-6xl">{{ messages.intro_section.title_line1 }}</span><br>
              <span class="text-4xl font-light text-white lg:text-6xl">{{ messages.intro_section.title_line2 }}</span><br>
              <span class="text-md font-medium text-white">{{ messages.intro_section.subtitle_line1 }}</span><br>
              <span class="text-md font-medium text-white">{{ messages.intro_section.subtitle_line2 }}</span>
            </h1>
          </div>
          <div class="order-1">
            <Dune spline="/spline/Backgrounds/cats.splinecode"></Dune>
          </div>
        </div>
      </div>
    </section>
    <section class="px-3">
      <div class="mt-32 max-w-7xl mx-auto sm:px-6 lg:px-8 lg:mt-52">
        <h1 class="text-4xl font-light text-esmerald lg:text-6xl">{{ messages.animations_section.section_title }}</h1>
        <h2 class="text-2xl font-light text-esmerald mt-20 lg:text-4xl">{{ messages.animations_section.section_subtitle }}</h2>
        <div class="mt-24 grid gap-4 md:grid-cols-2 lg:grid-cols-4 lg:mt-40">
          <div v-for="model3d in models3d" :key="model3d.id" @click="openModal(model3d.file_url)" class="cursor-pointer">
            <div class="border border-gray-200 rounded-lg">
              <img class="w-full rounded-lg" :src="model3d.image_url" :alt="model3d.title">
            </div>
            <h3 class="mt-4 font-regular text-esmerald text-md">{{ model3d.title }}</h3>
          </div>
        </div>
      </div>
    </section>
    <div class="mt-52">
      <Footer></Footer>
    </div>
    <Detail :visible="isModalVisible" :spline-url="currentSplineUrl" @update:visible="isModalVisible = $event"></Detail>
  </div>
</template>

<script setup>
import { ref, onMounted, defineAsyncComponent } from 'vue'; // Import Vue utilities
import Navbar from '@/components/layouts/Navbar.vue'; // Import the Navbar component
import Footer from '@/components/layouts/Footer.vue'; // Import the Footer component
import Detail from '@/views/3dAnimations/Detail.vue'; // Import the Detail view for 3D animations
import { useModels3dStore } from '@/stores/models-3d'; // Import the models 3D store
import { useMessages } from '@/composables/useMessages'; // Import the custom composable for localized messages

const { messages } = useMessages(); // Destructure the localized messages from the custom composable

// Dynamically import the Dune background component
const Dune = defineAsyncComponent(() =>
  import('@/components/spline/Backgrounds/Dune.vue')
);

// Store for managing 3D models data
const models3dStore = useModels3dStore();
const models3d = ref([]); // Reactive reference to store the list of 3D models

const isModalVisible = ref(false); // State to control the visibility of the modal
const currentSplineUrl = ref(''); // State to store the URL of the current Spline scene

/**
 * Opens a modal to display a Spline 3D model.
 * 
 * @param {string} splineUrl - The URL of the Spline model to display.
 */
const openModal = (splineUrl) => {
  currentSplineUrl.value = splineUrl; // Set the URL of the Spline model to show
  isModalVisible.value = true; // Show the modal
};

/**
 * Lifecycle hook that runs after the component is mounted.
 * 
 * This hook initializes the 3D models store and fetches the models data.
 * The data is then stored in the `models3d` ref.
 */
onMounted(async () => {
  await models3dStore.init(); // Initialize the 3D models store
  models3d.value = models3dStore.getModels3d; // Update the local reactive state with the fetched 3D models
});
</script>

<style scoped>
.loader {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  font-size: 1.5em;
  color: #888;
}
</style>
