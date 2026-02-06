<template>
  <!--Navbar Desktop-->
  <nav class="hidden lg:block relative w-screen" aria-label="Main navigation">
    <div class="absolute ps-8 pt-6 z-10">
      <h1 :class="[
        'text-xl font-bold',
        theme === 'dark' ? 'text-white' : 'text-esmerald'
      ]">
        <router-link 
          :to="{ name: 'home' }"
          class="cursor-pointer"
          aria-label="Project App. - Professional Web Design & Development Company - Homepage"
          >
            Project<br>App.
        </router-link>
      </h1>
    </div>
    <div class="flex absolute z-10 pt-6 top-0 right-0 lg:pe-8">
      <button
        @click="toggleLanguage"
        class="inline-flex items-center gap-x-1 text-sm bg-window-black bg-opacity-40 backdrop-blur-md text-white font-regular py-2 px-4 rounded-xl mx-2 transition duration-250 ease-out hover:bg-esmerald"
        :aria-label="`Switch to ${languageStore.currentLanguage === 'en' ? 'Spanish' : 'English'}`">
        <span class="uppercase font-light">{{ languageStore.currentLanguage === 'en' ? 'EN' : 'ES' }}</span>
        <span class="sr-only">Change language</span>
      </button>
      <Popover class="relative">
        <PopoverButton 
          class="inline-flex items-center gap-x-1 text-md bg-window-black bg-opacity-40 backdrop-blur-md text-white font-regular py-2 px-8 rounded-xl mx-2 transition duration-250 ease-out hover:bg-esmerald"
          aria-expanded="auto"
          aria-haspopup="true">
          <span>
            {{ globalMessages?.menu_button || 'Menu' }}
          </span>
          <span class="sr-only">Open website navigation menu</span>
        </PopoverButton>

        <transition 
          enter-active-class="transition ease-out duration-200" 
          enter-from-class="opacity-0 translate-y-1" 
          enter-to-class="opacity-100 translate-y-0" 
          leave-active-class="transition ease-in duration-150" 
          leave-from-class="opacity-100 translate-y-0" 
          leave-to-class="opacity-0 translate-y-1"
          >
          <PopoverPanel class="absolute right-0 z-10 mt-5 flex max-w-min px-2" role="menu" aria-orientation="vertical">
            <div class="w-max grid grid-cols-2 rounded-xl bg-window-black bg-opacity-40 text-white backdrop-blur-md" role="menubar">
              <RouterLink
                :to="{ name:  item.href }" 
                v-for="(item, index) in solutions" 
                :key="index" 
                class="flex p-2 ps-4 font-regular text-white text-xl relative group"
                @mouseenter="hoverMenu($event, true)" 
                @mouseleave="hoverMenu($event, false)"
                role="menuitem"
              >
                {{ item.name }}
                <div class="absolute ms-4 left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300 group-hover:w-full underline"></div>
                <div class="relative ps-2 transform opacity-0 group-hover:opacity-100 transition-opacity duration-300 font-regular arrow">
                  ➜
                </div>
                <span class="sr-only">Navigate to {{ item.name }}</span>
              </RouterLink>
              <SocialLinks></SocialLinks>
              <ButtonWhitArrow @click="showModalEmail = true"></ButtonWhitArrow>
            </div>
          </PopoverPanel>
        </transition>
      </Popover>
      <button 
        @click="showModalEmail = true" 
        class="inline-flex items-center gap-x-1 text-md bg-window-black bg-opacity-40 backdrop-blur-md text-white font-regular py-2 px-8 rounded-xl mx-2 transition duration-250 ease-out hover:bg-esmerald"
        aria-label="Contact our website development team">
        {{ globalMessages?.get_in_touch || 'Get in touch' }}
        <span class="sr-only">Open contact form</span>
      </button>
    </div>
  </nav>

  <!--Navbar Mobile-->
  <nav class="block lg:hidden relative min-h-[60px] w-screen" aria-label="Mobile navigation">
    <div class="absolute ps-8 pt-6 z-10">
      <h1 :class="[
        'text-xl font-bold',
        theme === 'dark' ? 'text-white' : 'text-esmerald'
      ]">
        <router-link 
          :to="{ name: 'home' }" 
          class="cursor-pointer"
          aria-label="Project App. - Professional Web Design & Development Company - Homepage">
          Project<br>App.
        </router-link>
      </h1>
    </div>

    <div class="flex absolute z-10 pt-6 pe-6 top-0 right-0 space-x-2 text-white">
      <button
        @click="toggleLanguage"
        class="bg-window-black bg-opacity-40 backdrop-blur-md rounded-xl px-3 py-3 text-sm font-light"
        :aria-label="`Switch to ${languageStore.currentLanguage === 'en' ? 'Spanish' : 'English'}`">
        {{ languageStore.currentLanguage === 'en' ? 'EN' : 'ES' }}
        <span class="sr-only">Change language</span>
      </button>
      <button 
        @click="openMenuMobile" 
        class="bg-window-black bg-opacity-40 backdrop-blur-md rounded-xl px-4 py-3 text-md"
        aria-expanded="false"
        aria-haspopup="true"
        aria-controls="mobile-menu">
        {{ globalMessages?.menu_button || 'Menu' }}
        <span class="sr-only">Open mobile navigation menu</span>
      </button>
      <button 
        @click="showModalEmail = true" 
        class="bg-window-black bg-opacity-40 backdrop-blur-md rounded-xl px-4 py-3 flex justify-center items-center font-regular text-md"
        aria-label="Contact our web design team">
        {{ globalMessages?.get_in_touch || 'Get in touch' }}
        <span class="sr-only">Open contact form</span>
      </button>
    </div>
  </nav>

  <Teleport to="body">
    <div class="fixed inset-0 flex justify-end z-50" v-show="showMenu" id="mobile-menu" role="dialog" aria-modal="true" aria-label="Mobile navigation menu">
      <div 
        ref="background" 
        @click="closeBackdrop" 
        class="absolute inset-0 bg-gray-500 bg-opacity-40 backdrop-blur-md"
        aria-hidden="true">
      </div>
      <nav ref="menuBox" class="relative bg-lemon h-svh w-full max-w-[100vw] shadow-lg flex flex-col z-60 overflow-y-auto" aria-label="Mobile navigation options">
        <div class="flex justify-end py-3 pe-3">
          <button 
            @click="closeMenuMobile" 
            class="text-esmerald"
            aria-label="Close menu">
            <XMarkIcon class="w-8 h-8"></XMarkIcon>
            <span class="sr-only">Close navigation menu</span>
          </button>
        </div>
        <div class="flex flex-col flex-grow py-4">
          <RouterLink
            :to="{ name:  item.href }" 
            v-for="(item, index) in solutions" 
            :key="index" 
            class="flex p-2 ps-4 font-regular text-esmerald text-4xl relative group"
            @click="closeMenuMobile"
            aria-label="Navigate to {{ item.name }}"
            >
            {{ item.name }}
            <span class="sr-only">Navigate to {{ item.name }} page</span>
          </RouterLink>
        </div>
        <div class="w-full pb-4">
          <SocialLinks></SocialLinks>
          <div class="border-transparent border-t-esmerald border-opacity-40 border"></div>
          <ButtonWhitArrow @click="showModalEmail = true"></ButtonWhitArrow>
        </div>
      </nav>
    </div>
  </Teleport>

  <Email :visible="showModalEmail" @update:visible="showModalEmail = $event"></Email>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { gsap } from 'gsap';
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/vue';
import { XMarkIcon } from '@heroicons/vue/24/outline';
import SocialLinks from '@/components/utils/SocialLinks.vue';
import ButtonWhitArrow from '@/components/utils/ButtonWithArrow.vue';
import { useGlobalMessages } from '@/composables/useMessages';
import { useLanguageStore } from '@/stores/language';
import Email from '@/components/layouts/Email.vue';

const { globalMessages } = useGlobalMessages('navbar');

// Language store
const languageStore = useLanguageStore();

/**
 * Toggle between English and Spanish
 */
const toggleLanguage = () => {
  const newLocale = languageStore.currentLanguage === 'en' ? 'es-co' : 'en-us';
  
  // Get current path and replace locale prefix, then navigate to new locale URL
  const currentPath = window.location.pathname;
  const pathWithoutLocale = currentPath.replace(/^\/(es-co|en-us)/, '');
  const newPath = `/${newLocale}${pathWithoutLocale || ''}`;
  
  // Full navigation so all messages and components reload with the new locale
  window.location.href = newPath;
};

// Props 
defineProps({
  theme: {
    type: String,
    default: 'light', // puede ser 'light' o 'dark'
  }
})

// Referencias reactivas
const background = ref(null);
const menuBox = ref(null);
const showModalEmail = ref(false);
const showMenu = ref(false);

// Menu items as computed for reactive translations
const solutions = computed(() => {
  const s = globalMessages.value?.solutions || {};
  return [
    { name: s.home || 'Home', href: 'home' },
    { name: s.about || 'About', href: 'aboutUs' },
    { name: s.web_designs || 'Web designs', href: 'webDesigns' },
    { name: s.web_developments || 'Web developments', href: 'portfolioWorks' },
    { name: s.custom_software || 'Custom software', href: 'customSoftware' },
    { name: s.animations_3d || '3D animations', href: '3dAnimations' },
    { name: s.prices || 'Prices', href: 'eCommercePrices' },
    { name: s.hosting || 'Hosting', href: 'hosting' },
  ];
});

/**
 * Optimización de las animaciones de hover para los elementos del menú
 * Usa un único listener con delegación de eventos
 */
const hoverMenu = (event, isHover) => {
  const target = event.currentTarget;
  const underline = target.querySelector('.underline');
  const arrow = target.querySelector('.arrow');
  
  if (underline) {
    gsap.to(underline, { width: isHover ? '50%' : '0%', duration: 0.05 });
  }
  if (arrow) {
    gsap.to(arrow, { opacity: isHover ? 1 : 0, duration: 0.05 });
  }
};

/**
 * Abre el menú móvil con protección contra propagación.
 */
const openMenuMobile = (event) => {
  // Detener la propagación del evento para evitar que llegue al document
  event.stopPropagation();
  openMenu();
};

/**
 * Abre el menú con animaciones GSAP.
 */
const openMenu = () => {
  showMenu.value = true;
  
  // Retrasamos las animaciones hasta el siguiente frame para evitar bloqueo de renderizado
  requestAnimationFrame(() => {
    if (background.value && menuBox.value) {
      gsap.fromTo(
        background.value,
        { opacity: 0 },
        { opacity: 1, duration: 0.25, ease: "power2.inOut" }
      );
    
      gsap.fromTo(
        menuBox.value,
        { x: window.innerWidth },
        { x: 0, duration: 0.25, ease: "power2.inOut" }
      );
    }
  });
};

/**
 * Cierra el menú móvil con protección contra propagación.
 */
const closeMenuMobile = (event) => {
  // Detener la propagación del evento para evitar comportamientos inesperados
  event.stopPropagation();
  closeMenu();
};

/**
 * Cierra el menú desde el backdrop/background con protección contra propagación.
 */
const closeBackdrop = (event) => {
  // Detener la propagación del evento
  event.stopPropagation();
  closeMenu();
};

/**
 * Cierra el menú con animaciones GSAP.
 */
const closeMenu = () => {
  if (!background.value || !menuBox.value) return;
  
  const tl = gsap.timeline({
    onComplete: () => {
      showMenu.value = false;
    }
  });
  
  // Usar timeline para coordinar animaciones
  tl.to(menuBox.value, {
    x: menuBox.value.offsetWidth,
    duration: 0.25,
    ease: "power2.inOut"
  }, 0);
  
  tl.to(background.value, {
    opacity: 0,
    duration: 0.25,
    ease: "power2.inOut"
  }, 0);
};

// Inicialización de efectos al montar el componente
onMounted(() => {
  document.addEventListener('click', (e) => {
    // Solo cerrar el menú si está abierto y el clic no fue en el menú ni en el botón de apertura
    if (showMenu.value) {
      // Verificar si el clic fue en el menú o en cualquier elemento dentro de él
      const isClickInsideMenu = menuBox.value?.contains(e.target);
      // Verificar si el clic fue en el fondo semitransparente
      const isClickOnBackground = background.value === e.target;
      // Verificar si el clic fue en el botón de menú móvil (por selector)
      const menuBtn = document.querySelector('.block.lg\\:hidden .flex.absolute span:first-child');
      const isClickOnMenuButton = menuBtn?.contains(e.target);

      // Si el clic no fue en ninguno de estos elementos, cerrar el menú
      if (!isClickInsideMenu && !isClickOnBackground && !isClickOnMenuButton) {
        closeMenu();
      }
    }
  });
  
  // Cerrar menú al presionar Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && showMenu.value) {
      closeMenu();
    }
  });
});
</script>

<style scoped>
.underline, 
.arrow {
  will-change: transform, opacity, width;
}
</style>