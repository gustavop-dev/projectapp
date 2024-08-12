<template>
    <div class="p-3 h-screen" @mousemove="handleMouseMove">
      <div class="relative w-full h-full overflow-hidden">
        <video class="absolute top-0 left-0 w-full h-full object-cover rounded-xl" autoplay muted loop>
          <source src="@/assets/videos/presentationPrevPc.mp4" type="video/mp4">
          Your browser does not support the video tag.
        </video>
        <div ref="ball" class="absolute bg-window-black bg-opacity-40 backdrop-blur-md text-white rounded-full flex items-center justify-center w-32 h-32 transition-opacity duration-300 cursor-pointer" @click="showModal = true">
          <span ref="ballText" class="font-light text-xl">Play Reel</span>
        </div>
        <div class="absolute bottom-0 right-0 w-full h-1/2 rounded-b-xl bg-window-black bg-opacity-40 backdrop-blur-md">
            <div class="grid lg:grid-cols-2">
              <div>
                <h3 class="hidden ms-4 mb-4 absolute bottom-0 text-lg font-regular text-white opacity-40 lg:block">Based in Colombia, working worldwild</h3>
              </div>
              <div class="grid lg:grid-cols-2">
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
                  <h3 class="hidden ms-4 mb-4 absolute bottom-0 text-lg font-regular text-white opacity-40 lg:block">©2024 Project App</h3>
                </div>
                <div class="w-60">
                  <div class="mt-4 p-2 ps-4">
                    <a href="https://www.instagram.com/paginaswebscolombia_?igsh=MWh3MHRha3A5MHFrbQ==" target="_blank" class="block text-lg cursor-pointer social-link text-white font-regular">Instagram <ArrowUpRightIcon class="w-5 inline arrow-icon"></ArrowUpRightIcon></a>
                    <a href="https://www.facebook.com/paginaswebscolombiaoficial" target="_blank" class="block text-lg cursor-pointer social-link text-white font-regular">Facebook <ArrowUpRightIcon class="w-5 inline arrow-icon"></ArrowUpRightIcon></a>
                    <a href="https://wa.me/message/XX77FJEUEM26H1?src=qr" target="_blank" class="block text-lg cursor-pointer social-link text-white font-regular">WhatsApp <ArrowUpRightIcon class="w-5 inline arrow-icon"></ArrowUpRightIcon></a>
                    <a 
                    @click="showModalEmail = true"
                    class="flex cursor-pointer font-regular text-white text-lg relative group"
                    @mouseover="hoverMenu($event, true)" 
                    @mouseleave="hoverMenu($event, false)"
                  >
                    hello@projectapp.co
                    <div class="absolute left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300 group-hover:w-full"></div>
                  </a>
                  </div>
                </div>
              </div>
            </div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 flex items-center justify-center z-50 bg-black bg-opacity-50 backdrop-blur-md" @mousemove="handleModalMouseMove">
      <div class="relative w-screen lg:h-screen">
        <video ref="modalVideo" class="w-full h-full object-cover" autoplay>
          <source src="@/assets/videos/presentationComp.mp4" type="video/mp4">
          Your browser does not support the video tag.
        </video>
      </div>
      <div ref="modalBall" class="absolute z-50 bg-window-black bg-opacity-60 backdrop-blur-md text-white rounded-full flex items-center justify-center w-20 h-20 transition-opacity duration-300 cursor-pointer" @click="closeModal">
        <XMarkIcon ref="modalBallText" class="w-8"></XMarkIcon>
      </div>
    </div>
    <Email :visible="showModalEmail" @update:visible="showModalEmail = $event"></Email>
</template>

<script setup>
import Email from '@/components/layouts/Email.vue';
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { gsap } from 'gsap';
import { XMarkIcon } from '@heroicons/vue/24/outline'
import ArrowUpRightIcon from '@heroicons/vue/20/solid/ArrowUpRightIcon';

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
const showModal = ref(false);
const ball = ref(null);
const ballText = ref(null);
const modalBall = ref(null);
const modalBallText = ref(null);
const modalVideo = ref(null);
let mouseX = 0;
let mouseY = 0;
let modalMouseX = 0;
let modalMouseY = 0;
let ballX = 0;
let ballY = 0;
let textX = 0;
let textY = 0;
let modalBallX = 0;
let modalBallY = 0;
let modalTextX = 0;
let modalTextY = 0;


const handleMouseMove = (event) => {
  const rect = event.currentTarget.getBoundingClientRect();
  mouseX = event.clientX - rect.left;
  mouseY = event.clientY - rect.top;
};

const handleModalMouseMove = (event) => {
  const rect = event.currentTarget.getBoundingClientRect();
  modalMouseX = event.clientX - rect.left;
  modalMouseY = event.clientY - rect.top;
};

const updateBallPosition = () => {
  if (ball.value) {
    ballX += (mouseX - ballX - ball.value.offsetWidth / 2) * 0.2;
    ballY += (mouseY - ballY - ball.value.offsetHeight / 2) * 0.2;

    gsap.to(ball.value, { x: ballX, y: ballY, duration: 0.1, ease: 'power2.out' });
  }

  if (ballText.value) {
    textX += (mouseX - ballX - textX - ball.value.offsetWidth / 2) * 0.15;
    textY += (mouseY - ballY - textY - ball.value.offsetHeight / 2) * 0.15;

    gsap.to(ballText.value, { x: textX, y: textY, duration: 0.1, ease: 'power2.out' });
  }

  if (modalBall.value) {
    modalBallX += (modalMouseX - modalBallX - (window.innerWidth / 2)) * 0.2;
    modalBallY += (modalMouseY - modalBallY - (window.innerHeight / 2)) * 0.2;

    gsap.to(modalBall.value, { x: modalBallX, y: modalBallY, duration: 0.1, ease: 'power2.out' });
  }

  if (modalBallText.value) {
    modalTextX += (modalMouseX - modalBallX - modalTextX - (window.innerWidth / 2)) * 0.15;
    modalTextY += (modalMouseY - modalBallY - modalTextY - (window.innerHeight / 2)) * 0.15;

    gsap.to(modalBallText.value, { x: modalTextX, y: modalTextY, duration: 0.1, ease: 'power2.out' });
  }

  requestAnimationFrame(updateBallPosition);
};

const closeModal = () => {
  showModal.value = false;
  if (modalVideo.value) {
    modalVideo.value.pause();
    modalVideo.value.currentTime = 0;
  }
};

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

onMounted(() => {
  updateBallPosition();
  watch(showModal, (newVal) => {
    if (newVal && modalVideo.value) {
      modalVideo.value.muted = false;
      modalVideo.value.play();
    }
  });

  const links = document.querySelectorAll('.social-link');
  
    links.forEach(link => {
      const arrow = link.querySelector('.arrow-icon');
      link.addEventListener('mouseenter', () => {
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
      });
    });
});

onUnmounted(() => {
  cancelAnimationFrame(updateBallPosition);
});
</script>

<style>
.group:hover .group-hover\:w-full {
  width: 50%;
}
.group:hover .group-hover\:opacity-100 {
  opacity: 1;
}
</style>