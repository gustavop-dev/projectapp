<template>
    <div>
        <div class="fixed top-0 left-0 w-full z-50">
            <Navbar></Navbar>
        </div>
        <section class="h-screen relative">
            <div class="absolute z-20 w-1/3 px-3 h-full flex items-center md:px-16">
                <h1 class="text-white font-light text-6xl md:text-8xl">Innovation and Efficiency with Custom Software</h1>
            </div>
            <Dune spline="/spline/Backgrounds/particles.splinecode"></Dune>
        </section>
        <section class="bg-black grid md:grid-cols-2 lg:pt-52">
            <div class="pb-32">
                <h2 class="px-3 max-w-7xl text-white text-6xl font-light">ERP Systems</h2>
                <p class="px-3 mt-20 text-white text-lg font-regular">Streamline your operations, improve efficiency, and enhance decision-making with our robust ERP solutions. We build systems that integrate seamlessly with your existing processes.</p>
                <p class="px-3 mt-8 text-white text-lg font-regular">Our ERP systems are designed to integrate all facets of your business operations, from finance and human resources to supply chain and manufacturing. By automating and optimizing your processes, our ERP solutions help reduce operational costs, improve productivity, and provide real-time insights for better decision-making. Customizable and scalable, our ERP systems grow with your business, ensuring you always have the tools you need to succeed.</p>
            </div>
            <div class="flex items-center justify-center">
                <img class="h-full w-full object-cover rounded-xl" src="@/assets/images/lightningBulb.webp" alt="Light Bulb 3D">
            </div>
        </section>
        <section class="bg-black grid md:grid-cols-2 lg:pt-52">
            <div class="flex items-center justify-center order-2 md:order-1 h-80 md:h-auto">
                <Dune spline="/spline/Backgrounds/bubleBlue.splinecode"></Dune>
            </div>
            <div class="pb-32 order-1 md:order-2">
                <h2 class="px-3 max-w-7xl text-white text-6xl font-light">CRM Solutions</h2>
                <p class="px-3 mt-20 text-white text-lg font-regular">Enhance customer relationships, drive sales, and improve customer service with our custom CRM software. Our solutions are designed to help you manage and analyze customer interactions effectively.</p>
                <p class="px-3 mt-8 text-white text-lg font-regular">Our custom CRM solutions enable you to build stronger relationships with your customers. With features like contact management, sales automation, and customer service tracking, our CRM systems help you stay connected with your customers and streamline your sales processes. By providing detailed analytics and reporting, our CRM software empowers you to understand customer behavior and preferences, allowing you to tailor your services and marketing strategies to meet their needs better.</p>
            </div>
        </section>
        <section class="bg-black pt-32 grid md:grid-cols-2 lg:pt-52">
            <div class="pb-32">
                <h2 class="px-3 max-w-7xl text-white text-6xl font-light">Tailored Business Solutions</h2>
                <p class="px-3 mt-20 text-white text-lg font-regular">Whether you need inventory management, human resources software, or any other specialized application, our team is equipped to deliver software that fits your specific requirements.</p>
                <p class="px-3 mt-8 text-white text-lg font-regular">We understand that every business has unique needs, which is why we offer tailored software solutions for various business functions. Whether you need an inventory management system to track stock levels and streamline order processing, human resources software to manage employee records and payroll, or any other specialized application, we have the expertise to deliver solutions that fit your specific requirements. Our tailored business solutions are designed to enhance efficiency, reduce manual workload, and provide you with the tools needed to manage your operations effectively.</p>
            </div>
            <div class="flex items-center justify-center h-80 md:h-auto">
                <Dune spline="/spline/Backgrounds/bubles.splinecode"></Dune>
            </div>
        </section>
        <section class="p-3 bg-black">
            <div class="border-t-2 border-t-gray-250 grid lg:h-80 lg:grid-cols-2">
                <div class="ps-8 mt-16">
                    <h2 class="text-white text-4xl font-regular">Connect with us today.<br>Start your project in minutes.<br>Experience excellence forever.</h2>
                </div>
                <div class="grid mt-16 lg:grid-cols-2">
                    <div class="relative border-s-2 border-s-gray-250 ps-4 py-8">
                        <h3 class="text-white text-4xl font-regular">Mail Us</h3>
                        <p class="mt-4 text-green-light text-lg font-regular">Tell us about your vision to get started.</p>
                        <a @click="showModalEmail = true" ref="emailLink" @mouseover="animateLink" @mouseleave="resetLink" class="inline-block text-xl absolute bottom-0 text-white cursor-pointer">
                        hello@projectapp.co
                        <span ref="underline" class="absolute left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300"></span>
                        <span ref="arrow" class="absolute right-0 top-1/2 transform -translate-y-1/2 opacity-0 transition-opacity duration-300">➜</span>
                        </a>
                    </div>
                    <div class="relative border-s-2 border-s-gray-250 ps-4 py-8">
                        <h3 class="text-white text-4xl font-regular">Direct Contact</h3>
                        <p class="mt-4 text-green-light text-lg font-regular">Let’s discuss your needs in detail. Speak soon!</p>
                        <a href="https://wa.me/message/XX77FJEUEM26H1?src=qr" target="_blank" ref="chatLink" @mouseover="animateLinkChat" @mouseleave="resetLinkChat" class="inline-block text-xl absolute bottom-0 text-white cursor-pointer">
                        Chat
                        <span ref="underlineChat" class="absolute left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300"></span>
                        <span ref="arrowChat" class="absolute right-0 top-1/2 transform -translate-y-1/2 opacity-0 transition-opacity duration-300">➜</span>
                        </a>
                    </div>
                </div>
            </div>
        </section>
        <div class="pt-32 bg-black">
            <Footer></Footer>
        </div>
    </div>
    <Email :visible="showModalEmail" @update:visible="showModalEmail = $event"></Email>
</template>

<script setup>
import Navbar from '@/components/layouts/Navbar.vue';
import Footer from '@/components/layouts/Footer.vue';
import Dune from '@/components/spline/Backgrounds/Dune.vue';
import Email from '@/components/layouts/Email.vue';
import { ref } from 'vue';
import { gsap } from 'gsap';

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