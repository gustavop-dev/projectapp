<template>
    <div>
      <div class="fixed top-0 left-0 w-full z-50">
        <Navbar></Navbar>
      </div>
      <section>
      <div class="p-3 h-svh">
        <div class="w-full h-full grid rounded-xl overflow-hidden lg:grid-cols-2">
          <div class="absolute z-10 bottom-0 flex items-center bg-transparent px-16 py-24 order-2 xl:bg-lemon xl:top-0 xl:relative xl:z-0">
            <h1>
              <span class="text-4xl font-light text-esmerald lg:text-6xl">{{ messages.header_title }}</span><br />
              <span class="text-md font-medium text-esmerald">{{ messages.header_subtitle }}</span>
            </h1>
          </div>
          <div class="order-1">
            <div class="relative w-full h-svh overflow-hidden">
              <video ref="backgroundVideo" autoplay muted loop playsinline class="absolute inset-0 w-auto h-full object-cover">
                <source src="@/assets/videos/webDevelopments/abstractGradientBackground.mp4" type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            </div>
          </div>
        </div>
      </div>
    </section>
      <section class="px-3">
        <div class="mt-32 max-w-7xl mx-auto sm:px-6 lg:mt-52 lg:px-8">
          <h1 class="text-6xl font-light text-esmerald">
            {{ messages.section_title }}
          </h1>
          <h2 class="text-4xl font-light text-esmerald mt-20">
            {{ messages.section_subtitle }}
          </h2>
          <p class="text-md font-light text-esmerald mt-6">
            *{{ messages.custom_software_notice }}
          </p>
          <p class="text-2md font-light text-esmerald mt-3">
            *{{ messages.dynamic_web_notice }}
          </p>
          <!-- Categories for filter -->
          <div 
            ref="categoriesSection"
            class="mt-24 font-regular flex flex-wrap justify-center items-center gap-3"
          >
            <!-- Button for 'All' category -->
            <button
              @click="getFilteredWorks('All')"
              :class="
                selectedCategory === 'All' ? 'bg-lemon' : 'bg-esmerald-light'
              "
              class="px-6 py-2 inline-block rounded-3xl text-esmerald text-sm"
            >
              {{ messages.all }}
            </button>
  
            <!-- Buttons for other categories -->
            <button
              v-for="(category, index) in categories"
              :key="index"
              @click="getFilteredWorks(category)"
              :class="
                selectedCategory === category ? 'bg-lemon' : 'bg-esmerald-light'
              "
              class="px-6 py-2 inline-block rounded-3xl text-esmerald text-sm"
            >
              {{ category }}
            </button>
          </div>
  
          <!-- Content by portfolio works -->
          <div class="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4 lg:mt-24">
            <div
              v-for="work in worksFiltered.slice().reverse().slice(0, visibleCount)"
              :key="work.id"
              @click="openWork(work.project_url)"
              class="cursor-pointer"
            >
              <div class="border border-gray-200 rounded-lg">
                <ImageLoader 
                  :src="work.cover_image"
                  :alt="work.title"
                />
              </div>
              <h3 class="mt-4 font-regular text-esmerald text-md">
                {{ work.title }}
              </h3>
            </div>
          </div>
          <!-- Button for load more content -->
          <div v-if="visibleCount < worksFiltered.length" class="text-center mt-8">
            <button @click="loadMore" class="px-6 py-2 font-regular text-md bg-lemon text-esmerlad rounded-full hover:bg-esmerald hover:text-esmerald-light">
              {{ messages.see_more }}
            </button>
          </div>
        </div>
      </section>
      <div class="mt-32 lg:mt-52">
        <Footer></Footer>
      </div>
    </div>
  </template>
  
  <script setup>
import Navbar from "@/components/layouts/Navbar.vue";
import ImageLoader from "@/components/layouts/ImageLoader.vue";
import Footer from "@/components/layouts/Footer.vue";
import { usePortfolioWorksStore } from "@/stores/portfolio_works";
import { onMounted, ref, nextTick } from "vue"; // Añadido nextTick
import { useMessages } from "@/composables/useMessages";
import { useFreeResources } from '@/composables/useFreeResources';
import { useRoute } from 'vue-router'; // Importar useRoute para acceder a los parámetros

const route = useRoute(); // Obtener la ruta actual
const categoriesSection = ref(null); // Referencia al div de categorías

const { messages } = useMessages();
const portfolioWorksStore = usePortfolioWorksStore();
const works = ref([]);
const worksFiltered = ref([]);
const categories = ref([]);
const selectedCategory = ref("All");
const visibleCount = ref(16);
const backgroundVideo = ref(null);

/**
 * Función para manejar el scroll automático basado en los parámetros de la ruta
 */
const handleRouteParams = async () => {
  // Esperar a que el DOM se actualice
  await nextTick();
  
  // Verificar si existe el parámetro 'example'
  if (route.params.example === 'see-dynamic-webs') {
    // Buscar si existe una categoría relacionada con webs dinámicas
    const dynamicWebCategory = categories.value.find(cat => 
      cat.toLowerCase().includes('dynamic') || 
      cat.toLowerCase().includes('dinámica') ||
      cat.toLowerCase().includes('web app')
    );
    
    // Si encontramos una categoría relacionada, seleccionarla
    if (dynamicWebCategory) {
      getFilteredWorks(dynamicWebCategory);
    }
    
    // Hacer scroll hasta la sección de categorías
    if (categoriesSection.value) {
      // Usar setTimeout para asegurarse de que todo esté renderizado
      setTimeout(() => {
        categoriesSection.value.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center' 
        });
      }, 500);
    }
  }
};

const openWork = (projectUrl) => {
  window.open(projectUrl, '_blank');
};

const getFilteredWorks = (category) => {
  selectedCategory.value = category;
  worksFiltered.value = portfolioWorksStore.getFilteredByCategory(works.value, selectedCategory.value);
};

onMounted(async () => {
  await portfolioWorksStore.init();

  const { portfolioWorks: fetchedWorks, categories: fetchedCategories } =
    portfolioWorksStore.getFilteredPortfolioWorksAndCategories;

  works.value = fetchedWorks;
  worksFiltered.value = fetchedWorks;
  categories.value = fetchedCategories;
  
  // Manejar los parámetros de la ruta después de cargar los datos
  handleRouteParams();
});

useFreeResources({
  videos: [backgroundVideo]
});

const loadMore = () => {
  visibleCount.value += 16;
};
</script>