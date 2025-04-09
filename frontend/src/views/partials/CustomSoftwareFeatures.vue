<template>
    <div>
        <section class="bg-dark grid md:grid-cols-2 lg:pt-52">
            <div class="flex items-center justify-center order-2 md:order-1 h-80 md:h-auto">
                <video ref="eCommerceVideo" autoplay muted loop playsinline preload="metadata">
                    <source src="@/assets/videos/customSoftware/holo-blobs.mp4" type="video/mp4" />
                    Your browser does not support the video tag.
                </video>
            </div>
            <div class="pb-32 order-1 md:order-2">
                <h2 class="px-3 max-w-7xl text-white text-6xl font-light">{{ messages.eCommerce_section.title }}</h2>
                <p class="px-3 mt-20 text-white text-lg font-regular">{{ messages.eCommerce_section.paragraph_1 }}</p>
                <p class="px-3 mt-8 text-white text-lg font-regular">{{ messages.eCommerce_section.paragraph_2 }}</p>
            </div>
        </section>
        <section class="bg-dark grid md:grid-cols-2 lg:pt-52">
            <div class="pb-32">
                <h2 class="px-3 max-w-7xl text-white text-6xl font-light">{{ messages.erp_section.title }}</h2>
                <p class="px-3 mt-20 text-white text-lg font-regular">{{ messages.erp_section.paragraph_1 }}</p>
                <p class="px-3 mt-8 text-white text-lg font-regular">{{ messages.erp_section.paragraph_2 }}</p>
            </div>
            <div class="flex items-center justify-center">
                <video ref="erpVideo" autoplay muted loop playsinline preload="metadata">
                    <source src="@/assets/videos/customSoftware/trails.mp4" type="video/mp4" />
                    Your browser does not support the video tag.
                </video>
            </div>
        </section>
        <section class="bg-dark grid md:grid-cols-2 lg:pt-52">
            <div class="flex items-center justify-center order-2 md:order-1 h-80 md:h-auto">
                <video ref="crmVideo" autoplay muted loop playsinline preload="metadata">
                    <source src="@/assets/videos/customSoftware/meeet.mp4" type="video/mp4" />
                    Your browser does not support the video tag.
                </video>
            </div>
            <div class="pb-32 order-1 md:order-2">
                <h2 class="px-3 max-w-7xl text-white text-6xl font-light">{{ messages.crm_section.title }}</h2>
                <p class="px-3 mt-20 text-white text-lg font-regular">{{ messages.crm_section.paragraph_1 }}</p>
                <p class="px-3 mt-8 text-white text-lg font-regular">{{ messages.crm_section.paragraph_2 }}</p>
            </div>
        </section>
        <section class="bg-dark pt-32 grid md:grid-cols-2 lg:pt-52">
            <div class="pb-32">
                <h2 class="px-3 max-w-7xl text-white text-6xl font-light">{{ messages.tailored_solutions_section.title }}</h2>
                <p class="px-3 mt-20 text-white text-lg font-regular">{{ messages.tailored_solutions_section.paragraph_1 }}</p>
                <p class="px-3 mt-8 text-white text-lg font-regular">{{ messages.tailored_solutions_section.paragraph_2 }}</p>
            </div>
            <div class="flex items-center justify-center h-80 md:h-auto">
                <video ref="tailoredSolutionsVideo" autoplay muted loop playsinline preload="metadata">
                    <source src="@/assets/videos/customSoftware/infinityBlubs.mp4" type="video/mp4" />
                    Your browser does not support the video tag.
                </video>
            </div>
        </section>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

// Definir props
const props = defineProps({
    messages: {
        type: Object,
        required: true
    }
});

// Emit eventos
const emit = defineEmits(['setup-videos']);

// Referencias para videos
const eCommerceVideo = ref(null);
const erpVideo = ref(null);
const crmVideo = ref(null);
const tailoredSolutionsVideo = ref(null);

// Configurar observador de intersección para reproducir videos solo cuando son visibles
onMounted(() => {
    // Enviar referencias al componente padre
    emit('setup-videos', {
        eCommerceVideo: eCommerceVideo.value,
        erpVideo: erpVideo.value,
        crmVideo: crmVideo.value,
        tailoredSolutionsVideo: tailoredSolutionsVideo.value
    });

    // Configurar observador de intersección
    const options = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const videoElements = [
        eCommerceVideo.value,
        erpVideo.value,
        crmVideo.value,
        tailoredSolutionsVideo.value
    ];

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            // Solo reproducir el video cuando es visible
            if (entry.isIntersecting) {
                entry.target.play();
            } else {
                entry.target.pause();
            }
        });
    }, options);

    // Observar cada video
    videoElements.forEach(video => {
        if (video) {
            observer.observe(video);
        }
    });
});
</script>

<style scoped>
/* Optimizaciones de rendimiento */
section {
    contain: content;
    content-visibility: auto;
    contain-intrinsic-size: 0 600px;
}

video {
    will-change: transform;
    max-width: 100%;
    height: auto;
}
</style> 