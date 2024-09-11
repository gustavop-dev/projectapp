<template>
  <div class="flex justify-center">
    <button 
      class="relative flex justify-center items-center py-4 w-3/4 my-4 font-regular rounded-xl bg-esmerald text-white lg:bg-lemon lg:text-esmerald js-hover-button"
      >
      <span class="inline-block js-text-animated">
        {{ globalMessages.contact_us }}
      </span>
      <ArrowRightIcon class="w-4 h-4 opacity-0 js-arrow-icon" />
    </button>
  </div>
</template>

<script setup>
import {onMounted } from 'vue'; // Import onMounted for lifecycle hook
import { gsap } from 'gsap'; // Import GSAP for animations
import ArrowRightIcon from '@heroicons/vue/20/solid/ArrowRightIcon'; // Import the ArrowRightIcon from Heroicons
import { useGlobalMessages } from '@/composables/useMessages'; // Import the custom composable for global messages

const { globalMessages } = useGlobalMessages('navbar'); // Get global messages for the 'navbar' section

/**
 * Lifecycle hook that runs after the component is mounted.
 * 
 * This hook selects the button with the class 'hover-button' and adds mouse enter and
 * mouse leave events to animate the arrow icon and text within the button when the user hovers over it.
 */
onMounted(() => {
  const button = document.querySelector('.js-hover-button'); // Select the button element with the class 'hover-button'
  const arrow = button.querySelector('.js-arrow-icon'); // Select the arrow icon inside the button
  const text = button.querySelector('.js-text-animated'); // Select the text (span) inside the button

  // Add mouseenter event to trigger the hover animation
  button.addEventListener('mouseenter', () => {
    gsap.to(arrow, {
      opacity: 1, // Fade in the arrow
      x: 0, // Move the arrow to its original position
      duration: 0.2, // Duration of the animation
      onStart: () => {
        gsap.set(arrow, { x: -20 }); // Start the arrow from -20px (offscreen to the left)
      },
    });
    gsap.to(text, {
      x: -12, // Move the text 12px to the left
      duration: 0.2, // Duration of the animation
    });
  });

  // Add mouseleave event to reset the button animation
  button.addEventListener('mouseleave', () => {
    gsap.to(arrow, {
      opacity: 0, // Fade out the arrow
      x: 20, // Move the arrow offscreen to the right
      duration: 0.2, // Duration of the animation
    });
    gsap.to(text, {
      x: 0, // Move the text back to its original position
      duration: 0.2, // Duration of the animation
    });
  });
});
</script>

<style scoped>
.hover-button {
  position: relative;
  overflow: hidden;
}

.arrow-icon {
  transition: opacity 0.5s, transform 0.5s;
}
</style>
