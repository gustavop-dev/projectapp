<template>
    <div class="p-3 h-screen" @mousemove="handleMouseMove" @mouseenter="showBall" @mouseleave="hideBall">
      <div class="relative w-full h-full overflow-hidden">
        <video class="absolute top-0 left-0 w-full h-full object-cover rounded-xl" autoplay muted loop>
          <source src="@/assets/videos/presentationPrevPc.mp4" type="video/mp4">
          Your browser does not support the video tag.
        </video>
        <div ref="ball" class="absolute bg-window-black bg-opacity-40 backdrop-blur-md text-white rounded-full flex items-center justify-center w-32 h-32 transition-opacity duration-300 cursor-pointer" @click="showModal = true">
          <span ref="ballText" class="font-light text-xl">{{ play_text }}</span>
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
import { ref, onMounted, onUnmounted, watch } from 'vue'; // Import Vue utilities for reactivity and lifecycle hooks
import { gsap } from 'gsap'; // Import GSAP for animations
import { XMarkIcon } from '@heroicons/vue/24/outline'; // Import Heroicon for the close icon

// Reactive references for controlling the modal, ball, and video elements
const showModal = ref(false); // Controls the visibility of the modal
const ball = ref(null); // Reference for the ball element
const ballText = ref(null); // Reference for the text inside the ball
const modalBall = ref(null); // Reference for the ball in the modal
const modalBallText = ref(null); // Reference for the text inside the modal ball
const modalVideo = ref(null); // Reference for the video in the modal

// Variables to track mouse and element positions
let mouseX = 0, mouseY = 0, modalMouseX = 0, modalMouseY = 0;
let ballX = 0, ballY = 0, textX = 0, textY = 0;
let modalBallX = 0, modalBallY = 0, modalTextX = 0, modalTextY = 0;

// Props passed to the component
const props = defineProps({
  play_text: String, // The play button text passed from the parent component
});

/**
 * Handles mouse movement and updates the coordinates for the ball element.
 * 
 * @param {Event} event - The mouse move event.
 */
const handleMouseMove = (event) => {
  const rect = event.currentTarget.getBoundingClientRect();
  mouseX = event.clientX - rect.left;
  mouseY = event.clientY - rect.top;
};

/**
 * Handles mouse movement inside the modal and updates the coordinates for the modal ball element.
 * 
 * @param {Event} event - The mouse move event inside the modal.
 */
const handleModalMouseMove = (event) => {
  const rect = event.currentTarget.getBoundingClientRect();
  modalMouseX = event.clientX - rect.left;
  modalMouseY = event.clientY - rect.top;
};

/**
 * Continuously updates the position of the ball and its text based on mouse movement.
 * Also updates the position of the modal ball and its text inside the modal.
 */
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

  requestAnimationFrame(updateBallPosition); // Keep updating the position on each animation frame
};

/**
 * Shows the ball by animating its opacity to 1.
 */
const showBall = () => {
  gsap.to(ball.value, { opacity: 1, duration: 0.5 });
};

/**
 * Hides the ball by animating its opacity to 0.
 */
const hideBall = () => {
  gsap.to(ball.value, { opacity: 0, duration: 0.5 });
};

/**
 * Closes the modal and pauses the video, resetting it to the beginning.
 */
const closeModal = () => {
  showModal.value = false;
  if (modalVideo.value) {
    modalVideo.value.pause();
    modalVideo.value.currentTime = 0;
  }
};

// Lifecycle hook that runs when the component is mounted
onMounted(() => {
  gsap.set(ball.value, { opacity: 0 }); // Initialize the ball with 0 opacity
  updateBallPosition(); // Start updating the ball's position based on mouse movement

  // Watch for changes to the showModal state and play the video if the modal is opened
  watch(showModal, (newVal) => {
    if (newVal && modalVideo.value) {
      modalVideo.value.muted = false;
      modalVideo.value.play();
    }
  });
});

// Lifecycle hook that runs when the component is unmounted
onUnmounted(() => {
  cancelAnimationFrame(updateBallPosition); // Stop updating the ball's position
});
</script>