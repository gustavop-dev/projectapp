<template>
    <div>
      <div class="fixed top-0 left-0 w-full z-50">
        <Navbar></Navbar>
      </div>
      <section>
        <div class="h-screen p-3">
          <div class="w-full h-full grid grid-cols-2 rounded-xl overflow-hidden">
            <div class="bg-pink flex items-center px-16">
              <h1 class=""><span class="text-6xl font-light text-white">All our inspiration for you, we are the artisans of the code.</span><br><span class="text-md font-medium text-white">Did you know that we make all our designs unique with Figma, Adobe Photoshop, Adobe Illustrator and a lot of love.</span></h1>
            </div>
            <div>
              <Dune spline="/spline/Backgrounds/webDesign.splinecode"></Dune>
            </div>
          </div>
        </div>
      </section>
      <section>
        <div class="mt-52 container mx-auto sm:px-6 lg:px-8">
          <h1 class="text-6xl font-light text-esmerald">Web Designs</h1>
          <h2 class="text-4xl font-light text-esmerald mt-20">We've turned ideas into reality, crafting unique web designs with passion and dedication.</h2>
          <div class="mt-40 grid grid-cols-4">
            <div v-for="design in designs" :key="design.id" @click="openModal(design.detail_image_url)" class="cursor-pointer">
              <div class="border border-gray-200 rounded-lg">
                <img class="w-full rounded-lg" :src="design.presentation_image_url" :alt="design.title_en">
              </div>
              <h3 class="mt-4 font-regular text-esmerald text-md">{{ design.title_en }}</h3>
            </div>
          </div>
        </div>
      </section>
      <div class="mt-52">
        <Footer></Footer>
      </div>
      <Detail :visible="isModalVisible" :detailImageUrl="currentDetailImageUrl" @update:visible="isModalVisible = $event" />
    </div>
  </template>
  
  <script setup>
  import Navbar from '@/components/Layouts/Navbar.vue';
  import Dune from '@/components/spline/Backgrounds/Dune.vue';
  import Footer from '@/components/Layouts/Footer.vue';
  import Detail from '@/views/WebDesigns/Detail.vue';
  import { useWebDesignsStore } from '@/stores/web-designs';
  import { onMounted, ref } from 'vue';
  
  const designsStore = useWebDesignsStore();
  const designs = ref([]);
  
  const isModalVisible = ref(false);
  const currentDetailImageUrl = ref('');
  
  const openModal = (detailImageUrl) => {
    currentDetailImageUrl.value = detailImageUrl;
    isModalVisible.value = true;
  };
  
  onMounted(async () => {
    await designsStore.init();
    designs.value = designsStore.designs;
  });
  </script>
  