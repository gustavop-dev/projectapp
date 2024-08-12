<template>
    <div>
        <div class="fixed top-0 left-0 w-full z-50">
            <Navbar></Navbar>
        </div>
        <section class="h-52"></section>
        <section>
            <div class="px-4 sm:px-6 lg:px-8 xl:px-32">
                <div v-if="data">
                    <h2 class="text-lg font-regular text-esmerald">{{ data.development.title_en }} / {{ data.section.title_en }}</h2>
                    <h1 class="text-6xl font-light text-esmerald">{{ data.component.title_en }}</h1>
                    <div v-for="example in data.examples" class="mt-16 mb-16">
                        <h2 class="text-xl font-regular text-esmerald">{{ example.title_en }}</h2>
                        <div class="mt-4 flex justify-center">
                            <img :src="example.image">
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
import Navbar from '@/components/layouts/Navbar.vue';
import Footer from '@/components/layouts/Footer.vue';
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useWebDevelopmentsStore } from '@/stores/web-developments';

const route = useRoute();
const developmentsStore = useWebDevelopmentsStore();

const data = ref(null);

onMounted(async () => {
  await developmentsStore.init();
  const { development_id, section_id, component_id } = route.params;
  data.value = developmentsStore.getExamplesById(development_id, section_id, component_id);
});
</script>