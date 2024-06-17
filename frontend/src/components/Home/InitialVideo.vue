<template>
    <div class="p-3 h-screen" @mousemove="handleMouseMove" @mouseenter="showBall" @mouseleave="hideBall">
      <div class="relative w-full h-full overflow-hidden">
        <video class="absolute top-0 left-0 w-full h-full object-cover rounded-xl" autoplay muted loop>
          <source src="@/assets/videos/presentationPrevPc.mp4" type="video/mp4">
          Your browser does not support the video tag.
        </video>
        <div ref="ball" class="absolute bg-window-black bg-opacity-40 backdrop-blur-md text-white rounded-full flex items-center justify-center w-32 h-32 transition-opacity duration-300 cursor-pointer" @click="showModal = true">
          <span ref="ballText" class="font-light text-xl">Play Reel</span>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 flex items-center justify-center z-50" @mousemove="handleModalMouseMove">
      <div class="relative w-screen h-screen">
        <video ref="modalVideo" class="w-full h-full object-cover" autoplay>
          <source src="@/assets/videos/presentationComp.mp4" type="video/mp4">
          Your browser does not support the video tag.
        </video>
      </div>
      <div ref="modalBall" class="absolute z-50 bg-window-black bg-opacity-60 backdrop-blur-md text-white rounded-full flex items-center justify-center w-20 h-20 transition-opacity duration-300 cursor-pointer" @click="closeModal">
        <XMarkIcon ref="modalBallText" class="w-8"></XMarkIcon>
      </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { gsap } from 'gsap';
import { XMarkIcon } from '@heroicons/vue/24/outline';

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

const showBall = () => {
  gsap.to(ball.value, { opacity: 1, duration: 0.5 });
};

const hideBall = () => {
  gsap.to(ball.value, { opacity: 0, duration: 0.5 });
};

const closeModal = () => {
  showModal.value = false;
  if (modalVideo.value) {
    modalVideo.value.pause();
    modalVideo.value.currentTime = 0;
  }
};

onMounted(() => {
  gsap.set(ball.value, { opacity: 0 });  
  updateBallPosition();
  watch(showModal, (newVal) => {
    if (newVal && modalVideo.value) {
      modalVideo.value.muted = false;
      modalVideo.value.play();
    }
  });
});

onUnmounted(() => {
  cancelAnimationFrame(updateBallPosition);
});
</script>
