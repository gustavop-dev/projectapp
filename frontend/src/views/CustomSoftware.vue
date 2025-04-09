<template>
    <div class="bg-dark">
        <div class="fixed top-0 left-0 w-full z-50">
            <Navbar theme="dark"></Navbar>
        </div>
        
        <!-- Hero Section -->
        <section class="h-svh relative">
            <div class="absolute z-20 w-1/3 px-3 h-full flex items-center md:px-16">
                <h1 class="text-white font-light text-6xl md:text-8xl">{{ messages.hero_section.title }}</h1>
            </div>
            <div class="relative w-full h-svh overflow-hidden">
                <video
                    ref="heroVideo"
                    autoplay
                    muted
                    loop
                    playsinline
                    preload="metadata"
                    class="absolute inset-0 w-auto h-full object-cover"
                >
                    <source src="@/assets/videos/customSoftware/chips.mp4" type="video/mp4" />
                    Your browser does not support the video tag.
                </video>
            </div>
        </section>
        
        <!-- Secciones de características cargadas de forma perezosa -->
        <Suspense>
            <template #default>
                <keep-alive>
                    <FeatureSections 
                        :messages="messages" 
                        @setup-videos="setupVideoRefs"
                    />
                </keep-alive>
            </template>
            <template #fallback>
                <div class="h-80 bg-dark flex items-center justify-center">
                    <div class="w-12 h-12 border-4 border-white rounded-full border-t-transparent animate-spin"></div>
                </div>
            </template>
        </Suspense>
        
        <!-- Contact section -->
        <section class="p-3 bg-dark">
            <div class="border-t-2 border-t-gray-250 grid lg:h-80 lg:grid-cols-2">
                <div class="ps-8 mt-16">
                    <h2 class="text-white text-4xl font-regular">{{ messages.contact_section.title }}</h2>
                </div>
                <div class="grid mt-16 lg:grid-cols-2">
                    <div class="relative border-s-2 border-s-gray-250 ps-4 py-8">
                        <h3 class="text-white text-4xl font-regular">{{ messages.contact_section.mail_title }}</h3>
                        <p class="mt-4 text-green-light text-lg font-regular">{{ messages.contact_section.mail_description }}</p>
                        <a 
                            @click.prevent="showModalEmail = true" 
                            href="#"
                            ref="emailLink" 
                            class="inline-block text-xl absolute bottom-0 text-white cursor-pointer hover-link"
                        >
                            hello@projectapp.co
                            <span class="link-underline"></span>
                            <span class="link-arrow">➜</span>
                        </a>
                    </div>
                    <div class="relative border-s-2 border-s-gray-250 ps-4 py-8">
                        <h3 class="text-white text-4xl font-regular">{{ messages.contact_section.direct_contact_title }}</h3>
                        <p class="mt-4 text-green-light text-lg font-regular">{{ messages.contact_section.direct_contact_description }}</p>
                        <a 
                            href="https://wa.me/message/XX77FJEUEM26H1?src=qr" 
                            target="_blank"
                            rel="noopener noreferrer" 
                            class="inline-block text-xl absolute bottom-0 text-white cursor-pointer hover-link"
                        >
                            Chat
                            <span class="link-underline"></span>
                            <span class="link-arrow">➜</span>
                        </a>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- Footer (cargado de forma perezosa) -->
        <div class="pt-32 bg-dark">
            <LazyFooter />
        </div>
    </div>
    
    <!-- Email modal -->
    <Email :visible="showModalEmail" @update:visible="showModalEmail = $event"></Email>
</template>

<script setup>
import { defineAsyncComponent, ref, shallowRef } from 'vue';
import Navbar from '@/components/layouts/Navbar.vue';
import Email from '@/components/layouts/Email.vue';
import { useMessages } from '@/composables/useMessages';
import { useFreeResources } from '@/composables/useFreeResources';

// Componentes cargados perezosamente
const LazyFooter = defineAsyncComponent(() => import('@/components/layouts/Footer.vue'));
const FeatureSections = defineAsyncComponent(() => import('./partials/CustomSoftwareFeatures.vue'));

const { messages } = useMessages();

// Estado reactivo para controlar la visibilidad del modal de email
const showModalEmail = ref(false);

// Referencias para videos
const heroVideo = ref(null);
const videoRefs = shallowRef({
    erpVideo: null,
    crmVideo: null,
    tailoredSolutionsVideo: null
});

// Configurar referencias de video desde el componente hijo
const setupVideoRefs = (refs) => {
    videoRefs.value = refs;
};

// Liberar recursos de video
useFreeResources({
    videos: [
        heroVideo, 
        () => videoRefs.value.erpVideo,
        () => videoRefs.value.crmVideo,
        () => videoRefs.value.tailoredSolutionsVideo
    ]
});
</script>

<style scoped>
/* Optimizaciones de rendimiento */
section {
    contain: content;
    content-visibility: auto;
    contain-intrinsic-size: 0 500px;
}

section:first-of-type {
    content-visibility: visible;
}

/* Estilos para los enlaces animados */
.hover-link {
    position: relative;
    padding-right: 2rem;
}

.link-underline {
    position: absolute;
    left: 0;
    bottom: 0;
    height: 2px;
    width: 0;
    background-color: white;
    transition: width 0.3s ease;
}

.link-arrow {
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    opacity: 0;
    transition: opacity 0.3s ease, transform 0.3s ease;
}

.hover-link:hover .link-underline {
    width: 100%;
}

.hover-link:hover .link-arrow {
    opacity: 1;
    transform: translateY(-50%) translateX(5px);
}
</style>

