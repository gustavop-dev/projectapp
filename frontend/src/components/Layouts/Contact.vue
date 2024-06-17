<template>
    <section class="p-3">
            <div class="border-t-2 border-t-gray-250 grid grid-cols-2 h-80">
                <div class="ps-8 mt-16">
                    <h2 class="text-esmerald text-4xl font-regular">Connect with us today.<br>Start your project in minutes.<br>Experience excellence forever.</h2>
                </div>
                <div class="grid grid-cols-2 mt-16">
                    <div class="relative border-s-2 border-s-gray-250 ps-4 py-8">
                        <h3 class="text-esmerald text-4xl font-regular">Mail Us</h3>
                        <p class="mt-4 text-green-light text-lg font-regular">Tell us about your vision to get started.</p>
                        <a @click="showModalEmail = true" ref="emailLink" @mouseover="animateLink" @mouseleave="resetLink" class="inline-block text-xl absolute bottom-0 text-esmerald cursor-pointer">
                        hello@projectapp.co
                        <span ref="underline" class="absolute left-0 bottom-0 h-0.5 w-0 bg-black transition-all duration-300"></span>
                        <span ref="arrow" class="absolute right-0 top-1/2 transform -translate-y-1/2 opacity-0 transition-opacity duration-300">➜</span>
                        </a>
                    </div>
                    <div class="relative border-s-2 border-s-gray-250 ps-4 py-8">
                        <h3 class="text-esmerald text-4xl font-regular">Direct Contact</h3>
                        <p class="mt-4 text-green-light text-lg font-regular">Let’s discuss your needs in detail. Speak soon!</p>
                        <a href="https://wa.me/message/XX77FJEUEM26H1?src=qr" target="_blank" ref="chatLink" @mouseover="animateLinkChat" @mouseleave="resetLinkChat" class="inline-block text-xl absolute bottom-0 text-esmerald cursor-pointer">
                        Chat
                        <span ref="underlineChat" class="absolute left-0 bottom-0 h-0.5 w-0 bg-black transition-all duration-300"></span>
                        <span ref="arrowChat" class="absolute right-0 top-1/2 transform -translate-y-1/2 opacity-0 transition-opacity duration-300">➜</span>
                        </a>
                    </div>
                </div>
            </div>
        </section>
        <Email :visible="showModalEmail" @update:visible="showModalEmail = $event"></Email>
</template>

<script setup>
import { ref } from 'vue';
import { gsap } from 'gsap';
import Email from '@/components/Layouts/Email.vue';

const showModalEmail = ref(false);

const emailLink = ref(null);
const chatLink = ref(null);
const underline = ref(null);
const arrow = ref(null);
const underlineChat = ref(null);
const arrowChat = ref(null);

const animateLink = () => {
  gsap.to(underline.value, { width: '100%', duration: 0.05 });
  gsap.to(arrow.value, { opacity: 1, x: 30, duration: 0.05 });
};

const resetLink = () => {
  gsap.to(underline.value, { width: '0%', duration: 0.05 });
  gsap.to(arrow.value, { opacity: 0, x: 20, duration: 0.05 });
};

const animateLinkChat = () => {
  gsap.to(underlineChat.value, { width: '100%', duration: 0.05 });
  gsap.to(arrowChat.value, { opacity: 1, x: 30, duration: 0.05 });
};

const resetLinkChat = () => {
  gsap.to(underlineChat.value, { width: '0%', duration: 0.05 });
  gsap.to(arrowChat.value, { opacity: 0, x: 20, duration: 0.05 });
};
</script>