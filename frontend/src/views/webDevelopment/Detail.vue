<template>
    <div>
        <div class="fixed top-0 left-0 w-full z-50">
            <Navbar></Navbar>
        </div>
        <section class="h-32 lg:h-52"></section>
        <section>
            <div class="px-4 sm:px-6 lg:px-8 xl:px-32">
                <div v-if="data">
                    <h2 class="text-lg font-regular text-esmerald">{{ data.development.title }} / {{ data.section.title }}</h2>
                    <h1 class="text-6xl font-light text-esmerald">{{ data.component.title }}</h1>
                    <div v-for="example in data.examples" class="mt-16 mb-16">
                        <h2 class="text-xl font-regular text-esmerald">{{ example.title }}</h2>
                        <div class="mt-8 flex justify-center">
                            <img :src="example.image">
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
import Navbar from '@/components/layouts/Navbar.vue'; // Import the Navbar component for the navigation bar
import Footer from '@/components/layouts/Footer.vue'; // Import the Footer component for the website's footer
import { ref, onMounted } from 'vue'; // Import ref for reactivity and onMounted for lifecycle hook
import { useRoute } from 'vue-router'; // Import useRoute to access route parameters
import { useWebDevelopmentsStore } from '@/stores/web_UI_section_category'; // Import the web developments store

const route = useRoute(); // Get the current route and its parameters
const developmentsStore = useWebDevelopmentsStore(); // Access the store to handle web developments

const data = ref(null); // Reactive reference to store the fetched data

/**
 * Lifecycle hook that runs after the component is mounted.
 * 
 * This hook initializes the web developments store, fetches the data based on the current route parameters,
 * and stores the result in the `data` ref.
 */
onMounted(async () => {
  await developmentsStore.init(); // Initialize the web developments store
  const { development_id, section_id, component_id } = route.params; // Destructure route parameters
  data.value = developmentsStore.getExamplesById(development_id, section_id, component_id); // Fetch the data based on the route params
});
</script>
