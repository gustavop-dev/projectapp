<template>
    <div>
        <div class="fixed top-0 left-0 w-full z-50">
            <Navbar></Navbar>
        </div>
        <section class="h-screen relative">
            <div class="absolute z-20 w-1/3 px-3 h-full flex items-center md:px-16">
                <h1 class="text-white font-light text-6xl md:text-8xl">{{ messages.hero_section.title }}</h1>
            </div>
            <Dune spline="/spline/Backgrounds/particles.splinecode"></Dune>
        </section>
        <section class="bg-black grid md:grid-cols-2 lg:pt-52">
            <div class="pb-32">
                <h2 class="px-3 max-w-7xl text-white text-6xl font-light">{{ messages.erp_section.title }}</h2>
                <p class="px-3 mt-20 text-white text-lg font-regular">{{ messages.erp_section.paragraph_1 }}</p>
                <p class="px-3 mt-8 text-white text-lg font-regular">{{ messages.erp_section.paragraph_2 }}</p>
            </div>
            <div class="flex items-center justify-center">
                <img class="h-full w-full object-cover rounded-xl" src="@/assets/images/lightningBulb.webp" alt="Light Bulb 3D">
            </div>
        </section>
        <section class="bg-black grid md:grid-cols-2 lg:pt-52">
            <div class="flex items-center justify-center order-2 md:order-1 h-80 md:h-auto">
                <Dune spline="/spline/Backgrounds/bubleBlue.splinecode"></Dune>
            </div>
            <div class="pb-32 order-1 md:order-2">
                <h2 class="px-3 max-w-7xl text-white text-6xl font-light">{{ messages.crm_section.title }}</h2>
                <p class="px-3 mt-20 text-white text-lg font-regular">{{ messages.crm_section.paragraph_1 }}</p>
                <p class="px-3 mt-8 text-white text-lg font-regular">{{ messages.crm_section.paragraph_2 }}</p>
            </div>
        </section>
        <section class="bg-black pt-32 grid md:grid-cols-2 lg:pt-52">
            <div class="pb-32">
                <h2 class="px-3 max-w-7xl text-white text-6xl font-light">{{ messages.tailored_solutions_section.title }}</h2>
                <p class="px-3 mt-20 text-white text-lg font-regular">{{ messages.tailored_solutions_section.paragraph_1 }}</p>
                <p class="px-3 mt-8 text-white text-lg font-regular">{{ messages.tailored_solutions_section.paragraph_2 }}</p>
            </div>
            <div class="flex items-center justify-center h-80 md:h-auto">
                <Dune spline="/spline/Backgrounds/bubles.splinecode"></Dune>
            </div>
        </section>
        <section class="p-3 bg-black">
            <div class="border-t-2 border-t-gray-250 grid lg:h-80 lg:grid-cols-2">
                <div class="ps-8 mt-16">
                    <h2 class="text-white text-4xl font-regular">{{ messages.contact_section.title }}</h2>
                </div>
                <div class="grid mt-16 lg:grid-cols-2">
                    <div class="relative border-s-2 border-s-gray-250 ps-4 py-8">
                        <h3 class="text-white text-4xl font-regular">{{ messages.contact_section.mail_title }}</h3>
                        <p class="mt-4 text-green-light text-lg font-regular">{{ messages.contact_section.mail_description }}</p>
                        <a @click="showModalEmail = true" ref="emailLink" @mouseover="animateLink" @mouseleave="resetLink" class="inline-block text-xl absolute bottom-0 text-white cursor-pointer">
                        hello@projectapp.co
                        <span ref="underline" class="absolute left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300"></span>
                        <span ref="arrow" class="absolute right-0 top-1/2 transform -translate-y-1/2 opacity-0 transition-opacity duration-300">➜</span>
                        </a>
                    </div>
                    <div class="relative border-s-2 border-s-gray-250 ps-4 py-8">
                        <h3 class="text-white text-4xl font-regular">{{ messages.contact_section.direct_contact_title }}</h3>
                        <p class="mt-4 text-green-light text-lg font-regular">{{ messages.contact_section.direct_contact_description }}</p>
                        <a href="https://wa.me/message/XX77FJEUEM26H1?src=qr" target="_blank" ref="chatLink" @mouseover="animateLinkChat" @mouseleave="resetLinkChat" class="inline-block text-xl absolute bottom-0 text-white cursor-pointer">
                        Chat
                        <span ref="underlineChat" class="absolute left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300"></span>
                        <span ref="arrowChat" class="absolute right-0 top-1/2 transform -translate-y-1/2 opacity-0 transition-opacity duration-300">➜</span>
                        </a>
                    </div>
                </div>
            </div>
        </section>
        <div class="pt-32 bg-black">
            <Footer></Footer>
        </div>
    </div>
    <Email :visible="showModalEmail" @update:visible="showModalEmail = $event"></Email>
</template>

<script setup>
import Navbar from '@/components/layouts/Navbar.vue'; // Import the Navbar component for the navigation bar
import Footer from '@/components/layouts/Footer.vue'; // Import the Footer component for the website's footer
import Dune from '@/components/spline/Backgrounds/Dune.vue'; // Import the Dune background component (possibly a 3D background)
import Email from '@/components/layouts/Email.vue'; // Import the Email component for email-related functionality
import { ref } from 'vue'; // Import ref for reactive state management
import { gsap } from 'gsap'; // Import GSAP (GreenSock Animation Platform) for animations
import { useMessages } from '@/composables/useMessages'; // Import the custom composable for localized messages

const { messages } = useMessages(); // Destructure the localized messages from the custom composable

// Reactive state to control the visibility of the email modal
const showModalEmail = ref(false);

// Refs for DOM elements to be animated
const emailLink = ref(null);
const chatLink = ref(null);
const underline = ref(null);
const arrow = ref(null);
const underlineChat = ref(null);
const arrowChat = ref(null);

// Animation functions using GSAP

/**
 * Animates the email link by expanding the underline and making the arrow visible.
 */
const animateLink = () => {
  gsap.to(underline.value, { width: '100%', duration: 0.05 });
  gsap.to(arrow.value, { opacity: 1, x: 30, duration: 0.05 });
};

/**
 * Resets the email link animation by collapsing the underline and hiding the arrow.
 */
const resetLink = () => {
  gsap.to(underline.value, { width: '0%', duration: 0.05 });
  gsap.to(arrow.value, { opacity: 0, x: 20, duration: 0.05 });
};

/**
 * Animates the chat link by expanding the underline and making the arrow visible.
 */
const animateLinkChat = () => {
  gsap.to(underlineChat.value, { width: '100%', duration: 0.05 });
  gsap.to(arrowChat.value, { opacity: 1, x: 30, duration: 0.05 });
};

/**
 * Resets the chat link animation by collapsing the underline and hiding the arrow.
 */
const resetLinkChat = () => {
  gsap.to(underlineChat.value, { width: '0%', duration: 0.05 });
  gsap.to(arrowChat.value, { opacity: 0, x: 20, duration: 0.05 });
};

</script>
