<template>
    <div itemscope itemtype="https://schema.org/CollectionPage">
      <div class="fixed top-0 left-0 w-full z-50">
        <Navbar></Navbar>
      </div>
      <section itemscope itemtype="https://schema.org/WPHeader">
        <div class="p-3 h-svh">
          <div class="w-full h-full grid rounded-xl overflow-hidden lg:grid-cols-2">
            <div class="absolute z-10 bottom-0 flex items-center bg-transparent px-16 py-24 order-2 xl:bg-lemon xl:top-0 xl:relative xl:z-0">
              <h1 itemprop="headline">
                <span class="text-4xl font-light text-esmerald lg:text-6xl">{{ messages.header_title }}</span>
                <span class="sr-only"> - Project App. Portfolio</span><br />
                <span class="text-md font-medium text-esmerald" itemprop="description">{{ messages.header_subtitle }}</span>
                <span class="sr-only">by Project App.</span>
              </h1>
            </div>
            <div class="order-1" itemscope itemtype="https://schema.org/VideoObject">
              <div class="relative w-full h-svh overflow-hidden">
                <video ref="backgroundVideo" autoplay muted loop playsinline class="absolute inset-0 w-auto h-full object-cover" itemprop="contentUrl">
                  <source src="@/assets/videos/webDevelopments/abstractGradientBackground.mp4" type="video/mp4" />
                  Your browser does not support the video tag.
                  <span class="sr-only">Project App. video presentation</span>
                </video>
                <meta itemprop="name" content="Project App. Portfolio Background Video" />
              </div>
            </div>
          </div>
        </div>
      </section>
      <section class="px-3" itemscope itemtype="https://schema.org/CreativeWorkSeries">
        <div class="mt-32 max-w-7xl mx-auto sm:px-6 lg:mt-52 lg:px-8">
          <h1 class="text-6xl font-light text-esmerald" itemprop="name">
            {{ messages.section_title }}
            <span class="sr-only">by Project App.</span>
          </h1>
          <h2 class="text-4xl font-light text-esmerald mt-20" itemprop="alternativeHeadline">
            {{ messages.section_subtitle }}
            <span class="sr-only">Project App. portfolio</span>
          </h2>
          <p class="text-md font-light text-esmerald mt-6" itemprop="description">
            *{{ messages.custom_software_notice }}
            <span class="sr-only">Project App.</span>
          </p>
          <p class="text-2md font-light text-esmerald mt-3" itemprop="description">
            *{{ messages.dynamic_web_notice }}
            <span class="sr-only">Project App. specializes in web solutions</span>
          </p>
          <!-- Categories for filter -->
          <div 
            ref="categoriesSection"
            class="mt-24 font-regular flex flex-wrap justify-center items-center gap-3"
            itemscope itemtype="https://schema.org/ItemList"
          >
            <!-- Button for 'All' category -->
            <button
              @click="getFilteredWorks('All')"
              :class="
                selectedCategory === 'All' ? 'bg-lemon' : 'bg-esmerald-light'
              "
              class="px-6 py-2 inline-block rounded-3xl text-esmerald text-sm"
              itemprop="itemListElement"
            >
              {{ messages.all }}
              <span class="sr-only">Project App. portfolio works</span>
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
              itemprop="itemListElement"
            >
              {{ category }}
              <span class="sr-only">by Project App.</span>
            </button>
          </div>
  
          <!-- Content by portfolio works -->
          <div class="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4 lg:mt-24" role="list" aria-label="Portfolio projects">
            <div
              v-for="work in worksFiltered.slice().reverse().slice(0, visibleCount)"
              :key="work.id"
              @click="openWork(work.project_url)"
              class="cursor-pointer"
              itemscope itemtype="https://schema.org/CreativeWork"
              itemprop="workExample"
            >
              <div class="border border-gray-200 rounded-lg">
                <ImageLoader 
                  :src="work.cover_image"
                  :alt="`${work.title} - Project App. portfolio project`"
                  itemprop="image"
                />
              </div>
              <h3 class="mt-4 font-regular text-esmerald text-md" itemprop="name">
                {{ work.title }}
                <span class="sr-only">- Project App. portfolio showcase</span>
              </h3>
              <meta itemprop="creator" content="Project App." />
              <link itemprop="url" :href="work.project_url" />
            </div>
          </div>
          <!-- Button for load more content -->
          <div v-if="visibleCount < worksFiltered.length" class="text-center mt-8">
            <button @click="loadMore" class="px-6 py-2 font-regular text-md bg-lemon text-esmerlad rounded-full hover:bg-esmerald hover:text-esmerald-light">
              {{ messages.see_more }}
              <span class="sr-only">Project App portfolio works</span>
            </button>
          </div>
        </div>
      </section>
      <div class="mt-32 lg:mt-52">
        <footer itemscope itemtype="https://schema.org/WPFooter">
          <Footer></Footer>
        </footer>
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
import { useLanguageStore } from '@/stores/language';

const route = useRoute(); // Obtener la ruta actual
const categoriesSection = ref(null); // Referencia al div de categorías
const languageStore = useLanguageStore();

const { messages } = useMessages();
const portfolioWorksStore = usePortfolioWorksStore();
const works = ref([]);
const worksFiltered = ref([]);
const categories = ref([]);
const selectedCategory = ref("All");
const visibleCount = ref(16);
const backgroundVideo = ref(null);

// SEO is handled through other means in the project

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