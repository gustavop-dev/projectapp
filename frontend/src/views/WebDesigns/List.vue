<template>
  <div>
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar></Navbar>
    </div>
    <section>
      <div class="h-screen p-3">
        <div class="w-full h-full grid rounded-xl overflow-hidden lg:grid-cols-2">
          <div class="bg-pink flex items-center px-16 order-2 py-24">
            <h1>
              <span class="text-4xl font-light text-white lg:text-6xl">{{ messages.header_title }}</span><br>
              <span class="text-md font-medium text-white">{{ messages.header_subtitle }}</span>
            </h1>
          </div>
          <div class="order-1">
            <Dune spline="/spline/Backgrounds/webDesign.splinecode"></Dune>
          </div>
        </div>
      </div>
    </section>
    <section class="px-3">
      <div class="mt-32 max-w-7xl mx-auto sm:px-6 lg:mt-52 lg:px-8">
        <h1 class="text-6xl font-light text-esmerald">{{ messages.section_title }}</h1>
        <h2 class="text-4xl font-light text-esmerald mt-20">{{ messages.section_subtitle }}</h2>
        <div class="mt-24 grid gap-4 md:grid-cols-2 lg:grid-cols-4 lg:mt-40">
          <div v-for="design in designs" :key="design.id" @click="openModal(design.detail_image_url)" class="cursor-pointer">
            <div class="border border-gray-200 rounded-lg">
              <img class="w-full rounded-lg" :src="design.presentation_image_url" :alt="design.title">
            </div>
            <h3 class="mt-4 font-regular text-esmerald text-md">{{ design.title }}</h3>
          </div>
        </div>
      </div>
    </section>
    <div class="mt-32 lg:mt-52">
      <Footer></Footer>
    </div>
    <Detail :visible="isModalVisible" :detailImageUrl="currentDetailImageUrl" @update:visible="isModalVisible = $event" />
  </div>
</template>

<script setup>
import Navbar from '@/components/layouts/Navbar.vue'; // Import the Navbar component for the navigation bar
import Dune from '@/components/spline/Backgrounds/Dune.vue'; // Import the Dune component, likely a 3D background
import Footer from '@/components/layouts/Footer.vue'; // Import the Footer component for the website's footer
import Detail from '@/views/WebDesigns/Detail.vue'; // Import the Detail view for web designs
import { useWebDesignsStore } from '@/stores/web-designs'; // Import the web designs store
import { onMounted, ref, computed } from 'vue'; // Import Vue's lifecycle hook, ref for reactivity, and computed
import { useMessages } from '@/composables/useMessages'; // Import the custom composable to get localized messages

const { messages } = useMessages(); // Destructure the localized messages from the custom composable

// Store for managing web designs data
const webDesignsStore = useWebDesignsStore();
const designs = ref([]); // Reactive reference to store the list of designs

const isModalVisible = ref(false); // State to control the visibility of the modal
const currentDetailImageUrl = ref(''); // State to store the URL of the current detail image

/**
 * Opens a modal displaying the detail image of a design.
 * 
 * @param {string} detailImageUrl - The URL of the detail image to display in the modal.
 */
const openModal = (detailImageUrl) => {
  currentDetailImageUrl.value = detailImageUrl; // Set the current image URL to be shown in the modal
  isModalVisible.value = true; // Show the modal
};

/**
 * Lifecycle hook that runs after the component is mounted.
 * 
 * This hook initializes the web designs store and fetches the designs data.
 * The data is then stored in the `designs` ref.
 */
onMounted(async () => {
  await webDesignsStore.init(); // Initialize the web designs store
  designs.value = webDesignsStore.getDesigns; // Update the local reactive state with the fetched designs
});
</script>
