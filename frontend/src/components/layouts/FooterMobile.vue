<template>
  <div class="relative p-3 h-svh">
      <div class="relative w-full h-full overflow-hidden">
          <video ref="mainVideo" class="absolute top-0 left-0 w-full h-full object-cover rounded-xl" autoplay muted loop>
              <source src="@/assets/videos/presentationMobile.mp4" type="video/mp4">
              Your browser does not support the video tag.
          </video>
      </div>

      <div class="absolute bottom-0 right-0 w-full h-1/2 p-3">
        <div class="h-full grid auto-rows-min rounded-b-xl bg-window-black bg-opacity-40 backdrop-blur-md">
            <div class="md:w-max grid grid-cols-2 auto-rows-min text-white mt-4">
              <RouterLink
                :to="{ name:  item.href }" 
                v-for="item in solutions" 
                :key="item.name" 
                :href="item.href" 
                class="flex p-1 ps-4 font-regular text-white text-md relative group"
                @mouseover="hoverMenu($event, true)" 
                @mouseleave="hoverMenu($event, false)"
              >
                {{ item.name }}
                <div class="absolute ms-4 left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300 group-hover:w-full"></div>
                <div class="relative ps-2 transform opacity-0 group-hover:opacity-100 transition-opacity duration-300 font-regular">
                  ➜
                </div>
              </RouterLink>
            </div>
            <div class="w-60">
              <div class="mt-4 p-1 ps-4">
                <a 
                  href="https://www.instagram.com/projectapp.co/" 
                  target="_blank" 
                  class="block text-md cursor-pointer social-link text-white font-regular"
                  >
                  {{ globalMessages.instagram }} 
                  <ArrowUpRightIcon class="w-5 inline arrow-icon"></ArrowUpRightIcon>
                </a>
                <a 
                  href="https://www.facebook.com/projectapp.co" 
                  target="_blank" 
                  class="block text-md cursor-pointer social-link text-white font-regular"
                  >
                  {{ globalMessages.facebook }} 
                  <ArrowUpRightIcon class="w-5 inline arrow-icon"></ArrowUpRightIcon>
                </a>
                <a 
                  href="https://wa.me/message/XX77FJEUEM26H1?src=qr" 
                  target="_blank" 
                  class="block text-md cursor-pointer social-link text-white font-regular">
                  {{ globalMessages.whatsapp }} 
                  <ArrowUpRightIcon class="w-5 inline arrow-icon"></ArrowUpRightIcon>
                </a>
                <a 
                  @click="showModalEmail = true"
                  class="flex cursor-pointer font-regular text-white text-md relative group"
                  @mouseover="hoverMenu($event, true)" 
                  @mouseleave="hoverMenu($event, false)"
                  >
                  {{ globalMessages.email_address }}
                  <div class="absolute left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300 group-hover:w-full"></div>
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
  </div>
  <Email :visible="showModalEmail" @update:visible="showModalEmail = $event"></Email>
</template>

<script setup>
import Email from '@/components/layouts/Email.vue'; // Import the Email component
import { ref } from 'vue'; // Import Vue utilities for state management
import ArrowUpRightIcon from '@heroicons/vue/20/solid/ArrowUpRightIcon'; // Import Heroicons for the arrow icon
import { useGlobalMessages } from '@/composables/useMessages'; // Import the custom composable for global messages
import { useFreeResources } from '@/composables/useFreeResources'; // Import the composable for freeing resources

const { globalMessages } = useGlobalMessages('footer'); // Get the global messages for the 'footer' section

// Reactive state
const showModalEmail = ref(false); // Controls the visibility of the email modal
const solutions = ref([ // Array of solution links populated from global messages
{ name: globalMessages.solutions.home, href: 'home' },
{ name: globalMessages.solutions.about, href: 'aboutUs' },
{ name: globalMessages.solutions.web_designs, href: 'webDesigns' },
{ name: globalMessages.solutions.web_developments, href: 'webDevelopments' },
{ name: globalMessages.solutions.custom_software, href: 'customSoftware' },
{ name: globalMessages.solutions.animations_3d, href: '3dAnimations' },
{ name: globalMessages.solutions.prices, href: 'eCommercePrices' },
{ name: globalMessages.solutions.hosting, href: 'hosting' },
]);

const mainVideo = ref(null); // Reference for the main video

// Use free resources to clean up video resources on unmount
useFreeResources({
videos: [mainVideo],
});
</script>
