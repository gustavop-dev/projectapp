<template>
    <div>
        <div class="fixed top-0 left-0 w-full z-50">
            <Navbar></Navbar>
        </div>
        <section>
            <div class="p-3 h-screen">
                <div class="w-full h-full grid grid-cols-2 rounded-xl overflow-hidden">
                    <div class="flex items-center bg-lemon px-16">
                        <h1><span class="text-6xl font-light text-esmerald">We prepare more than 500 web components only for You!</span><br><span class="text-md font-medium text-esmerald">Did you know that we do all our developments with Tailwind CSS, the best framework for styles in web development.</span></h1>
                    </div>
                    <div>
                        <Dune spline="/spline/Backgrounds/dune.splinecode"></Dune>
                    </div>
                </div>
            </div>
        </section>
        <section class="mt-52">
            <div v-for="development in developments" :key="development.id" class="container mx-auto sm:px-6 lg:px-8">
                <h1 class="text-6xl font-light text-esmerald">{{ development.title_en }}</h1>
                <h2 class="text-4xl font-light text-esmerald mt-20">{{ development.description_en }}</h2>
                <div v-for="section in development.sections" :key="section.id" class="mt-40 grid grid-cols-4">
                    <div class="col-span-1">
                        <h2 class="font-light text-esmerald text-lg">{{ section.title_en }}</h2>
                    </div>
                    <div class="col-span-3 grid grid-cols-3 gap-8">
                        <div v-for="component in section.components" :key="component.id" @click="goToDetail(development.id, section.id, component.id)" class="cursor-pointer">
                            <div class="border border-gray-200 rounded-lg">
                                <img :src="component.image_url" :alt="component.id">
                            </div>
                            <h3 class="mt-4 font-regular text-esmerald text-md">{{ component.title_en }}</h3>
                            <p class="mt-2 bg-esmerald-light px-6 py-2 inline-block rounded-3xl text-esmerald text-sm">{{ component.examples.length }} components</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        <div class="mt-52">
            <Footer></Footer>
        </div>
    </div>
</template>
<script setup>
import { useWebDevelopmentsStore } from '@/stores/web-developments';
import Navbar from '@/components/Layouts/Navbar.vue';
import Dune from '@/components/spline/Backgrounds/Dune.vue';
import Footer from '@/components/Layouts/Footer.vue';
import { useRouter } from 'vue-router';
import { ref, onMounted } from 'vue';

const developmentsStore = useWebDevelopmentsStore();
const developments = ref([]);
const router = useRouter();

const goToDetail = (developmentId, sectionId, componentId) => {
  router.push({
    name: 'webDevelopmentsDetail',
    params: {
      development_id: developmentId,
      section_id: sectionId,
      component_id: componentId
    }
  });
};

onMounted(async () => {
  await developmentsStore.init();
  developments.value = developmentsStore.getDevelopments;
});
</script>