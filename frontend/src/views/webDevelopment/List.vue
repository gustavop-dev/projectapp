<template>
    <div>
        <div class="fixed top-0 left-0 w-full z-50">
            <Navbar></Navbar>
        </div>
        <section>
            <div class="p-3 h-screen">
                <div class="w-full h-full grid rounded-xl overflow-hidden lg:grid-cols-2">
                    <div class="flex items-center bg-lemon px-16 py-24 order-2">
                        <h1>
                            <span class="text-4xl font-light text-esmerald lg:text-6xl">{{ messages.main_title }}</span><br>
                            <span class="text-md font-medium text-esmerald">{{ messages.main_subtitle }}</span>
                        </h1>
                    </div>
                    <div class="order-1">
                        <Dune spline="/spline/Backgrounds/dune.splinecode"></Dune>
                    </div>
                </div>
            </div>
        </section>
        <section class="mt-24 px-3 lg:mt-52">
            <div v-for="development in developments" :key="development.id" class="container mx-auto sm:px-6 lg:px-8">
                <h1 class="text-4xl font-light text-esmerald md:text-5xl lg:text-6xl">{{ development.title }}</h1>
                <h2 class="text-2xl font-light text-esmerald mt-20 md:text:text-3xl lg:text-4xl">{{ development.description }}</h2>
                <div v-for="section in development.sections" :key="section.id" class="mt-20 grid grid-cols-4 lg:mt-40">
                    <div class="col-span-4 lg:col-span-1">
                        <h2 class="font-light text-esmerald text-lg">{{ section.title }}</h2>
                    </div>
                    <div class="col-span-4 mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-3 lg:mt-0 lg:col-span-3">
                        <div v-for="component in section.components" :key="component.id" @click="goToDetail(development.id, section.id, component.id)" class="cursor-pointer">
                            <div class="border border-gray-200 rounded-lg">
                                <img :src="component.image_url" :alt="component.id">
                            </div>
                            <h3 class="mt-4 font-regular text-esmerald text-md">{{ component.title }}</h3>
                            <p class="mt-2 bg-esmerald-light px-6 py-2 inline-block rounded-3xl text-esmerald text-sm">{{ component.examples.length }} {{ messages.component_count_label }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        <div class="mt-52">
            <Footer></Footer>
        </div>
    </div>
</template>

<script setup>
import { useWebDevelopmentsStore } from '@/stores/web_UI_section_category'; // Import the store for handling web developments
import Navbar from '@/components/layouts/Navbar.vue'; // Import the Navbar component for the navigation bar
import Dune from '@/components/spline/Backgrounds/Dune.vue'; // Import the Dune component (possibly a 3D background)
import Footer from '@/components/layouts/Footer.vue'; // Import the Footer component for the website's footer
import { useRouter } from 'vue-router'; // Import Vue Router for navigation
import { ref, onMounted } from 'vue'; // Import Vue's ref for reactivity and onMounted for lifecycle hook
import { useMessages } from '@/composables/useMessages'; // Import the custom composable to get localized messages

const { messages } = useMessages(); // Destructure the localized messages from the custom composable

// Store to handle web developments data
const developmentsStore = useWebDevelopmentsStore();
const developments = ref([]); // Reactive state to store the list of developments
const router = useRouter(); // Get the Vue Router instance for navigation

/**
 * Navigates to the detail page of a specific development component.
 * 
 * @param {number} developmentId - The ID of the development.
 * @param {number} sectionId - The ID of the section.
 * @param {number} componentId - The ID of the component.
 */
const goToDetail = (developmentId, sectionId, componentId) => {
  router.push({
    name: 'webDevelopmentsDetail', // Name of the route for the development details page
    params: {
      development_id: developmentId, // Pass the development ID as a route parameter
      section_id: sectionId,         // Pass the section ID as a route parameter
      component_id: componentId      // Pass the component ID as a route parameter
    }
  });
};

/**
 * Lifecycle hook that runs after the component is mounted.
 * 
 * This hook initializes the web developments store and fetches the developments data.
 * The data is then stored in the `developments` ref.
 */
onMounted(async () => {
  await developmentsStore.init(); // Initialize the store and fetch data
  developments.value = developmentsStore.getDevelopments; // Update the local reactive state with the fetched developments
});
</script>
