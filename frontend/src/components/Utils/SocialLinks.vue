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
import { ref, onMounted } from "vue";
import { gsap } from "gsap";
import ArrowUpRightIcon from "@heroicons/vue/20/solid/ArrowUpRightIcon";

onMounted(() => {
  const links = document.querySelectorAll(".social-link");

  links.forEach((link) => {
    const arrow = link.querySelector(".arrow-icon");
    link.addEventListener("mouseenter", () => {
      gsap.to(arrow, {
        x: 10,
        y: -10,
        opacity: 0,
        duration: 0.1,
        onComplete: () => {
          gsap.set(arrow, { x: -10, y: 10, opacity: 0 });
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
