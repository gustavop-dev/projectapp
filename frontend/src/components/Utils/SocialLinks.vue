<template>
  <div
    class="mt-4 p-2 ps-4 border-transparent border-t-esmerald border-opacity-40 border grid grid-cols-2 lg:border-t-white"
  >
    <a href="https://www.instagram.com/paginaswebscolombia_?igsh=MWh3MHRha3A5MHFrbQ==" target="_blank" class="inline-block text-sm cursor-pointer font-regular social-link"
      >Instagram
      <ArrowUpRightIcon class="w-3 inline arrow-icon"></ArrowUpRightIcon
    ></a>
    <a href="https://www.facebook.com/paginaswebscolombiaoficial" target="_blank" class="inline-block text-sm ms-2 cursor-pointer font-regular social-link"
      >Facebook
      <ArrowUpRightIcon class="w-3 inline arrow-icon"></ArrowUpRightIcon
    ></a>
    <a href="https://wa.me/message/XX77FJEUEM26H1?src=qr" target="_blank" class="inline-block text-sm cursor-pointer font-regular social-link"
      >WhatsApp
      <ArrowUpRightIcon class="w-3 inline arrow-icon"></ArrowUpRightIcon
    ></a>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"; // Import ref for reactivity and onMounted for the lifecycle hook
import { gsap } from "gsap"; // Import GSAP for animations
import ArrowUpRightIcon from "@heroicons/vue/20/solid/ArrowUpRightIcon"; // Import the ArrowUpRightIcon from Heroicons

/**
 * Lifecycle hook that runs after the component is mounted.
 * 
 * This hook selects all elements with the class "social-link" and adds a mouse enter
 * event listener to animate the arrow icon inside each link. The animation makes the 
 * arrow move diagonally and disappear, then resets it back to the starting position and fades it in.
 */
onMounted(() => {
  const links = document.querySelectorAll(".social-link"); // Select all elements with the "social-link" class

  links.forEach((link) => {
    const arrow = link.querySelector(".arrow-icon"); // Find the arrow icon inside each link

    // Add mouseenter event to trigger animation
    link.addEventListener("mouseenter", () => {
      gsap.to(arrow, {
        x: 10, // Move arrow 10px to the right
        y: -10, // Move arrow 10px upwards
        opacity: 0, // Make arrow disappear
        duration: 0.1, // Animation duration
        onComplete: () => {
          // Reset arrow position and opacity
          gsap.set(arrow, { x: -10, y: 10, opacity: 0 });
          // Fade in the arrow and bring it back to its original position
          gsap.to(arrow, { x: 0, y: 0, opacity: 1, duration: 0.1 });
        },
      });
    });
  });
});
</script>

<style scoped>
.social-link {
  position: relative;
  display: inline-block;
  overflow: hidden;
}

.arrow-icon {
  display: inline-block;
}
</style>
