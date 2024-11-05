<template>
  <div>
    <!-- Fixed navbar component at the top of the page -->
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar></Navbar>
    </div>

    <!-- Render InitialVideo component only on desktop screens -->
    <InitialVideo v-if="isDesktop" :play_text="messages.video.text"></InitialVideo>

    <!-- Render InitialVideoMobile component only on mobile screens -->
    <InitialVideoMobile v-else></InitialVideoMobile>
    
    <!-- First section of the home page with a title -->
    <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52">
      <h2 class="block font-light text-4xl text-esmerald lg:pe-60 lg:text-6xl">
        {{ messages.section_1.title }}
      </h2>
    </section>

    <!-- Grid section with responsive text layout -->
    <section class="grid grid-cols-3">
      <div class="col-span-1">
        <h1 class="hidden font-light text-sm ms-32 text-esmerald lg:inline">{{ messages.section_2.software_house }}</h1>
      </div>
      <div class="col-span-3 lg:col-span-2">
        <div class="grid grid-cols-3 gap-12 lg:grid-cols-2">
          <div class="col-span-1 lg:hidden"></div>
          <div class="col-span-2 lg:col-span-1">
            <h1 class="bg-esmerald-light px-6 py-2 inline-block rounded-3xl text-esmerald text-sm">{{ messages.section_2.our_motto }}</h1>
            <h2 class="mt-20">
              <span class="text-esmerald font-regular text-lg">{{ messages.section_2.text.first }}</span>
              <span class="text-green-light text-lg font-regular">{{ messages.section_2.text.second }}<br><br>{{ messages.section_2.text.third }}</span>
            </h2>
          </div>
          <div class="col-span-3 lg:pe-4 lg:col-span-1">
            <video autoplay muted loop playsinline>
              <source src="@/assets/videos/home/cubic.mp4" type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
        </div>
      </div>
    </section>

    <!-- Third section of the home page with image and text content -->
    <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52">
      <h2 class="block font-light text-5xl mb-24 text-esmerald lg:mb-40 lg:text-6xl lg:text-end">{{ messages.section_3.title }}</h2>
      <div class="grid lg:grid-cols-2">
        <div class="h-80 order-2 mt-24 lg:mt-0 lg:order-1 lg:h-auto">
          <img src="@/assets/images/home/cube_illusion.webp" alt="Section 3">
        </div>
        <div class="order-1 lg:order-2 lg:ps-32">
          <h3 class="text-end text-4xl font-light text-esmerald">{{ messages.section_3.web_development.title }}</h3>
          <p class="text-end text-lg font-regular mt-8 text-green-light">{{ messages.section_3.web_development.text }}</p>
          <h3 class="text-end text-4xl font-light text-esmerald mt-24 lg:mt-32">{{ messages.section_3.custom_development.title }}</h3>
          <p class="text-end text-lg font-regular mt-8 text-green-light">{{ messages.section_3.custom_development.text }}</p>
        </div>
      </div>
    </section>

    <!-- Contact section at the bottom of the page -->
    <section class="mt-16">
      <Contact></Contact>
    </section>

    <!-- Footer component at the very end of the page -->
    <section class="mt-16 relative">
      <Footer></Footer>
    </section>
  </div>
</template>

<script setup>
// Import components for the homepage layout
import Navbar from '@/components/layouts/Navbar.vue'; // Navbar component for navigation at the top
import InitialVideo from '@/components/home/InitialVideo.vue'; // Video component for desktop
import InitialVideoMobile from '@/components/home/InitialVideoMobile.vue'; // Video component for mobile
import Footer from '@/components/layouts/Footer.vue'; // Footer component for the end of the page
import Contact from '@/components/layouts/Contact.vue'; // Contact section component
import { useMessages } from '@/composables/useMessages'; // Custom composable to retrieve localized messages
import { ref, onMounted, onBeforeUnmount } from 'vue';

// Retrieve localized messages for the current view using a custom composable
const { messages } = useMessages();
const isDesktop = ref(window.innerWidth >= 1024);

// Function to handle screen resize events
function handleResize() {
  isDesktop.value = window.innerWidth >= 1024;
}

// Add event listener for window resize
onMounted(() => {
  window.addEventListener('resize', handleResize);
});

// Remove event listener when component is destroyed
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
});

</script>

