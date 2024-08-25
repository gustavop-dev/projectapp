<template>
  <div>
    <div>
      <div class="fixed top-0 left-0 w-full z-50">
        <Navbar></Navbar>
      </div>
      <InitialVideo :play_text="messages.video.text"></InitialVideo>
      <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52">
        <h2 class="block font-light text-4xl text-esmerald lg:pe-60 lg:text-6xl">
          {{ messages.section_1.title }}
        </h2>
      </section>
      <section class="grid grid-cols-3">
        <div class="col-span-1">
          <h1 class="hidden font-light text-sm ms-32 text-esmerald lg:inline">{{ messages.section_2.software_house }}</h1>
        </div>
        <div class="col-span-3 lg:col-span-2">
          <div class="grid grid-cols-3 gap-12 lg:grid-cols-2">
            <div class="col-span-1 lg:hidden"></div>
            <div class="col-span-2 lg:col-span-1">
              <h1 class="bg-esmerald-light px-6 py-2 inline-block rounded-3xl text-esmerald text-sm">{{ messages.section_2.our_motto }}</h1>
              <h2 class="mt-20"><span class="text-esmerald font-regular text-lg">{{ messages.section_2.text.first }}</span><span class="text-green-light text-lg font-regular">{{ messages.section_2.text.second }}<br><br> {{ messages.section_2.text.third }}</span></h2>
            </div>
            <div class="col-span-3 lg:pe-4 lg:col-span-1">
              <Dune spline="/spline/cube/scene.splinecode"></Dune>
            </div>
          </div>
        </div>
      </section>
      <section class="mt-24 mb-40 px-3 lg:px-32 lg:mt-52">
        <h2 class="block font-light text-5xl mb-24 text-esmerald lg:mb-40 lg:text-6xl lg:text-end">{{ messages.section_3.title }}</h2>
        <div class="grid lg:grid-cols-2">
          <div class="h-80 order-2 mt-24 lg:mt-0 lg:order-1 lg:h-auto">
            <Dune spline="/spline/gradientColor/scene.splinecode"></Dune>
          </div>
          <div class="order-1 lg:order-2 lg:ps-32">
            <h3 class="text-end text-4xl font-light text-esmerald">{{ messages.section_3.web_development.title }}</h3>
            <p class="text-end text-lg font-regular mt-8 text-green-light">{{ messages.section_3.web_development.text }}</p>
            <h3 class="text-end text-4xl font-light text-esmerald mt-24 lg:mt-32">{{ messages.section_3.custom_development.title }}</h3>
            <p class="text-end text-lg font-regular mt-8 text-green-light">{{ messages.section_3.custom_development.text }}</p>
          </div>
        </div>
      </section>
      <section class="mt-16">
        <Contact></Contact>
      </section>
      <section class="mt-16 relative">
        <Footer></Footer>
      </section>
    </div>
  </div>
</template>

<script setup>
import Navbar from '@/components/layouts/Navbar.vue'; // Import the Navbar component for the navigation bar
import InitialVideo from '@/components/home/InitialVideo.vue'; // Import the InitialVideo component, likely the main video of the homepage
import Footer from '@/components/layouts/Footer.vue'; // Import the Footer component for the website's footer
import Contact from '@/components/layouts/Contact.vue'; // Import the Contact component for the contact section
import { useMessages } from '@/composables/useMessages'; // Import the custom composable to get localized messages
import { defineAsyncComponent } from 'vue'; // Import the function to define asynchronous components

// Get the localized messages for the current view using the custom useMessages composable
const { messages } = useMessages();

// Dynamically import the Dune component, which is loaded only when needed (async loading)
const Dune = defineAsyncComponent(() =>
  import('@/components/spline/Backgrounds/Dune.vue')
);
</script>
