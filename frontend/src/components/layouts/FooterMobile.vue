<template>
  <footer class="relative p-3 h-svh">
      <div class="relative w-full h-full overflow-hidden">
          <video ref="mainVideo" class="absolute top-0 left-0 w-full h-full object-cover rounded-xl" autoplay muted loop preload="metadata" aria-label="Mobile footer background video">
              <source src="@/assets/videos/presentationMobile.mp4" type="video/mp4">
              <p class="sr-only">Video showcasing our web design and development services</p>
          </video>
      </div>

      <div class="absolute bottom-0 right-0 w-full h-1/2 p-3">
        <div class="h-full grid auto-rows-min rounded-b-xl bg-window-black bg-opacity-40 backdrop-blur-md">
            <nav aria-label="Mobile website sections" class="md:w-max grid grid-cols-2 auto-rows-min text-white mt-4">
              <RouterLink
                :to="{ name:  item.href }" 
                v-for="item in solutions" 
                :key="item.name" 
                :href="item.href" 
                class="flex p-1 ps-4 font-regular text-white text-md relative group"
                aria-label="Navigate to {{ item.name }}"
              >
                {{ item.name }}
                <div class="absolute ms-4 left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300 group-hover:w-full"></div>
                <div class="relative ps-2 transform opacity-0 group-hover:opacity-100 transition-opacity duration-300 font-regular">
                  ➜
                </div>
                <span class="sr-only">Visit our {{ item.name }} page</span>
              </RouterLink>
            </nav>
            <div class="w-60">
              <div class="mt-4 p-1 ps-4">
                <a 
                  href="https://www.instagram.com/projectapp.co/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  class="block text-md cursor-pointer social-link text-white font-regular"
                  aria-label="Visit our Instagram profile"
                  >
                  {{ globalMessages.instagram }} 
                  <ArrowUpRightIcon class="w-5 inline arrow-icon"></ArrowUpRightIcon>
                  <span class="sr-only">Opens in a new window</span>
                </a>
                <a 
                  href="https://www.facebook.com/projectapp.co" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  class="block text-md cursor-pointer social-link text-white font-regular"
                  aria-label="Visit our Facebook page"
                  >
                  {{ globalMessages.facebook }} 
                  <ArrowUpRightIcon class="w-5 inline arrow-icon"></ArrowUpRightIcon>
                  <span class="sr-only">Opens in a new window</span>
                </a>
                <a 
                  href="https://wa.me/message/XX77FJEUEM26H1?src=qr" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  class="block text-md cursor-pointer social-link text-white font-regular"
                  aria-label="Contact us on WhatsApp">
                  {{ globalMessages.whatsapp }} 
                  <ArrowUpRightIcon class="w-5 inline arrow-icon"></ArrowUpRightIcon>
                  <span class="sr-only">Opens in a new window</span>
                </a>
                <a 
                  @click.prevent="showModalEmail = true"
                  href="#"
                  class="flex cursor-pointer font-regular text-white text-md relative group"
                  aria-label="Email our web design team"
                  >
                  {{ globalMessages.email_address }}
                  <div class="absolute left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300 group-hover:w-full"></div>
                  <span class="sr-only">Open contact form to email our website developers</span>
                </a>
              </div>
            </div>
            <div class="absolute bottom-0">
              <h3 class="ms-4 mb-4 text-lg font-regular text-white opacity-40">
              {{ globalMessages.based_in }}
              </h3>
            </div>
        </div>
    </div>
  </footer>
  <Email :visible="showModalEmail" @update:visible="showModalEmail = $event"></Email>
</template>

<script setup>
import Email from '@/components/layouts/Email.vue';
import { ref, onMounted, onUnmounted } from 'vue';
import ArrowUpRightIcon from '@heroicons/vue/20/solid/ArrowUpRightIcon';
import { useGlobalMessages } from '@/composables/useMessages';
import { useFreeResources } from '@/composables/useFreeResources';

const { globalMessages } = useGlobalMessages('footer');

// Estado reactivo
const showModalEmail = ref(false);
const solutions = ref([
  { name: globalMessages.solutions.home, href: 'home' },
  { name: globalMessages.solutions.about, href: 'aboutUs' },
  { name: globalMessages.solutions.web_designs, href: 'webDesigns' },
  { name: globalMessages.solutions.web_developments, href: 'portfolioWorks' },
  { name: globalMessages.solutions.custom_software, href: 'customSoftware' },
  { name: globalMessages.solutions.animations_3d, href: '3dAnimations' },
  { name: globalMessages.solutions.prices, href: 'eCommercePrices' },
  { name: globalMessages.solutions.hosting, href: 'hosting' },
]);

const mainVideo = ref(null);

// Limpiar recursos cuando el componente se desmonta
useFreeResources({
  videos: [mainVideo],
});
</script>

<style scoped>
.group:hover .group-hover\:w-full {
  width: 100%;
}
.group:hover .group-hover\:opacity-100 {
  opacity: 1;
}
</style>
