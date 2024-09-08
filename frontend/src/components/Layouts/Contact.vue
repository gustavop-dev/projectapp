<template>
  <section class="p-3">
          <div class="border-t-2 border-t-gray-250 grid lg:h-80 lg:grid-cols-2">
              <div class="mt-16 lg:ps-8">
                  <h2 class="text-esmerald text-4xl font-regular" v-html="globalMessages.heading"></h2>
              </div>
              <div class="grid mt-16 lg:grid-cols-2">
                  <div class="relative border-s-2 border-s-gray-250 ps-4 py-8">
                      <h3 class="text-esmerald text-4xl font-regular">
                        {{ globalMessages.mail_us_title }}
                      </h3>
                      <p class="mt-4 text-green-light text-lg font-regular">
                        {{ globalMessages.mail_us_description }}
                      </p>
                      <a 
                        @click="showModalEmail = true" 
                        ref="emailLink" 
                        @mouseover="animateLink" 
                        @mouseleave="resetLink" 
                        class="inline-block text-xl absolute bottom-0 text-esmerald cursor-pointer"
                        >
                        {{ globalMessages.email_address }}
                        <span 
                          ref="underline" 
                          class="absolute left-0 bottom-0 h-0.5 w-0 bg-black transition-all duration-300"
                          >
                        </span>
                        <span 
                          ref="arrow" 
                          class="absolute right-0 top-1/2 transform -translate-y-1/2 opacity-0 transition-opacity duration-300"
                          >
                          ➜
                        </span>
                      </a>
                  </div>
                  <div class="relative border-s-2 border-s-gray-250 ps-4 py-8">
                      <h3 class="text-esmerald text-4xl font-regular">
                        {{ globalMessages.direct_contact_title }}
                      </h3>
                      <p class="mt-4 text-green-light text-lg font-regular">
                        {{ globalMessages.direct_contact_description }}
                      </p>
                      <a 
                        href="https://wa.me/message/XX77FJEUEM26H1?src=qr" 
                        target="_blank" 
                        ref="chatLink" 
                        @mouseover="animateLinkChat" 
                        @mouseleave="resetLinkChat" 
                        class="inline-block text-xl absolute bottom-0 text-esmerald cursor-pointer"
                        >
                        {{ globalMessages.chat }}
                        <span 
                          ref="underlineChat" 
                          class="absolute left-0 bottom-0 h-0.5 w-0 bg-black transition-all duration-300"
                          >
                        </span>
                        <span 
                          ref="arrowChat" 
                          class="absolute right-0 top-1/2 transform -translate-y-1/2 opacity-0 transition-opacity duration-300"
                          >
                          ➜
                        </span>
                      </a>
                  </div>
              </div>
          </div>
      </section>
      <Email :visible="showModalEmail" @update:visible="showModalEmail = $event"></Email>
</template>

<script setup>
import { ref } from 'vue'; // Import ref for reactivity
import { gsap } from 'gsap'; // Import GSAP for animations
import Email from '@/components/layouts/Email.vue'; // Import the Email component
import { useGlobalMessages } from '@/composables/useMessages'; // Import the custom composable for global messages

const { globalMessages } = useGlobalMessages('contact_section'); // Get global messages for the contact section

// State to control the visibility of the email modal
const showModalEmail = ref(false);

// Refs for the email and chat links, and their underline and arrow elements
const emailLink = ref(null);
const chatLink = ref(null);
const underline = ref(null);
const arrow = ref(null);
const underlineChat = ref(null);
const arrowChat = ref(null);

/**
 * Animates the underline and arrow for the email link.
 * 
 * Expands the underline and makes the arrow visible.
 */
const animateLink = () => {
  gsap.to(underline.value, { width: '100%', duration: 0.05 }); // Expand the underline
  gsap.to(arrow.value, { opacity: 1, x: 30, duration: 0.05 }); // Move and show the arrow
};

/**
 * Resets the underline and arrow for the email link.
 * 
 * Collapses the underline and hides the arrow.
 */
const resetLink = () => {
  gsap.to(underline.value, { width: '0%', duration: 0.05 }); // Collapse the underline
  gsap.to(arrow.value, { opacity: 0, x: 20, duration: 0.05 }); // Hide the arrow and move it back
};

/**
 * Animates the underline and arrow for the chat link.
 * 
 * Expands the underline and makes the arrow visible.
 */
const animateLinkChat = () => {
  gsap.to(underlineChat.value, { width: '100%', duration: 0.05 }); // Expand the underline for chat
  gsap.to(arrowChat.value, { opacity: 1, x: 30, duration: 0.05 }); // Move and show the arrow for chat
};

/**
 * Resets the underline and arrow for the chat link.
 * 
 * Collapses the underline and hides the arrow.
 */
const resetLinkChat = () => {
  gsap.to(underlineChat.value, { width: '0%', duration: 0.05 }); // Collapse the underline for chat
  gsap.to(arrowChat.value, { opacity: 0, x: 20, duration: 0.05 }); // Hide the arrow and move it back for chat
};
</script>