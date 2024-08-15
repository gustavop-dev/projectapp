<template>
  <div>
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar></Navbar>
    </div>
    <section>
      <div class="h-screen p-3">
        <div class="w-full h-full grid rounded-xl overflow-hidden lg:grid-cols-2">
          <div class="bg-brown flex items-center px-16 order-2 py-24">
            <h1>
              <span class="text-4xl font-light text-white lg:text-6xl">Try touch it!<br>All our animations made and rendered in code with JavaScript!</span><br>
              <span class="text-md font-medium text-white">Did you know that these animations are being rendered in your browser and the most surprising thing is that one feather is heavier than each of them.</span>
            </h1>
          </div>
          <div class="order-1">
            <Dune spline="/spline/Backgrounds/cats.splinecode"></Dune>
          </div>
        </div>
      </div>
    </section>
    <section class="px-3">
      <div class="mt-32 max-w-7xl mx-auto sm:px-6 lg:px-8 lg:mt-52">
        <h1 class="text-4xl font-light text-esmerald lg:text-6xl">3D Animations</h1>
        <h2 class="text-2xl font-light text-esmerald mt-20 lg:text-4xl">Enjoy interactive and customized 3D animations, developed from scratch with JavaScript for a unique and immersive visual experience.</h2>
        <div class="mt-24 grid gap-4 md:grid-cols-2 lg:grid-cols-4 lg:mt-40">
          <div v-for="model3d in models3d" :key="model3d.id" @click="openModal(model3d.file_url)" class="cursor-pointer">
            <div class="border border-gray-200 rounded-lg">
              <img class="w-full rounded-lg" :src="model3d.image_url" :alt="model3d.title_en">
            </div>
            <h3 class="mt-4 font-regular text-esmerald text-md">{{ model3d.title_en }}</h3>
          </div>
        </div>
      </div>
    </section>
    <div class="mt-52">
      <Footer></Footer>
    </div>
    <Detail :visible="isModalVisible" :spline-url="currentSplineUrl" @update:visible="isModalVisible = $event"></Detail>
  </div>
</template>

<script setup>
import { ref, onMounted, defineAsyncComponent } from 'vue';
import Navbar from '@/components/layouts/Navbar.vue';
import Footer from '@/components/layouts/Footer.vue';
import Detail from '@/views/3dAnimations/Detail.vue';
import { useModels3dStore } from '@/stores/models-3d';


const Dune = defineAsyncComponent(() =>
  import('@/components/spline/Backgrounds/Dune.vue')
);

const models3dStore = useModels3dStore();
const models3d = ref([]);

const isModalVisible = ref(false);
const currentSplineUrl = ref('');

const openModal = (splineUrl) => {
  currentSplineUrl.value = splineUrl;
  isModalVisible.value = true;
};

onMounted(async () => {
  await models3dStore.init();
  models3d.value = models3dStore.models3d;
});
</script>

<style scoped>
.loader {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  font-size: 1.5em;
  color: #888;
}
</style>
