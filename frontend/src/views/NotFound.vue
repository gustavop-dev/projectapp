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
            <div>
              <h1>
                <span class="text-7xl font-light text-white lg:text-8xl xl:text-esmerald">404</span><br />
                <span class="text-xl font-medium text-white xl:text-esmerald mt-3 block">{{ messages.page_not_found }}</span>
              </h1>
              <p class="mt-4 text-white xl:text-esmerald text-md max-w-lg">{{ messages.subtitle }}</p>
              <div class="mt-8">
                <router-link to="/" class="px-8 py-3 font-regular text-md bg-lemon text-esmerald rounded-full hover:bg-esmerald hover:text-esmerald-light transition-all duration-300 ease-in-out">
                  {{ messages.back_to_home }}
                </router-link>
              </div>
            </div>
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
                <source src="@/assets/videos/webDesigns/Dunes.mp4" type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            </div>
          </div>
        </div>
      </div>
    </section>
    <div class="mt-32 lg:mt-52">
      <Footer></Footer>
    </div>
  </div>
</template>

<script setup>
import Navbar from "@/components/layouts/Navbar.vue";
import Footer from "@/components/layouts/Footer.vue";
import { ref } from "vue";
import { useMessages } from "@/composables/useMessages";
import { useFreeResources } from '@/composables/useFreeResources';

const { messages } = useMessages();

// Referencia para el video de fondo
const backgroundVideo = ref(null);

// Liberar recursos cuando el componente se desmonta
useFreeResources({
  videos: [backgroundVideo]
});
</script> 