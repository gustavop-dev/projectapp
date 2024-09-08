<template>
  <!--Navbar Desktop-->
  <div class="hidden lg:block relative w-screen">
    <div class="absolute ps-8 pt-6 z-10">
      <h1 class="text-xl font-bold text-esmerald">
        Project<br>App.
      </h1>
    </div>
    <div class="flex absolute z-10 pt-6 top-0 right-0 lg:pe-8">
      <Popover class="relative">

        <PopoverButton 
          class="inline-flex items-center gap-x-1 text-md bg-window-black bg-opacity-40 backdrop-blur-md text-white font-regular py-2 px-8 rounded-xl mx-2 transition duration-250 ease-out hover:bg-esmerald">
          <span>
            {{ globalMessages.menu_button }}
          </span>
        </PopoverButton>

        <transition 
          enter-active-class="transition ease-out duration-200" 
          enter-from-class="opacity-0 translate-y-1" 
          enter-to-class="opacity-100 translate-y-0" 
          leave-active-class="transition ease-in duration-150" 
          leave-from-class="opacity-100 translate-y-0" 
          leave-to-class="opacity-0 translate-y-1"
          >
          <PopoverPanel class="absolute right-0 z-10 mt-5 flex max-w-min px-2">
            <div class="w-max grid grid-cols-2 rounded-xl bg-window-black bg-opacity-40 text-white backdrop-blur-md">
              <RouterLink
                :to="{ name:  item.href }" 
                v-for="(item, index) in solutions" 
                :key="index" 
                class="flex p-2 ps-4 font-regular text-white text-xl relative group"
                @mouseenter="hoverMenu($event, true)" 
                @mouseleave="hoverMenu($event, false)"
              >
                {{ item.name }}
                <div class="absolute ms-4 left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300 group-hover:w-full underline"></div>
                <div class="relative ps-2 transform opacity-0 group-hover:opacity-100 transition-opacity duration-300 font-regular arrow">
                  ➜
                </div>
              </RouterLink>
              <SocialLinks></SocialLinks>
              <ButtonWhitArrow @click="showModalEmail = true"></ButtonWhitArrow>
            </div>
          </PopoverPanel>
        </transition>
      </Popover>
      <button 
        @click="showModalEmail = true" 
        class="inline-flex items-center gap-x-1 text-md bg-window-black bg-opacity-40 backdrop-blur-md text-white font-regular py-2 px-8 rounded-xl mx-2 transition duration-250 ease-out hover:bg-esmerald">
        {{ globalMessages.get_in_touch }}
      </button>
    </div>
  </div>

  <!--Navbar Mobile-->
  <div class="block lg:hidden relative h-8 w-screen">

    <div class="absolute ps-8 pt-6 z-10">
      <h1 class="text-xl font-bold text-esmerald">
        Project<br>App.
      </h1>
    </div>

    <div class="flex absolute z-10 pt-6 pe-6 top-0 right-0">
      <span class="bg-window-black bg-opacity-40 backdrop-blur-md rounded-xl p-2">
        <Bars3Icon @click="openMenu()" class="text-white w-8 h-8"></Bars3Icon>
      </span>
    </div>
  </div>

  <div class="fixed inset-0 flex justify-end z-50" v-show="showMenu">
    <div 
      ref="background" 
      @click="closeMenu()" 
      class="absolute inset-0 bg-gray-500 bg-opacity-40 backdrop-blur-md"
      >
    </div>
    <div ref="menuBox" class="relative bg-lemon h-screen w-screen shadow-lg flex flex-col z-60">
      <div class="flex justify-end py-3 pe-3">
        <XMarkIcon @click="closeMenu()" class="text-esmerald w-8 h-8"></XMarkIcon>
      </div>
      <RouterLink
        :to="{ name:  item.href }" 
        v-for="(item, index) in solutions" 
        :key="index" 
        class="flex p-2 ps-4 font-regular text-esmerald text-4xl relative group"
        >
        {{ item.name }}
      </RouterLink>
      <div class="absolute bottom-0 w-full">
        <SocialLinks></SocialLinks>
        <div class="border-transparent border-t-esmerald border-opacity-40 border"></div>
        <ButtonWhitArrow @click="showModalEmail = true"></ButtonWhitArrow>
      </div>
    </div>
  </div>

  <Email :visible="showModalEmail" @update:visible="showModalEmail = $event"></Email>
</template>

<script setup>
import Email from '@/components/layouts/Email.vue'; // Import the Email component
import { ref } from 'vue'; // Import ref for reactive state
import { gsap } from 'gsap'; // Import GSAP for animations
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/vue'; // Import Popover components from Headless UI
import { Bars3Icon, XMarkIcon } from '@heroicons/vue/24/outline'; // Import Heroicons for the menu and close icons
import SocialLinks from '@/components/utils/SocialLinks.vue'; // Import the SocialLinks component
import ButtonWhitArrow from '@/components/utils/ButtonWithArrow.vue'; // Import the ButtonWithArrow component
import { useGlobalMessages } from '@/composables/useMessages'; // Import the custom composable to get global messages

const { globalMessages } = useGlobalMessages('navbar'); // Get the global messages for the 'navbar' section

// Reactive references for various states
const background = ref(null); // Reference to the background element for animations
const menuBox = ref(null); // Reference to the menu box element for animations
const showModalEmail = ref(false); // Controls visibility of the email modal
const showMenu = ref(false); // Controls visibility of the menu

// Solutions array, populated with global messages for navbar links
const solutions = ref([
  { name: globalMessages.solutions.home, href: 'home' },
  { name: globalMessages.solutions.about, href: 'aboutUs' },
  { name: globalMessages.solutions.web_designs, href: 'webDesigns' },
  { name: globalMessages.solutions.web_developments, href: 'webDevelopments' },
  { name: globalMessages.solutions.custom_software, href: 'customSoftware' },
  { name: globalMessages.solutions.animations_3d, href: '3dAnimations' },
  { name: globalMessages.solutions.prices, href: 'eCommercePrices' },
  { name: globalMessages.solutions.hosting, href: 'hosting' },
]);

/**
 * Handles hover animations for menu items.
 * 
 * @param {Event} event - The hover event.
 * @param {Boolean} isHover - Whether the menu item is being hovered over.
 */
const hoverMenu = (event, isHover) => {
  const underline = event.target.querySelector('.underline'); // Find underline element
  const arrow = event.target.querySelector('.arrow'); // Find arrow element
  if (isHover) {
    gsap.to(underline, { width: '50%', duration: 0.05 }); // Expand underline on hover
    gsap.to(arrow, { opacity: 1, duration: 0.05 }); // Show arrow on hover
  } else {
    gsap.to(underline, { width: '0%', duration: 0.05 }); // Hide underline on hover out
    gsap.to(arrow, { opacity: 0, duration: 0.05 }); // Hide arrow on hover out
  }
};

/**
 * Opens the menu with GSAP animations.
 * 
 * Animates the background and menu box into view when the menu is opened.
 */
const openMenu = () => {
  showMenu.value = true; // Show the menu
  if (background.value && menuBox.value) {
    gsap.fromTo(
      background.value,
      { opacity: 0 },
      { opacity: 1, duration: 1, ease: "power2.inOut" } // Fade in the background
    );
  
    gsap.fromTo(
      menuBox.value,
      { x: window.innerWidth }, // Start the menu off-screen
      { x: 0, duration: 1, ease: "power2.inOut" } // Slide the menu into view
    );
  }
};

/**
 * Closes the menu with GSAP animations.
 * 
 * Animates the background and menu box out of view when the menu is closed.
 */
const closeMenu = () => {
  // Animate the menu box sliding out
  const menuAnimation = gsap.fromTo(
    menuBox.value,
    { x: 0 },
    { x: menuBox.value.offsetWidth, duration: 1, ease: "power2.inOut" }
  ).then();

  // Animate the background fading out
  const backgroundAnimation = gsap.fromTo(
    background.value,
    { opacity: 1 },
    { opacity: 0, duration: 1, ease: "power2.inOut" }
  ).then();

  // Wait for both animations to complete before hiding the menu
  Promise.all([menuAnimation, backgroundAnimation]).then(() => {
    showMenu.value = false; // Hide the menu
  });
};
</script>