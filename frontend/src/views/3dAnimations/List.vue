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
              <span class="text-4xl font-light text-white lg:text-6xl">{{ messages.intro_section.title_line1 }}</span><br>
              <span class="text-4xl font-light text-white lg:text-6xl">{{ messages.intro_section.title_line2 }}</span><br>
              <span class="text-md font-medium text-white">{{ messages.intro_section.subtitle_line1 }}</span><br>
              <span class="text-md font-medium text-white">{{ messages.intro_section.subtitle_line2 }}</span>
            </h1>
          </div>
          <div class="order-1">
            <div class="relative w-full h-screen overflow-hidden">
              <img
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
            v-for="model3d in models3dFiltered"
            :key="model3d.id"
            @click="openModal(model3d.file)"
            class="cursor-pointer"
          >
            <div class="border border-gray-200 rounded-lg">
              <img class="w-full rounded-lg" :src="model3d.image" :alt="model3d.title">
            </div>
            <h3 class="mt-4 font-regular text-esmerald text-md">{{ model3d.title }}</h3>
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
import { ref, onMounted } from 'vue'; // Import Vue utilities
import Navbar from '@/components/layouts/Navbar.vue'; // Import the Navbar component
import Footer from '@/components/layouts/Footer.vue'; // Import the Footer component
import Detail from '@/views/3dAnimations/Detail.vue'; // Import the Detail view for 3D animations
import { useModels3dStore } from '@/stores/models_3d'; // Import the models 3D store
import { useMessages } from '@/composables/useMessages'; // Import the custom composable for localized messages

const { messages } = useMessages(); // Destructure the localized messages from the custom composable

// Store para gestionar los datos de los modelos 3D
const models3dStore = useModels3dStore();
const models3d = ref([]); // Lista completa de modelos 3D
const models3dFiltered = ref([]); // Lista filtrada de modelos 3D por categoría
const categories = ref([]); // Lista de categorías de modelos 3D
const selectedCategory = ref("All"); // 'All' seleccionado por defecto

const isModalVisible = ref(false); // Estado para controlar la visibilidad del modal
const currentSplineUrl = ref(''); // Estado para almacenar la URL de la escena actual de Spline

// Abre el modal para mostrar un modelo 3D de Spline
const openModal = (splineUrl) => {
  currentSplineUrl.value = splineUrl;
  isModalVisible.value = true;
};

// Método para obtener los modelos 3D filtrados basados en la categoría seleccionada
const getFilteredModels = (category) => {
  selectedCategory.value = category;
  models3dFiltered.value = models3dStore.getFilteredByCategory(models3d.value, selectedCategory.value);
};

// Hook que se ejecuta después de que el componente se monta
onMounted(async () => {
  await models3dStore.init(); // Inicializar el store de modelos 3D

  // Desestructurar el objeto devuelto para obtener los modelos y las categorías
  const { models: fetchedModels, categories: fetchedCategories } =
    models3dStore.getFilteredModelsAndCategories;

  // Asignar los valores obtenidos a las variables reactivas
  models3d.value = fetchedModels;
  models3dFiltered.value = fetchedModels;
  categories.value = fetchedCategories;
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
