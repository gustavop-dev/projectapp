<template>
  <div class="flex justify-center">
    <button class="relative flex justify-center items-center bg-lemon py-4 w-3/4 my-4 text-esmerald font-regular rounded-xl hover-button">
      <span class="inline-block">Contact us</span>
      <ArrowRightIcon class="w-4 h-4 opacity-0 arrow-icon" />
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { gsap } from 'gsap';
import ArrowRightIcon from '@heroicons/vue/20/solid/ArrowRightIcon';

onMounted(() => {
  const button = document.querySelector('.hover-button');
  const arrow = button.querySelector('.arrow-icon');
  const text = button.querySelector('span');

  button.addEventListener('mouseenter', () => {
    gsap.to(arrow, {
      opacity: 1,
      x: 0,
      duration: 0.2,
      onStart: () => {
        gsap.set(arrow, { x: -20 });
      },
    });
    gsap.to(text, {
      x: -12,
      duration: 0.2,
    });
  });

  button.addEventListener('mouseleave', () => {
    gsap.to(arrow, {
      opacity: 0,
      x: 20,
      duration: 0.2,
    });
    gsap.to(text, {
      x: 0,
      duration: 0.2,
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
