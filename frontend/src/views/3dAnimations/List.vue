<template>
  <div>
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar></Navbar>
    </div>
    <section>
      <div class="h-svh p-3">
        <div class="relative w-full h-full grid rounded-xl overflow-hidden lg:grid-cols-2">
          <div class="absolute z-10 bottom-0 bg-transparent flex items-center px-16 order-2 py-24 xl:bg-brown xl:top-0 xl:relative xl:z-0">
            <h1>
              <span class="text-4xl font-light text-esmerald xl:text-white lg:text-6xl">{{ messages.intro_section.title_line1 }}</span><br>
              <span class="text-4xl font-light text-esmerald xl:text-white lg:text-6xl">{{ messages.intro_section.title_line2 }}</span><br>
              <span class="text-md font-medium text-esmerald xl:text-white">{{ messages.intro_section.subtitle_line1 }}</span><br>
              <span class="text-md font-medium text-esmerald xl:text-white">{{ messages.intro_section.subtitle_line2 }}</span>
            </h1>
          </div>
          <div class="order-1">
            <div class="relative w-full h-svh overflow-hidden">
              <img
                loading="lazy"
                src="@/assets/images/3dAnimations/mountainFaces.webp"
                alt="3d Animations view"
                class="absolute inset-0 w-auto h-full object-cover object-center"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
    <!-- Bloque de categorías y filtrado -->
    <section class="px-3">
      <div class="mt-32 max-w-7xl mx-auto sm:px-6 lg:px-8 lg:mt-52">
        <h1 class="text-6xl font-light text-esmerald">
          {{ messages.animations_section.section_title }}
        </h1>
        <h2 class="text-4xl font-light text-esmerald mt-20">
          {{ messages.animations_section.section_subtitle }}
        </h2>
        <!-- Categorías para el filtrado -->
        <div class="mt-24 flex flex-wrap justify-center items-center gap-3">
          <!-- Botón para 'All' categoría -->
          <button
            @click="getFilteredModels('All')"
            :class="
              selectedCategory === 'All' ? 'bg-lemon' : 'bg-esmerald-light'
            "
            class="px-6 py-2 inline-block rounded-3xl text-esmerald text-sm"
          >
            {{ messages.animations_section.all }}
          </button>

          <!-- Botones para otras categorías -->
          <button
            v-for="(category, index) in categories"
            :key="index"
            @click="getFilteredModels(category)"
            :class="
              selectedCategory === category ? 'bg-lemon' : 'bg-esmerald-light'
            "
            class="px-6 py-2 inline-block rounded-3xl text-esmerald text-sm"
          >
            {{ category }}
          </button>
        </div>

        <!-- Contenido de modelos 3D -->
        <div class="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4 lg:mt-24">
          <div
            v-for="model3d in models3dFiltered.slice().reverse().slice(0, visibleCount)"
            :key="model3d.id"
            @click="openModal(model3d.file)"
            class="cursor-pointer"
          >
            <div class="border border-gray-200 rounded-lg">
              <ImageLoader 
                :src="model3d.image"
                :alt="model3d.title"
              />
            </div>
            <h3 class="mt-4 font-regular text-esmerald text-md">{{ model3d.title }}</h3>
          </div>
        </div>
        <!-- Button for load more content -->
        <div v-if="visibleCount < models3dFiltered.length" class="text-center mt-8">
          <button @click="loadMore" class="px-6 py-2 font-regular text-md bg-lemon text-esmerlad rounded-full hover:bg-esmerald hover:text-esmerald-light">
            {{ messages.animations_section.see_more }}
          </button>
        </div>
      </div>
    </section>
    <div class="mt-52">
      <Footer></Footer>
    </div>
    <!-- Renderiza Detail solo si isModalVisible es true -->
    <Detail 
      v-if="isModalVisible" 
      :visible="isModalVisible" 
      :spline-url="currentSplineUrl" 
      @update:visible="closeModal" 
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import Navbar from '@/components/layouts/Navbar.vue';
import Footer from '@/components/layouts/Footer.vue';
import Detail from '@/views/3dAnimations/Detail.vue';
import ImageLoader from "@/components/layouts/ImageLoader.vue";
import { useModels3dStore } from '@/stores/models_3d';
import { useMessages } from '@/composables/useMessages';
import { useFreeResources } from '@/composables/useFreeResources';

const { messages } = useMessages();

const models3dStore = useModels3dStore();
const models3d = ref([]);
const models3dFiltered = ref([]);
const categories = ref([]);
const selectedCategory = ref("All");
const visibleCount = ref(16); // Number of pictures for showing

const isModalVisible = ref(false);
const currentSplineUrl = ref('');

// Método para abrir el modal y cargar la URL del modelo 3D
const openModal = (splineUrl) => {
  currentSplineUrl.value = splineUrl;
  isModalVisible.value = true;
};

// Método para cerrar el modal y limpiar la URL del modelo 3D
const closeModal = () => {
  isModalVisible.value = false;
  currentSplineUrl.value = ''; // Limpia la URL para liberar memoria
};

watch(isModalVisible, (newVal) => {
  if (newVal) {
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
  }
});

const getFilteredModels = (category) => {
  selectedCategory.value = category;
  models3dFiltered.value = models3dStore.getFilteredByCategory(models3d.value, selectedCategory.value);
};

onMounted(async () => {
  await models3dStore.init();
  const { models: fetchedModels, categories: fetchedCategories } =
    models3dStore.getFilteredModelsAndCategories;

  models3d.value = fetchedModels;
  models3dFiltered.value = fetchedModels;
  categories.value = fetchedCategories;
});

useFreeResources({
  images: models3dFiltered.value.map(model => ref(model.image))
});

// Use loadMore for increment the number of images for showing
const loadMore = () => {
  visibleCount.value += 16;
};
</script>