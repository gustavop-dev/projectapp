<template>
    <div class="bg-dark" itemscope itemtype="https://schema.org/WebPage">
        <div class="fixed top-0 left-0 w-full z-50">
            <Navbar theme="dark"></Navbar>
        </div>
        <main>
            <section class="h-svh relative" aria-labelledby="hero-title" itemscope itemtype="https://schema.org/WPHeader">
                <div class="absolute z-20 w-1/3 px-3 h-full flex items-center md:px-16">
                    <h1 id="hero-title" class="text-white font-light text-6xl md:text-8xl" itemprop="headline">
                        {{ messages.hero_section.title }}
                        <span class="sr-only">by Project App. - Soluciones de software personalizadas</span>
                    </h1>
                </div>
                <div class="relative w-full h-svh overflow-hidden">
                    <video
                        ref="heroVideo"
                        autoplay
                        muted
                        loop
                        playsinline
                        class="absolute inset-0 w-auto h-full object-cover"
                        preload="metadata"
                        fetchpriority="high"
                        aria-label="Video de software personalizado"
                    >
                        <source src="@/assets/videos/customSoftware/chips.mp4" type="video/mp4" />
                        <span class="sr-only">Animación de tecnología de software personalizado de Project App.</span>
                    </video>
                </div>
                <meta itemprop="keywords" content="desarrollo de software personalizado, soluciones de comercio electrónico, sistemas ERP, software CRM, software a medida, Project App.">
            </section>
            
            <section class="bg-dark grid md:grid-cols-2 lg:pt-52" aria-labelledby="ecommerce-title" itemscope itemtype="https://schema.org/Service">
                <div class="flex items-center justify-center order-2 md:order-1 h-80 md:h-auto">
                    <video ref="crmVideo" autoplay muted loop playsinline preload="metadata" loading="lazy" aria-label="Video de soluciones de comercio electrónico">
                        <source src="@/assets/videos/customSoftware/holo-blobs.mp4" type="video/mp4" />
                        <span class="sr-only">Representación visual de las soluciones de comercio electrónico de Project App.</span>
                    </video>
                </div>
                <div class="pb-32 order-1 md:order-2">
                    <h2 id="ecommerce-title" class="px-3 max-w-7xl text-white text-6xl font-light" itemprop="name">
                        {{ messages.eCommerce_section.title }}
                        <span class="sr-only">de Project App.</span>
                    </h2>
                    <p class="px-3 mt-20 text-white text-lg font-regular" itemprop="description">
                        {{ messages.eCommerce_section.paragraph_1 }}
                        <span class="sr-only">desarrolladas por Project App.</span>
                    </p>
                    <p class="px-3 mt-8 text-white text-lg font-regular" itemprop="description">
                        {{ messages.eCommerce_section.paragraph_2 }}
                        <span class="sr-only">por Project App.</span>
                    </p>
                </div>
                <meta itemprop="category" content="E-commerce Software">
                <meta itemprop="provider" content="Project App.">
            </section>
            
            <section class="bg-dark grid md:grid-cols-2 lg:pt-52" aria-labelledby="erp-title" itemscope itemtype="https://schema.org/Service">
                <div class="pb-32">
                    <h2 id="erp-title" class="px-3 max-w-7xl text-white text-6xl font-light" itemprop="name">
                        {{ messages.erp_section.title }}
                        <span class="sr-only">de Project App.</span>
                    </h2>
                    <p class="px-3 mt-20 text-white text-lg font-regular" itemprop="description">
                        {{ messages.erp_section.paragraph_1 }}
                        <span class="sr-only">desarrollados por Project App.</span>
                    </p>
                    <p class="px-3 mt-8 text-white text-lg font-regular" itemprop="description">
                        {{ messages.erp_section.paragraph_2 }}
                        <span class="sr-only">diseñados por Project App.</span>
                    </p>
                </div>
                <div class="flex items-center justify-center">
                    <video ref="erpVideo" autoplay muted loop playsinline preload="metadata" loading="lazy" aria-label="Video de sistemas ERP">
                        <source src="@/assets/videos/customSoftware/trails.mp4" type="video/mp4" />
                        <span class="sr-only">Representación visual de los sistemas ERP avanzados de Project App.</span>
                    </video>
                </div>
                <meta itemprop="category" content="ERP Systems">
                <meta itemprop="provider" content="Project App.">
            </section>
            
            <section class="bg-dark grid md:grid-cols-2 lg:pt-52" aria-labelledby="crm-title" itemscope itemtype="https://schema.org/Service">
                <div class="flex items-center justify-center order-2 md:order-1 h-80 md:h-auto">
                    <video ref="crmVideo" autoplay muted loop playsinline preload="metadata" loading="lazy" aria-label="Video de soluciones CRM">
                        <source src="@/assets/videos/customSoftware/meeet.mp4" type="video/mp4" />
                        <span class="sr-only">Representación visual de las soluciones CRM personalizadas de Project App.</span>
                    </video>
                </div>
                <div class="pb-32 order-1 md:order-2">
                    <h2 id="crm-title" class="px-3 max-w-7xl text-white text-6xl font-light" itemprop="name">
                        {{ messages.crm_section.title }}
                        <span class="sr-only">de Project App.</span>
                    </h2>
                    <p class="px-3 mt-20 text-white text-lg font-regular" itemprop="description">
                        {{ messages.crm_section.paragraph_1 }}
                        <span class="sr-only">desarrolladas por Project App.</span>
                    </p>
                    <p class="px-3 mt-8 text-white text-lg font-regular" itemprop="description">
                        {{ messages.crm_section.paragraph_2 }}
                        <span class="sr-only">creadas por Project App.</span>
                    </p>
                </div>
                <meta itemprop="category" content="CRM Software">
                <meta itemprop="provider" content="Project App.">
            </section>
            
            <section class="bg-dark pt-32 grid md:grid-cols-2 lg:pt-52" aria-labelledby="custom-solutions-title" itemscope itemtype="https://schema.org/Service">
                <div class="pb-32">
                    <h2 id="custom-solutions-title" class="px-3 max-w-7xl text-white text-6xl font-light" itemprop="name">
                        {{ messages.tailored_solutions_section.title }}
                        <span class="sr-only">de Project App.</span>
                    </h2>
                    <p class="px-3 mt-20 text-white text-lg font-regular" itemprop="description">
                        {{ messages.tailored_solutions_section.paragraph_1 }}
                        <span class="sr-only">desarrolladas por Project App.</span>
                    </p>
                    <p class="px-3 mt-8 text-white text-lg font-regular" itemprop="description">
                        {{ messages.tailored_solutions_section.paragraph_2 }}
                        <span class="sr-only">por Project App.</span>
                    </p>
                </div>
                <div class="flex items-center justify-center h-80 md:h-auto">
                    <video ref="tailoredSolutionsVideo" autoplay muted loop playsinline preload="metadata" loading="lazy" aria-label="Video de soluciones empresariales a medida">
                        <source src="@/assets/videos/customSoftware/infinityBlubs.mp4" type="video/mp4" />
                        <span class="sr-only">Representación visual de las soluciones empresariales a medida desarrolladas por Project App.</span>
                    </video>
                </div>
                <meta itemprop="category" content="Custom Business Solutions">
                <meta itemprop="provider" content="Project App.">
            </section>
            
            <section class="p-3 bg-dark" aria-labelledby="contact-title" itemscope itemtype="https://schema.org/ContactPoint">
                <div class="border-t-2 border-t-gray-250 grid lg:h-80 lg:grid-cols-2">
                    <div class="ps-8 mt-16">
                        <h2 id="contact-title" class="text-white text-4xl font-regular" itemprop="name">
                            {{ messages.contact_section.title }}
                            <span class="sr-only">con Project App.</span>
                        </h2>
                    </div>
                    <div class="grid mt-16 lg:grid-cols-2">
                        <div class="relative border-s-2 border-s-gray-250 ps-4 py-8">
                            <h3 class="text-white text-4xl font-regular" itemprop="contactType">
                                {{ messages.contact_section.mail_title }}
                                <span class="sr-only">a Project App.</span>
                            </h3>
                            <p class="mt-4 text-green-light text-lg font-regular" itemprop="description">
                                {{ messages.contact_section.mail_description }}
                                <span class="sr-only">con Project App.</span>
                            </p>
                            <a @click="showModalEmail = true" ref="emailLink" @mouseover="animateLink" @mouseleave="resetLink" class="inline-block text-xl absolute bottom-0 text-white cursor-pointer" itemprop="email">
                            hello@projectapp.co
                            <span ref="underline" class="absolute left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300"></span>
                            <span ref="arrow" class="absolute right-0 top-1/2 transform -translate-y-1/2 opacity-0 transition-opacity duration-300">➜</span>
                            <span class="sr-only">Contactar a Project App. por correo electrónico para soluciones de software personalizadas</span>
                            </a>
                        </div>
                        <div class="relative border-s-2 border-s-gray-250 ps-4 py-8">
                            <h3 class="text-white text-4xl font-regular" itemprop="contactType">
                                {{ messages.contact_section.direct_contact_title }}
                                <span class="sr-only">con Project App.</span>
                            </h3>
                            <p class="mt-4 text-green-light text-lg font-regular" itemprop="description">
                                {{ messages.contact_section.direct_contact_description }}
                                <span class="sr-only">por Project App.</span>
                            </p>
                            <a href="https://wa.me/message/XX77FJEUEM26H1?src=qr" target="_blank" ref="chatLink" @mouseover="animateLinkChat" @mouseleave="resetLinkChat" class="inline-block text-xl absolute bottom-0 text-white cursor-pointer" itemprop="url">
                            Chat
                            <span ref="underlineChat" class="absolute left-0 bottom-0 h-0.5 w-0 bg-white transition-all duration-300"></span>
                            <span ref="arrowChat" class="absolute right-0 top-1/2 transform -translate-y-1/2 opacity-0 transition-opacity duration-300">➜</span>
                            <span class="sr-only">Contactar con Project App. por WhatsApp para consultas sobre desarrollo de software personalizado</span>
                            </a>
                        </div>
                    </div>
                </div>
            </section>
        </main>
        
        <footer class="pt-32 bg-dark" itemscope itemtype="https://schema.org/WPFooter">
            <Footer></Footer>
        </footer>
    </div>
    <Email :visible="showModalEmail" @update:visible="showModalEmail = $event"></Email>
</template>

<script setup>
import Navbar from '@/components/layouts/Navbar.vue'; // Import the Navbar component for the navigation bar
import Footer from '@/components/layouts/Footer.vue'; // Import the Footer component for the website's footer
import Email from '@/components/layouts/Email.vue'; // Import the Email component for email-related functionality
import { ref, onMounted, onBeforeUnmount } from 'vue'; // Import ref for reactive state management
import { gsap } from 'gsap'; // Import GSAP (GreenSock Animation Platform) for animations
import { useMessages } from '@/composables/useMessages'; // Import the custom composable for localized messages
import { useFreeResources } from '@/composables/useFreeResources'; // Import the free resources composable

const { messages } = useMessages(); // Destructure the localized messages from the custom composable

// Reactive state to control the visibility of the email modal
const showModalEmail = ref(false);

// Refs for DOM elements to be animated
const emailLink = ref(null);
const chatLink = ref(null);
const underline = ref(null);
const arrow = ref(null);
const underlineChat = ref(null);
const arrowChat = ref(null);

// Refs for video elements
const heroVideo = ref(null);
const erpVideo = ref(null);
const crmVideo = ref(null);
const tailoredSolutionsVideo = ref(null);

// Animation functions using GSAP

/**
 * Animates the email link by expanding the underline and making the arrow visible.
 */
const animateLink = () => {
  gsap.to(underline.value, { width: '100%', duration: 0.05 });
  gsap.to(arrow.value, { opacity: 1, x: 30, duration: 0.05 });
};

/**
 * Resets the email link animation by collapsing the underline and hiding the arrow.
 */
const resetLink = () => {
  gsap.to(underline.value, { width: '0%', duration: 0.05 });
  gsap.to(arrow.value, { opacity: 0, x: 20, duration: 0.05 });
};

/**
 * Animates the chat link by expanding the underline and making the arrow visible.
 */
const animateLinkChat = () => {
  gsap.to(underlineChat.value, { width: '100%', duration: 0.05 });
  gsap.to(arrowChat.value, { opacity: 1, x: 30, duration: 0.05 });
};

/**
 * Resets the chat link animation by collapsing the underline and hiding the arrow.
 */
const resetLinkChat = () => {
  gsap.to(underlineChat.value, { width: '0%', duration: 0.05 });
  gsap.to(arrowChat.value, { opacity: 0, x: 20, duration: 0.05 });
};

// Video management - Intersection Observer for video playback
const setupVideoObservers = () => {
  if (!window.IntersectionObserver) return;
  
  const options = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      const video = entry.target;
      if (entry.isIntersecting) {
        if (video.paused) video.play();
      } else {
        if (!video.paused) video.pause();
      }
    });
  }, options);
  
  // Observe all videos except hero video which should always play
  if (erpVideo.value) observer.observe(erpVideo.value);
  if (crmVideo.value) observer.observe(crmVideo.value);
  if (tailoredSolutionsVideo.value) observer.observe(tailoredSolutionsVideo.value);
};

onMounted(() => {
  // Establecer observadores de intersección para videos
  setupVideoObservers();
  
  // Establecer tiempo de inicio de video principal con un ligero retraso para mejorar FCP
  setTimeout(() => {
    if (heroVideo.value && heroVideo.value.paused) {
      heroVideo.value.play().catch(() => {
        console.warn('Autoplay was prevented for hero video.');
      });
    }
  }, 100);
});

// Cleanup event listeners on unmount
onBeforeUnmount(() => {
  // Liberar recursos de video cuando el componente se desmonta
  const videos = [heroVideo.value, erpVideo.value, crmVideo.value, tailoredSolutionsVideo.value];
  videos.forEach(video => {
    if (video) {
      video.pause();
      video.src = '';
      video.load();
    }
  });
});

// Use free resources to manage video resources
useFreeResources({
  videos: [heroVideo, erpVideo, crmVideo, tailoredSolutionsVideo]
});
</script>
