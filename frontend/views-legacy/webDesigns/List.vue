<template>
  <div>
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar></Navbar>
    </div>
    <section>
      <div class="h-svh p-3">
        <div
          class="relative w-full h-full grid rounded-xl overflow-hidden lg:grid-cols-2"
        >
          <div class="absolute z-10 bottom-0 flex items-center px-16 order-2 py-24 xl:bg-bone xl:top-0 xl:relative xl:z-0">
            <h1>
              <span class="text-4xl font-light text-white lg:text-6xl xl:text-esmerald">{{
                messages.header_title
              }}</span
              ><br />
              <span class="text-md font-medium text-white xl:text-esmerald">{{
                messages.header_subtitle
              }}</span>
            </h1>
          </div>
          <div class="order-1">
            <div class="relative w-full h-svh overflow-hidden">
              <video
                ref="backgroundVideo" 
                autoplay
                muted
                loop
                playsinline
                class="absolute inset-0 w-auto h-full object-cover"
              >
                <source src="~/assets/videos/webDesigns/Dunes.mp4" type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            </div>
          </div>
        </div>
      </div>
    </section>
    <section class="px-3">
      <div class="mt-32 max-w-7xl mx-auto sm:px-6 lg:mt-52 lg:px-8">
        <h1 class="text-6xl font-light text-esmerald">
          {{ messages.section_title }}
        </h1>
        <h2 class="text-4xl font-light text-esmerald mt-20">
          {{ messages.section_subtitle }}
        </h2>
        <!-- Categories for filter -->
        <div class="mt-24 font-regular flex flex-wrap justify-center items-center gap-3">
          <!-- Button for 'All' category -->
          <button
            @click="getFilteredDesigns('All')"
            :class="
              selectedCategory === 'All' ? 'bg-lemon' : 'bg-esmerald-light'
            "
            class="px-6 py-2 inline-block rounded-3xl text-esmerald text-sm"
          >
            {{ messages.all }}
          </button>

          <!-- Buttons for other categories -->
          <button
            v-for="(category, index) in categories"
            :key="index"
            @click="getFilteredDesigns(category)"
            :class="
              selectedCategory === category ? 'bg-lemon' : 'bg-esmerald-light'
            "
            class="px-6 py-2 inline-block rounded-3xl text-esmerald text-sm"
          >
            {{ category }}
          </button>
        </div>

        <!-- Content by web designs -->
        <div class="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4 lg:mt-24">
          <div
            v-for="design in designsFiltered.slice().reverse().slice(0, visibleCount)"
            :key="design.id"
            @click="openModal(design.detail_image)"
            class="cursor-pointer"
          >
            <div class="border border-gray-200 rounded-lg">
              <ImageLoader 
                :src="design.cover_image"
                :alt="design.title"
              />
            </div>
            <h3 class="mt-4 font-regular text-esmerald text-md">
              {{ design.title }}
            </h3>
          </div>
        </div>
        <!-- Button for load more content -->
        <div v-if="visibleCount < designsFiltered.length" class="text-center mt-8">
          <button @click="loadMore" class="px-6 py-2 font-regular text-md bg-lemon text-esmerlad rounded-full hover:bg-esmerald hover:text-esmerald-light">
            {{ messages.see_more }}
          </button>
        </div>
      </div>
    </section>
    <div class="mt-32 lg:mt-52">
      <Footer></Footer>
    </div>
    <Detail
      :visible="isModalVisible"
      :detailImageUrl="currentDetailImageUrl"
      @update:visible="isModalVisible = $event"
    />
  </div>
</template>

<script setup>
import Navbar from "~/components/layouts/Navbar.vue"; // Import the Navbar component for the navigation bar
import ImageLoader from "~/components/layouts/ImageLoader.vue"; // Import the ImageLoader component for the loading animation
import Footer from "~/components/layouts/Footer.vue"; // Import the Footer component for the website's footer
import Detail from "~/views-legacy/webDesigns/Detail.vue"; // Import the Detail view for web designs
import { useWebDesignsStore } from "~/stores/web_designs"; // Import the web designs store
import { onMounted, ref, watch } from "vue"; // Import Vue's lifecycle hook and ref for reactivity
import { useMessages } from "~/composables/useMessages"; // Import the custom composable to get localized messages
import { useFreeResources } from '~/composables/useFreeResources'; // Import for managing media resources

const { messages } = useMessages(); // Destructure the localized messages from the custom composable

// Store for managing web designs data
const webDesignsStore = useWebDesignsStore();
const designs = ref([]); // Reactive reference to store the list of designs
const designsFiltered = ref([]); // Reactive reference to store the list of designs when an category is selected
const categories = ref([]); // Reactive reference to store the list of designs's categories
const selectedCategory = ref("All"); // 'All' is selected by default
const visibleCount = ref(16); // Number of pictures for showing

const isModalVisible = ref(false); // State to control the visibility of the modal
const currentDetailImageUrl = ref(""); // State to store the URL of the current detail image
const backgroundVideo = ref(null); // Reference for background video

/**
 * Opens a modal displaying the detail image of a design.
 *
 * @param {string} detailImageUrl - The URL of the detail image to display in the modal.
 */
const openModal = (detailImageUrl) => {
  currentDetailImageUrl.value = detailImageUrl; // Set the current image URL to be shown in the modal
  isModalVisible.value = true; // Show the modal
};

// Watcher for active/disactive the scroll
watch(isModalVisible, (newVal) => {
  if (newVal) {
    document.body.style.overflow = 'hidden' // Desactiva el scroll
  } else {
    document.body.style.overflow = '' // Activa el scroll
  }
})

// Method to get filtered designs based on the selected category
const getFilteredDesigns = (category) => {
  selectedCategory.value = category;
  designsFiltered.value =  webDesignsStore.getFilteredByCategory(designs.value, selectedCategory.value);
};

/**
 * Lifecycle hook that runs after the component is mounted.
 *
 * This hook initializes the web designs store and fetches the designs data.
 * The data is then stored in the `designs` ref.
 */
onMounted(async () => {
  await webDesignsStore.init(); // Initialize the web designs store

  // Destructure the returned object to get designs and categories
  const { designs: fetchedDesigns, categories: fetchedCategories } =
    webDesignsStore.getFilteredDesignsAndCategories;

  // Assign the fetched values to the reactive variables
  designs.value = fetchedDesigns;
  designsFiltered.value = fetchedDesigns;
  categories.value = fetchedCategories;
});

// Use `useFreeResources` to manage cleanup for video resources
useFreeResources({
  videos: [backgroundVideo]
});

// Use loadMore for increment the number of images for showing
const loadMore = () => {
  visibleCount.value += 16;
};
</script>