<template>
    <div>
        <div class="fixed top-0 left-0 w-full z-50">
            <Navbar></Navbar>
        </div>
        <section class="bg-lemon pt-52 pb-60">
            <div class="grid grid-cols-2">
                <div class="ps-6">
                    <h1 class="bg-window-black bg-opacity-40 backdrop-blur-md px-6 py-2 inline-block rounded-3xl text-esmerald text-sm">About</h1>
                </div>
                <div>
                    <h1 class="inline-block text-6xl font-regular text-esmerald">Full-time<br>Perfection<br><span class="border-4 border-transparent border-b-esmerald">Seekers</span></h1>
                    <h2 class="mt-6 font-regular text-esmerald text-md">In our work.<br>In how to be good people too.</h2>
                </div>
            </div>
        </section>
        <section class="bg-lemon h-screen p-3">
            <div class="w-full h-full rounded-xl overflow-hidden">
                <Dune spline="/spline/Backgrounds/planet.splinecode"></Dune>
            </div>
        </section>
        <section class="p-52">
            <h1 class="text-6xl text-esmerald font-light">The digital landscape has transformed everything. Now, businesses must stand out every single day with a robust online presence and continuous innovation.</h1>
            <div class="grid grid-cols-2 mt-32">
                <h2 class="inline-block font-light text-sm text-esmerald">[01] — About</h2>
                <div>
                    <h2 class="w-1/2"><span class="text-esmerald font-regular text-lg">In fact, every company could benefit from an expert web development team today.</span><span class="text-green-light text-lg font-regular">But managing an in-house team can be overwhelming, right? Plus, many of the best talents are thriving as freelancers.<br><br>At our software house, we specialize in web development, offering top-tier developers to elevate your online presence without the headaches of in-house management. Let us handle the complexity while you focus on your core business.</span></h2>
                </div>
            </div>
        </section>
        <section>
            <div class="grid grid-cols-2 p-3">
                <div ref="imageContainer" class="overflow-hidden">
                    <img ref="leftImage" class="w-full rounded-xl" src="@/assets/images/left.webp" alt="A man in a computer" @load="initScrollTrigger">
                </div>
                <div>
                    <img ref="mobileImage" class="w-full rounded-xl" src="@/assets/images/mobile.webp" alt="A mobile in the hand of a man">
                </div>
            </div>
        </section>
        <section class="p-52">
            <div class="inline-block mx-auto">
                <h2 class="inline-block font-regular text-esmerald text-4xl border-2 border-transparent border-b-esmerald">We got your back.</h2>
                <h3 class="w-1/2 ms-32 inline-block font-regular text-lg"><span class="text-esmerald">For every mission, we gather independent talents </span><span class="text-green-light">into a powerful team. A team able to defy conformity and get you that edge it takes to perform. They are programers, copywriters, designers, directors, 3D artists, and they can see your brand in ways you haven’t dreamt of yet.</span></h3>
            </div>
        </section>
        <section class="h-screen p-3 relative">
            <div class="w-full h-full rounded-xl overflow-hidden">
                <img src="@/assets/images/visual_intro.webp">
                <div class="absolute inset-0 flex items-center justify-center">
                    <div class="text-center text-white">
                    <h2 class="text-6xl font-bold mb-2">Our super creatives are all different.</h2>
                    <h2 class="text-6xl font-bold">except for one same belief - <br><span class="border-b-2 border-white">execution is everything.</span></h2>
                    </div>
                </div>
            </div>
        </section>
        <section class="py-52">
            <h2 class="text-9xl text-esmerald font-light text-center">LET’S GET YOU <br> WHERE YOU NEED<br>TO BE</h2>
        </section>
        <Contact></Contact>
        <div class="mt-32">
            <Footer></Footer>
        </div>
    </div>
</template>
<script setup>
import Navbar from '@/components/Layouts/Navbar.vue';
import Dune from '@/components/spline/Backgrounds/Dune.vue';
import Footer from '@/components/Layouts/Footer.vue';
import Contact from '@/components/Layouts/Contact.vue'
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