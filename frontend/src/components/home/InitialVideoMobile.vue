<template>
    <div class="p-3 h-svh">
      <!-- Background video container -->
      <div class="relative w-full h-full overflow-hidden">
        <video
          class="absolute top-0 left-0 w-full h-full object-cover rounded-xl"
          autoplay
          muted
          loop
        >
          <source src="@/assets/videos/presentationMobile.mp4" type="video/mp4" />
          Your browser does not support the video tag.
        </video>
  
        <!-- "Play Reel" button -->
        <button
          class="absolute bottom-4 left-1/2 transform -translate-x-1/2 px-3 py-2 bg-window-black bg-opacity-40 backdrop-blur-md rounded-xl text-white font-regular flex items-center gap-2"
          @click="playReel"
        >
          <PlayIcon class="size-4" />
          {{ play_text }}
        </button>
      </div>
  
      <!-- Video Modal -->
      <div
        v-if="showModal"
        class="fixed inset-0 bg-window-black bg-opacity-90 backdrop-blur-md z-50 flex items-center justify-center"
      >
        <!-- Loading Animation -->
        <div
          v-if="isLoading"
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
        
        <!-- Video element only mounts if showVideo is true -->
        <video
          v-if="showVideo"
          ref="videoRef"
          class="w-full max-w-screen h-auto"
          autoplay
          playsinline
          :muted="false"
          @loadeddata="onVideoLoad"
        >
          <source src="@/assets/videos/presentationComp.mp4" type="video/mp4" />
          Your browser does not support the video tag.
        </video>
  
        <!-- Close button in the top-right corner -->
        <div class="absolute top-4 right-4 z-10">
          <button @click="closeModal" class="p-2">
            <XMarkIcon class="size-6 text-white" />
          </button>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, nextTick, watch } from 'vue';
  import { PlayIcon, XMarkIcon } from '@heroicons/vue/24/outline';
  import { Vue3Lottie } from "vue3-lottie";
  import whiteAnimation from "@/assets/loading/white.json";
  
  // Reactive variables to control modal and video mounting
  const showModal = ref(false);
  const showVideo = ref(false);
  const isLoading = ref(true);
  // Reference to the video element inside the modal
  const videoRef = ref(null);

  // Props passed to the component
  const props = defineProps({
    play_text: String, // The play button text passed from the parent component
  });
  
  /**
   * Event handler that forces the video to play if it gets paused.
   * This is used to prevent the user from pausing the video.
   */
  const handlePause = () => {
    if (videoRef.value) {
      videoRef.value.play();
    }
  };
  
  /**
   * Event handler that ensures the video is not muted or set to zero volume.
   */
  const handleVolumeChange = () => {
    const video = videoRef.value;
    if (video) {
      if (video.muted) video.muted = false;
      if (video.volume === 0) video.volume = 1;
    }
  };
  
  /**
   * Function to handle when the video has fully loaded.
   */
  const onVideoLoad = () => {
    // Set isLoading to false once the video has loaded
    isLoading.value = false;
  };
  
  // Watch for changes to the showModal state to control scroll
  watch(showModal, (newVal) => {
    if (newVal) {
      document.body.style.overflow = 'hidden'; // Desactiva el scroll
    } else {
      document.body.style.overflow = ''; // Activa el scroll
    }
  });
  
  /**
   * Handles the "Play Reel" button click.
   * - Displays the modal and mounts the video.
   * - Starts playback with sound enabled.
   * - Disables video controls and prevents context menu, pause, and volume change.
   */
  const playReel = async () => {
    showModal.value = true;
    isLoading.value = true;
    showVideo.value = true;
  
    await nextTick(); // Wait for the video element to mount in the DOM
    const video = videoRef.value;
  
    if (video) {
      try {
        // Enable sound and play video
        video.muted = false;
        await video.play();
  
        // Disable video controls
        video.controls = false;
        // Prevent context menu from appearing
        video.addEventListener('contextmenu', e => e.preventDefault());
        // Prevent user from pausing the video
        video.addEventListener('pause', handlePause);
        // Prevent user from muting or lowering volume
        video.addEventListener('volumechange', handleVolumeChange);
      } catch (err) {
        console.error('Autoplay with sound is not allowed by the browser:', err);
      }
    }
  };
  
  /**
   * Handles closing the modal:
   * - Removes event listeners to allow proper pausing.
   * - Pauses the video and resets it to the beginning.
   * - Hides the modal and unmounts the video element after a short delay.
   */
  const closeModal = () => {
    const video = videoRef.value;
  
    if (video) {
      // Remove event listeners to avoid forcing playback on pause
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('volumechange', handleVolumeChange);
  
      // Pause the video and reset playback position
      video.pause();
      video.currentTime = 0;
    }
  
    showModal.value = false;
    isLoading.value = true;
  
    // Unmount the video element to fully stop the video and release resources
    setTimeout(() => {
      showVideo.value = false;
    }, 300);
  };
  </script>
  