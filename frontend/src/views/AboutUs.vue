<template>
    <div>
        <div class="fixed top-0 left-0 w-screen z-50">
            <Navbar></Navbar>
        </div>
        <section class="bg-lemon px-3 py-32 lg:pt-52 lg:pb-60">
            <div class="grid lg:grid-cols-2">
                <div class="mb-24 lg:ps-6 lg:mb-0">
                    <h1 class="bg-window-black bg-opacity-40 backdrop-blur-md px-6 py-2 inline-block rounded-3xl text-esmerald text-sm">About</h1>
                </div>
                <div>
                    <h1 class="inline-block text-6xl font-regular text-esmerald">Full-time<br>Perfection<br><span class="border-4 border-transparent border-b-esmerald">Seekers</span></h1>
                    <h2 class="mt-6 font-regular text-esmerald text-md">In our work.<br>In how to be good people too.</h2>
                </div>
            </div>
        </section>
        <section class="bg-lemon h-auto p-3">
            <div class="w-full h-80 rounded-xl overflow-hidden lg:h-full">
                <Dune spline="/spline/Backgrounds/planet.splinecode"></Dune>
            </div>
        </section>
        <section class="grid justify-items-end max-w-7xl mx-auto px-3 py-32 lg:py-52 lg:justify-items-start">
            <h1 class="text-4xl text-esmerald font-light lg:text-6xl">The digital landscape has transformed everything. Now, businesses must stand out every single day with a robust online presence and continuous innovation.</h1>
            <div class="grid flex-initial w-3/5 mt-20 lg:grid-cols-2 lg:mt-32 lg:w-full">
                <h2 class="inline-block font-light text-sm text-esmerald">[01] — About</h2>
                <div>
                    <p class="lg:w-1/2">
                        <span class="text-esmerald font-regular text-lg">
                            In fact, every company could benefit from an expert web development team today.
                        </span>
                        <span class="text-green-light text-lg font-regular">
                            But managing an in-house team can be overwhelming, right? Plus, many of the best talents are thriving as freelancers.
                            <br>
                            <br>
                            At our software house, we specialize in web development, offering top-tier developers to elevate your online presence without the headaches of in-house management. Let us handle the complexity while you focus on your core business.
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
                <h2 class="inline-block font-regular text-esmerald text-4xl border-2 border-transparent border-b-esmerald">We got your back.</h2>
                <h3 class="w-1/2 ms-32 inline-block font-regular text-lg"><span class="text-esmerald">For every mission, we gather independent talents </span><span class="text-green-light">into a powerful team. A team able to defy conformity and get you that edge it takes to perform. They are programers, copywriters, designers, directors, 3D artists, and they can see your brand in ways you haven’t dreamt of yet.</span></h3>
            </div>
        </section>
        <section class="h-screen p-3 relative">
            <div class="w-full h-full rounded-xl overflow-hidden">
                <img src="@/assets/images/visual_intro.webp" class="h-full w-full object-cover">
                <div class="absolute inset-0 flex items-center justify-center px-3">
                    <div class="text-center text-white">
                    <h2 class="text-4xl font-bold mb-2 md:text-6xl">Our super creatives are all different.</h2>
                    <h2 class="text-4xl font-bold md:text-6xl">except for one same belief - <br><span class="border-b-2 border-white">execution is everything.</span></h2>
                    </div>
                </div>
            </div>
        </section>
        <section class="pt-32 lg:py-52">
            <h2 class="text-7xl text-esmerald font-light text-center lg:text-9xl">LET’S GET YOU <br> WHERE YOU NEED<br>TO BE</h2>
        </section>
        <Contact></Contact>
        <div class="mt-32">
            <Footer></Footer>
        </div>
    </div>
</template>
<script setup>
import Navbar from '@/components/layouts/Navbar.vue';
import Dune from '@/components/spline/Backgrounds/Dune.vue';
import Footer from '@/components/layouts/Footer.vue';
import Contact from '@/components/layouts/Contact.vue'
import { onMounted, ref } from 'vue';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const leftImage = ref(null);
const imageContainer = ref(null);
const mobileImage = ref(null);

const initScrollTrigger = () => {
  gsap.to(leftImage.value, {
    y: () => imageContainer.value.offsetHeight - leftImage.value.offsetHeight,
    ease: "none",
    scrollTrigger: {
      trigger: imageContainer.value,
      start: "top bottom",
      end: "bottom center",
      scrub: true,
      markers: false
    }
  });
};

onMounted(() => {
  if (mobileImage.value.complete) {
    initScrollTrigger();
  }
});
</script>