<template>
  <div>
    <div class="absolute ps-8 pt-6 z-10">
      <h1 class="text-xl font-bold text-esmerald">
        Project<br>App.
      </h1>
    </div>
    <div class="flex absolute z-10 pe-8 pt-6 top-0 right-0">
      <Popover class="relative">
        <PopoverButton class="inline-flex items-center gap-x-1 text-md bg-window-black bg-opacity-40 backdrop-blur-md text-white font-regular py-2 px-8 rounded-xl mx-2 transition duration-250 ease-out hover:bg-esmerald">
          <span>Menu</span>
        </PopoverButton>

        <transition enter-active-class="transition ease-out duration-200" enter-from-class="opacity-0 translate-y-1" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition ease-in duration-150" leave-from-class="opacity-100 translate-y-0" leave-to-class="opacity-0 translate-y-1">
          <PopoverPanel class="absolute right-0 z-10 mt-5 flex max-w-min px-2">
            <div class="w-max grid grid-cols-2 rounded-xl bg-window-black bg-opacity-40 text-white backdrop-blur-md">
              <RouterLink
                :to="{ name:  item.href }" 
                v-for="item in solutions" 
                :key="item.name" 
                class="flex p-2 ps-4 font-regular text-white text-xl relative group"
                @mouseover="hoverMenu($event, true)" 
                @mouseleave="hoverMenu($event, false)"
              >
                {{ item.name }}
                <div class="absolute ms-4 left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300 group-hover:w-full "></div>
                <div class="relative ps-2 transform opacity-0 group-hover:opacity-100 transition-opacity duration-300 font-regular">
                  ➜
                </div>
              </RouterLink>
              <SocialLinks></SocialLinks>
              <ButtonWhitArrow @click="showModalEmail = true"></ButtonWhitArrow>
            </div>
          </PopoverPanel>
        </transition>
      </Popover>
      <button @click="showModalEmail = true" class="inline-flex items-center gap-x-1 text-md bg-window-black bg-opacity-40 backdrop-blur-md text-white font-regular py-2 px-8 rounded-xl mx-2 transition duration-250 ease-out hover:bg-esmerald">
        Get in touch
      </button>
    </div>
    <Email :visible="showModalEmail" @update:visible="showModalEmail = $event"></Email>
  </div>
</template>

<script setup>
import Email from '@/components/Layouts/Email.vue';
import { ref } from 'vue';
import { gsap } from 'gsap';
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/vue';
import SocialLinks from '@/components/Utils/SocialLinks.vue';
import ButtonWhitArrow from '@/components/Utils/ButtonWithArrow.vue'

const showModalEmail = ref(false);
const solutions = ref([
  { name: 'Home', href: 'home' },
  { name: 'About', href: 'aboutUs' },
  { name: 'Web Designs', href: 'webDesigns' },
  { name: 'Web Developments', href: 'webDevelopments' },
  { name: 'Custom Software', href: 'customSoftware' },
  { name: '3D Animations', href: '3dAnimations' },
  { name: 'Prices', href: 'eCommercePrices'},
  { name: 'Hosting', href: 'hosting' },
]);


const hoverMenu = (event, isHover) => {
  const underline = event.target.querySelector('.underline');
  const arrow = event.target.querySelector('.arrow');
  if (isHover) {
    gsap.to(underline, { width: '100%', duration: 0.3 });
    gsap.to(arrow, { opacity: 1, duration: 0.3 });
  } else {
    gsap.to(underline, { width: '0%', duration: 0.3 });
    gsap.to(arrow, { opacity: 0, duration: 0.3 });
  }
};
</script>

<style>
.group:hover .group-hover\:w-full {
  width: 50%;
}
.group:hover .group-hover\:opacity-100 {
  opacity: 1;
}
</style>
