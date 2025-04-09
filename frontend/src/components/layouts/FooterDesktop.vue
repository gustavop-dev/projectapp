<template>
  <div class="p-3 h-svh" @mousemove="handleMouseMove">
    <div class="relative w-full h-full overflow-hidden">
      <video ref="mainVideo" class="absolute top-0 left-0 w-full h-full object-cover rounded-xl" autoplay muted loop preload="metadata">
        <source src="@/assets/videos/presentationPrevPc.mp4" type="video/mp4">
        Your browser does not support the video tag.
      </video>
      <div 
        ref="ball" 
        class="absolute bg-window-black bg-opacity-40 backdrop-blur-md text-white rounded-full flex items-center justify-center w-32 h-32 transition-opacity duration-300 cursor-pointer" 
        @click="showModal = true"
        >
        <span ref="ballText" class="font-light text-xl">
          {{ globalMessages.play_reel }}
        </span>
      </div>
      <div class="absolute bottom-0 right-0 w-full h-1/2 rounded-b-xl bg-window-black bg-opacity-40 backdrop-blur-md">
          <div class="flex justify-end w-full">
            <div class="md:w-max grid grid-cols-2 text-white mt-4">
              <RouterLink
                :to="{ name:  item.href }" 
                v-for="item in solutions" 
                :key="item.name" 
                :href="item.href" 
                class="flex p-2 ps-4 font-regular text-white text-xl relative group"
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
              <div class="mt-4 p-2 ps-4">
                <a 
                  href="https://www.instagram.com/projectapp.co/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  class="block text-lg cursor-pointer social-link text-white font-regular"
                  >
                  {{ globalMessages.instagram }} 
                  <ArrowUpRightIcon class="w-5 inline arrow-icon"></ArrowUpRightIcon>
                </a>
                <a 
                  href="https://www.facebook.com/projectapp.co" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  class="block text-lg cursor-pointer social-link text-white font-regular"
                  >
                  {{ globalMessages.facebook }} 
                  <ArrowUpRightIcon class="w-5 inline arrow-icon"></ArrowUpRightIcon>
                </a>
                <a 
                  href="https://wa.me/message/XX77FJEUEM26H1?src=qr" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  class="block text-lg cursor-pointer social-link text-white font-regular">
                  {{ globalMessages.whatsapp }} 
                  <ArrowUpRightIcon class="w-5 inline arrow-icon"></ArrowUpRightIcon>
                </a>
                <a 
                  @click.prevent="showModalEmail = true"
                  href="#"
                  class="flex cursor-pointer font-regular text-white text-lg relative group"
                  @mouseover="hoverMenu($event, true)" 
                  @mouseleave="hoverMenu($event, false)"
                  >
                  {{ globalMessages.email_address }}
                  <div class="absolute left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300 group-hover:w-full"></div>
                </a>
              </div>
            </div>
          </div>
        <div class="flex w-full justify-between absolute bottom-0">
            <h3 
              class="hidden ms-4 mb-4 text-lg font-regular text-white opacity-40 lg:block"
              >
              {{ globalMessages.based_in }}
            </h3>
            <h3 class="hidden me-4 mb-4 text-lg font-regular text-white opacity-40 lg:block">
              {{ globalMessages.copyright }}
            </h3>
        </div>
      </div>
    </div>
  </div>

  <!-- Modal -->
  <Teleport to="body">
    <div 
      v-if="showModal" 
      class="fixed inset-0 flex items-center justify-center z-50 bg-black bg-opacity-50 backdrop-blur-md" 
      @mousemove="handleModalMouseMove"
      >
      <!-- Loading Animation -->
      <div
        v-show="isLoading"
        class="absolute inset-0 flex items-center justify-center"
      >
          <Vue3Lottie
            :animationData="whiteAnimation"
            :height="300"
            :width="300"
            :loop="true"
            :autoplay="true"
          />
      </div>
      <div 
        v-show="!isLoading" 
        class="relative w-screen lg:h-svh"
      >
        <video 
          ref="modalVideo" 
          class="w-full h-full object-cover" 
          muted
          preload="metadata"
          @loadeddata="onVideoLoad"
        >
          <source src="@/assets/videos/presentationComp.mp4" type="video/mp4">
          Your browser does not support the video tag.
        </video>
      </div>
      <div 
        ref="modalBall" 
        class="absolute z-50 bg-window-black bg-opacity-60 backdrop-blur-md text-white rounded-full flex items-center justify-center w-20 h-20 transition-opacity duration-300 cursor-pointer" 
        @click="closeModal"
        >
        <XMarkIcon ref="modalBallText" class="w-8"></XMarkIcon>
      </div>
    </div>
  </Teleport>
  
  <Email :visible="showModalEmail" @update:visible="showModalEmail = $event"></Email>
</template>

<script setup>
import Email from '@/components/layouts/Email.vue';
import { ref, onMounted, onUnmounted, watch, shallowRef } from 'vue';
import { gsap } from 'gsap';
import { XMarkIcon } from '@heroicons/vue/24/outline';
import ArrowUpRightIcon from '@heroicons/vue/20/solid/ArrowUpRightIcon';
import { useGlobalMessages } from '@/composables/useMessages';
import { useFreeResources } from '@/composables/useFreeResources';

// Usar importación dinámica para reducir el tamaño del bundle inicial
const Vue3Lottie = shallowRef(null);
const whiteAnimation = shallowRef(null);

// Cargar componentes no críticos de forma diferida
onMounted(async () => {
  const [lottieModule, animationModule] = await Promise.all([
    import("vue3-lottie"),
    import("@/assets/loading/white.json")
  ]);
  
  Vue3Lottie.value = lottieModule.Vue3Lottie;
  whiteAnimation.value = animationModule.default;
});

const { globalMessages } = useGlobalMessages('footer');

// Animación de estado de carga
const isLoading = ref(true);

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

const showModal = ref(false);
const ball = ref(null);
const ballText = ref(null);
const modalBall = ref(null);
const modalBallText = ref(null);
const mainVideo = ref(null);
const modalVideo = ref(null);

// Variables para seguimiento de ratón y posiciones de elementos
let mouseX = 0, mouseY = 0, modalMouseX = 0, modalMouseY = 0;
let ballX = 0, ballY = 0, textX = 0, textY = 0;
let modalBallX = 0, modalBallY = 0, modalTextX = 0, modalTextY = 0;
let animationFrameId = null;

/**
 * Función que se ejecuta cuando el video se ha cargado completamente.
 */
const onVideoLoad = () => {
  isLoading.value = false;
  if (modalVideo.value) {
    modalVideo.value.play();
  }
};

/**
 * Maneja el movimiento del ratón dentro de un elemento específico.
 * Actualiza las coordenadas del ratón relativas a la posición del elemento.
 * 
 * @param {Event} event - El evento de movimiento del ratón.
 */
const handleMouseMove = (event) => {
  const rect = event.currentTarget.getBoundingClientRect();
  mouseX = event.clientX - rect.left;
  mouseY = event.clientY - rect.top;
};

/**
 * Maneja el movimiento del ratón dentro del modal.
 * Actualiza las coordenadas específicas del modal.
 * 
 * @param {Event} event - El evento de movimiento del ratón dentro del modal.
 */
const handleModalMouseMove = (event) => {
  const rect = event.currentTarget.getBoundingClientRect();
  modalMouseX = event.clientX - rect.left;
  modalMouseY = event.clientY - rect.top;
};

/**
 * Actualiza continuamente la posición de la bola y su texto basado en el movimiento del ratón.
 * Utiliza GSAP para animaciones suaves.
 */
const updateBallPosition = () => {
  if (ball.value) {
    ballX += (mouseX - ballX - ball.value.offsetWidth / 2) * 0.2;
    ballY += (mouseY - ballY - ball.value.offsetHeight / 2) * 0.2;
    gsap.to(ball.value, { x: ballX, y: ballY, duration: 0.1, ease: 'power2.out' });
  }

  if (ballText.value) {
    textX += (mouseX - ballX - textX - ball.value?.offsetWidth / 2 || 0) * 0.15;
    textY += (mouseY - ballY - textY - ball.value?.offsetHeight / 2 || 0) * 0.15;
    gsap.to(ballText.value, { x: textX, y: textY, duration: 0.1, ease: 'power2.out' });
  }

  if (showModal.value && modalBall.value) {
    modalBallX += (modalMouseX - modalBallX - window.innerWidth / 2) * 0.2;
    modalBallY += (modalMouseY - modalBallY - window.innerHeight / 2) * 0.2;
    gsap.to(modalBall.value, { x: modalBallX, y: modalBallY, duration: 0.1, ease: 'power2.out' });
  
    if (modalBallText.value) {
      modalTextX += (modalMouseX - modalBallX - modalTextX - window.innerWidth / 2) * 0.15;
      modalTextY += (modalMouseY - modalBallY - modalTextY - window.innerHeight / 2) * 0.15;
      gsap.to(modalBallText.value, { x: modalTextX, y: modalTextY, duration: 0.1, ease: 'power2.out' });
    }
  }

  animationFrameId = requestAnimationFrame(updateBallPosition);
};

/**
 * Cierra el modal y pausa el video si corresponde.
 */
const closeModal = () => {
  showModal.value = false;
  if (modalVideo.value) {
    modalVideo.value.pause();
    modalVideo.value.currentTime = 0;
  }
};

/**
 * Maneja animaciones de hover para elementos de menú.
 * 
 * @param {Event} event - El evento de hover.
 * @param {Boolean} isHover - Si el elemento del menú está siendo hover o no.
 */
const hoverMenu = (event, isHover) => {
  const underline = event.target.querySelector('.underline');
  const arrow = event.target.querySelector('.arrow');
  if (underline) {
    gsap.to(underline, { width: isHover ? '100%' : '0%', duration: 0.3 });
  }
  if (arrow) {
    gsap.to(arrow, { opacity: isHover ? 1 : 0, duration: 0.3 });
  }
};

// Hook de ciclo de vida que se ejecuta cuando el componente está montado
onMounted(() => {
  // Iniciar la actualización de la posición de la bola
  animationFrameId = requestAnimationFrame(updateBallPosition);

  // Observar cambios en el estado showModal y reproducir/pausar el video en consecuencia
  watch(showModal, (newVal) => {
    if (newVal) {
      document.body.style.overflow = 'hidden';
      isLoading.value = true;
      
      // Cargar el video solo cuando se muestra el modal
      if (modalVideo.value) {
        modalVideo.value.load();
      }
    } else {
      document.body.style.overflow = '';
    }
  });

  // Añadir efectos hover a los enlaces sociales usando delegación de eventos
  const container = document.querySelector('.w-60');
  if (container) {
    container.addEventListener('mouseenter', (e) => {
      if (e.target.classList.contains('social-link')) {
        const arrow = e.target.querySelector('.arrow-icon');
        if (arrow) {
          gsap.to(arrow, {
            x: 10,
            y: -10,
            opacity: 0,
            duration: 0.1,
            onComplete: () => {
              gsap.set(arrow, { x: -10, y: 10, opacity: 0 });
              gsap.to(arrow, { x: 0, y: 0, opacity: 1, duration: 0.1 });
            }
          });
        }
      }
    }, true);
  }
});

// Hook de ciclo de vida que se ejecuta cuando el componente es desmontado
onUnmounted(() => {
  // Detener las actualizaciones de la posición de la bola
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
  }
});

// Usar recursos gratuitos para limpiar los recursos de video al desmontar
useFreeResources({
  videos: [mainVideo, modalVideo],
});
</script>

<style scoped>
.group:hover .group-hover\:w-full {
  width: 50%;
}
.group:hover .group-hover\:opacity-100 {
  opacity: 1;
}
</style>