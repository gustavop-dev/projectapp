<template>
    <div>
        <div class="fixed top-0 left-0 w-screen z-50">
            <Navbar></Navbar>
        </div>
        <section class="bg-lemon px-3 py-32 lg:pt-52 lg:pb-60">
            <div class="grid lg:grid-cols-2">
                <div class="mb-24 lg:ps-6 lg:mb-0">
                    <h1 class="bg-window-black bg-opacity-40 backdrop-blur-md px-6 py-2 inline-block rounded-3xl text-esmerald text-sm">
                        {{ messages.about.label }}
                    </h1>
                </div>
                <div>
                    <h1 class="inline-block text-6xl font-regular text-esmerald">
                        {{ messages.about.main_title_1 }}<br>
                        {{ messages.about.main_title_2 }}<br>
                        <span class="border-4 border-transparent border-b-esmerald">
                            {{ messages.about.main_title_3 }}
                        </span>
                    </h1>
                    <h2 class="mt-6 font-regular text-esmerald text-md">
                        {{ messages.about.sub_title_1 }}<br>
                        {{ messages.about.sub_title_2 }}
                    </h2>
                </div>
            </div>
        </section>
        <section class="bg-lemon h-auto p-3">
            <div class="w-full h-80 rounded-xl overflow-hidden lg:h-full">
                <Dune spline="/spline/Backgrounds/planet.splinecode"></Dune>
            </div>
        </section>
        <section class="grid justify-items-end max-w-7xl mx-auto px-3 py-32 lg:py-52 lg:justify-items-start">
            <h1 class="text-4xl text-esmerald font-light lg:text-6xl">
                {{ messages.digital_landscape.title }}
            </h1>
            <div class="grid flex-initial w-3/5 mt-20 lg:grid-cols-2 lg:mt-32 lg:w-full">
                <h2 class="inline-block font-light text-sm text-esmerald">
                    {{ messages.digital_landscape.section_label }}
                </h2>
                <div>
                    <p class="lg:w-1/2">
                        <span class="text-esmerald font-regular text-lg">
                            {{ messages.digital_landscape.text_1 }}
                        </span>
                        <span class="text-green-light text-lg font-regular">
                            {{ messages.digital_landscape.text_2 }}
                        </span>
                        <br>
                        <br>
                        <span class="text-green-light text-lg font-regular">
                            {{ messages.digital_landscape.text_3 }}
                        </span>
                    </p>
                </div>
            </div>
        </section>
        <section>
            <div class="grid lg:grid-cols-2 p-3">
                <div ref="imageContainer" class="overflow-hidden">
                    <img ref="leftImage" class="w-full rounded-xl" src="@/assets/images/left.webp" alt="A man in a computer" @load="initScrollTrigger">
                </div>
                <div>
                    <img ref="mobileImage" class="w-full rounded-xl" src="@/assets/images/mobile.webp" alt="A mobile in the hand of a man">
                </div>
            </div>
        </section>
        <section class="max-w-7xl mx-auto px-3 py-32 lg:py-52">
            <div class="inline-block mx-auto space-y-20">
                <h2 class="inline-block font-regular text-esmerald text-4xl border-2 border-transparent border-b-esmerald">
                    {{ messages.team_support.title }}
                </h2>
                <h3 class="w-1/2 ms-32 inline-block font-regular text-lg">
                    <span class="text-esmerald">
                        {{ messages.team_support.text_1 }}
                    </span>
                    <span class="text-green-light">
                        {{ messages.team_support.text_2 }}
                    </span>
                </h3>
            </div>
        </section>

        <section class="h-screen p-3 relative">
            <div class="w-full h-full rounded-xl overflow-hidden">
                <img src="@/assets/images/visual_intro.webp" class="h-full w-full object-cover">
                <div class="absolute inset-0 flex items-center justify-center px-3">
                    <div class="text-center text-white">
                        <h2 class="text-4xl font-bold mb-2 md:text-6xl">
                            {{ messages.creatives.title_1 }}
                        </h2>
                        <h2 class="text-4xl font-bold md:text-6xl">
                            {{ messages.creatives.title_2_part_1 }} 
                            <br>
                            <span class="border-b-2 border-white">
                                {{ messages.creatives.title_2_part_2 }}
                            </span>
                        </h2>
                    </div>
                </div>
            </div>
        </section>

        <section class="pt-32 lg:py-52">
            <h2 class="text-7xl text-esmerald font-light text-center lg:text-9xl">
                {{ messages.motivation.title_1 }} <br>
                {{ messages.motivation.title_2 }}<br>
                {{ messages.motivation.title_3 }}
            </h2>
        </section>

        <Contact></Contact>

        <div class="mt-32">
            <Footer></Footer>
        </div>
    </div>
</template>

<script setup>
import Navbar from '@/components/layouts/Navbar.vue'; // Import the Navbar component for the navigation bar
import Dune from '@/components/spline/Backgrounds/Dune.vue'; // Import the Dune component, likely a 3D background
import Footer from '@/components/layouts/Footer.vue'; // Import the Footer component for the website's footer
import Contact from '@/components/layouts/Contact.vue'; // Import the Contact component for the contact section
import { onMounted, ref } from 'vue'; // Import Vue's lifecycle hook and ref for reactivity
import { gsap } from 'gsap'; // Import GSAP (GreenSock Animation Platform) for animations
import { ScrollTrigger } from 'gsap/ScrollTrigger'; // Import the GSAP ScrollTrigger plugin
import { useMessages } from '@/composables/useMessages'; // Import the custom composable to get localized messages

const { messages } = useMessages(); // Destructure the localized messages from the custom composable

gsap.registerPlugin(ScrollTrigger); // Register ScrollTrigger plugin with GSAP

// Refs for DOM elements used in the scroll-triggered animations
const leftImage = ref(null);
const imageContainer = ref(null);
const mobileImage = ref(null);

/**
 * Initializes the ScrollTrigger animation on the leftImage element.
 * 
 * This function creates a GSAP scroll animation where the `leftImage` moves vertically
 * as the user scrolls through the `imageContainer`.
 */
const initScrollTrigger = () => {
  gsap.to(leftImage.value, {
    y: () => imageContainer.value.offsetHeight - leftImage.value.offsetHeight, // Set the animation distance
    ease: "none", // No easing for a smooth scroll effect
    scrollTrigger: {
      trigger: imageContainer.value, // The element that triggers the scroll animation
      start: "top bottom", // Animation starts when the top of the imageContainer hits the bottom of the viewport
      end: "bottom center", // Animation ends when the bottom of the imageContainer reaches the center of the viewport
      scrub: true, // Enables scrubbing (animation is tied to the scrollbar position)
      markers: false // Disable visible markers for debugging the scroll animation
    }
  });
};

/**
 * Lifecycle hook: Executes after the component is mounted.
 * 
 * This hook checks if the `mobileImage` is fully loaded. If so, it initializes the ScrollTrigger animation.
 */
onMounted(() => {
  if (mobileImage.value.complete) { // Ensure the image is fully loaded before initializing animations
    initScrollTrigger();
  }
});
</script>
