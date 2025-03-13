<template>
  <div class="bg-esmerald-light">
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar></Navbar>
    </div>
    <div class="h-32"></div>
    <section>
      <h1 class="text-center font-light text-6xl text-esmerald lg:text-8xl">
        {{ messages.hero_section.title_line1 }}
        <br />
        {{ messages.hero_section.title_line2 }}
      </h1>
    </section>
    <Wordpress></Wordpress>
    
    <!-- Products -->
    <div v-if="products.length" v-for="(product, index) in products" :key="index">
      <section v-if="index % 2 === 0" class="mt-32 w-full px-3">
        <h2 class="text-esmerald text-4xl font-light lg:text-6xl">
          {{ product.title }}
        </h2>
        <div class="grid mt-6 lg:grid-cols-3">
          <div
            class="bg-esmerald rounded-b-xl p-6 grid order-2 gap-2 md:grid-cols-2 lg:rounded-r-none lg:rounded-l-xl lg:col-span-2 lg:order-1"
          >
            <div class="grid gap-3 mt-6 order-2 lg:mt-0 lg:order-1">
              <div v-if="product.categories && product.categories.length" v-for="category in product.categories">
                <h3 class="text-xl text-white font-light">{{ category.name }}</h3>
                <ul class="font-regular text-lg text-green-light ps-6">
                  <li v-for="item in category.items" class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >{{ item.name }}
                  </li>
                </ul>
              </div>
            </div>
            <div class="border-l border-l-green-light ps-4 order-1 lg:order-2 space-y-2">
              <p class="text-lg text-green-light font-regular whitespace-pre-line">
                {{ product.description }}
              </p>
              <br />
              <p class="text-md font-regular text-white flex gap-2 items-center">
                <CheckIcon class="w-6 h-6 text-lemon"></CheckIcon>
                {{ messages.product_details.figma_design.title }} 
                <Tooltip width="w-60" backgroundColor="bg-lemon" textColor="text-esmerald">
                  <div>
                    <p>{{ messages.product_details.figma_design.description }}</p>
                  </div>
                </Tooltip>
              </p>
              <p class="text-md font-regular text-white flex gap-2 items-center">
                <CheckIcon class="w-6 h-6 text-lemon"></CheckIcon>
                {{ messages.product_details.responsive_design.title }} 
                <Tooltip width="w-60" backgroundColor="bg-lemon" textColor="text-esmerald">
                  <div>
                    <p>{{ messages.product_details.responsive_design.description }}</p>
                  </div>
                </Tooltip>
              </p>
              <p class="text-md font-regular text-white flex gap-2 items-center">
                <XMarkIcon class="w-6 h-6 text-lemon"></XMarkIcon>
                {{ messages.product_details.animations.title }} 
                <router-link
                  :to="{name: 'portfolioWorks', params: { example: 'see-dynamic-webs' }}"
                >
                  <Tooltip width="w-60" backgroundColor="bg-lemon" textColor="text-esmerald">
                    <div>
                      <p>{{ messages.product_details.animations.description }}</p>
                      <p>
                        {{ messages.product_details.animations.click }}
                      </p>
                    </div>
                  </Tooltip>
                </router-link>
              </p>
              <p class="text-md font-regular text-white flex gap-2 items-center">
                <XMarkIcon class="w-6 h-6 text-lemon"></XMarkIcon>
                {{ messages.product_details.mobile_app.title }} 
                <Tooltip width="w-60" backgroundColor="bg-lemon" textColor="text-esmerald">
                  <div>
                    <p>{{ messages.product_details.mobile_app.description }}</p>
                  </div>
                </Tooltip>
              </p>
              <p class="text-md font-regular text-white flex gap-2">
                <BanknotesIcon class="w-6 h-6 text-lemon"></BanknotesIcon> 
                {{ messages.product_details?.price_label || '$' }} {{ formatPrice(product.price) }} {{ languageStore.currentLanguage === 'en' ? 'USD' : 'COP' }}
              </p>
              <p class="text-md font-regular text-white flex gap-2 mt-2">
                <ClockIcon class="w-6 h-6 text-lemon"></ClockIcon> {{ product.development_time }}
              </p>
              
              <router-link 
                v-if="product.hosting_name" 
                :to="{name: 'hosting', params: { plan: `hosting_plan_${product.hosting_id || '1'}` }}"
                class="text-md font-regular text-white flex gap-2 mt-2 cursor-pointer hover:text-lemon transition-colors"
              >
                <ServerStackIcon class="w-6 h-6 text-lemon"></ServerStackIcon>
                {{messages.product_details.server}} ({{ product.hosting_name }})
              </router-link>
            </div>
          </div>
          <div class="flex justify-center items-center order-1 lg:order-2">
            <img
              :src="product.image"
              loading="lazy"
              class="w-full h-full object-cover rounded-t-xl lg:rounded-l-none lg:rounded-r-xl"
            />
          </div>
        </div>
      </section>
  
      <section v-else class="mt-32 w-full px-3">
        <h2 class="text-esmerald text-end text-4xl font-light lg:text-6xl">
          {{ product.title }}
        </h2>
        <div class="grid mt-6 lg:grid-cols-3">
          <div class="flex justify-center items-center">
            <img
              :src="product.image"
              loading="lazy"
              class="w-full h-full object-cover rounded-t-xl lg:rounded-r-none lg:rounded-l-xl"
            />
          </div>
          <div
            class="bg-esmerald rounded-b-xl p-6 grid order-2 gap-2 md:grid-cols-2 lg:rounded-l-none lg:rounded-r-xl lg:col-span-2 lg:order-2"
          >
            <div class="border-r border-r-green-light pe-4">
              <p class="text-lg text-green-light font-regular text-end whitespace-pre-line">
                {{ product.description }}
              </p>
              <br />
              <p class="text-md font-regular text-white flex gap-2 justify-end">
                  {{ messages.product_details?.price_label || '$' }} {{ formatPrice(product.price) }} {{ languageStore.currentLanguage === 'en' ? 'USD' : 'COP' }}
                  <BanknotesIcon class="w-6 h-6 text-lemon"></BanknotesIcon> 
              </p>
              <p class="text-md font-regular text-white flex gap-2 mt-2 justify-end">
                {{ product.development_time }} <ClockIcon class="w-6 h-6 text-lemon"></ClockIcon>
              </p>
              
              <router-link 
                v-if="product.hosting_name" 
                :to="{name: 'hosting', params: { plan: `hosting_plan_${product.hosting_id || '1'}` }}"
                class="text-md font-regular text-white flex gap-2 mt-2 justify-end cursor-pointer hover:text-lemon transition-colors"
              >
                {{messages.product_details.server}} ({{ product.hosting_name }}) <ServerStackIcon class="w-6 h-6 text-lemon"></ServerStackIcon>
              </router-link>
              
            </div>
            <div class="grid text-end mt-6 lg:mt-0">
              <div v-if="product.categories && product.categories.length" v-for="category in product.categories">
                <h3 class="text-xl text-white font-light">{{ category.name }}</h3>
                <ul class="font-regular text-lg text-green-light ps-6">
                  <li v-for="item in category.items" class="flex items-center gap-2 justify-end">
                      {{ item.name }}
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <Contact></Contact>

    <div class="mt-16">
        <Footer></Footer>
    </div>
  </div>
</template>

<script setup>
import Navbar from "@/components/layouts/Navbar.vue";
import Footer from "@/components/layouts/Footer.vue";
import Contact from "@/components/layouts/Contact.vue";
import Wordpress from "@/components/utils/Wordpress.vue";
import Tooltip from "@/components/ui/Tooltip.vue"
import {
  BanknotesIcon,
  CheckBadgeIcon,
  ClockIcon,
  ServerStackIcon,
  CheckIcon,
  XMarkIcon
} from "@heroicons/vue/24/outline";
import { useProductStore } from "@/stores/products";
import { onMounted, ref } from "vue";
import { useFreeResources } from '@/composables/useFreeResources';
import { useMessages } from '@/composables/useMessages';
import { useLanguageStore } from '@/stores/language';

// Obtener los stores necesarios
const products = ref([]);
const productStore = useProductStore();
const languageStore = useLanguageStore();

// Obtener los mensajes para la vista actual
const { messages } = useMessages();

// Función para formatear el precio según el idioma actual
const formatPrice = (price) => {
  // El precio puede venir como "500.000" (string con formato colombiano)
  // Primero limpiamos el precio eliminando los puntos para poder convertirlo correctamente a número
  let cleanPrice = String(price).replace(/\./g, '');
  let numericPrice = Number(cleanPrice);
  
  // Si sigue sin ser un número válido, intentamos una limpieza más agresiva
  if (isNaN(numericPrice)) {
    cleanPrice = String(price).replace(/[^\d]/g, '');
    numericPrice = Number(cleanPrice);
    
    if (isNaN(numericPrice)) {
      console.error('Invalid price value:', price);
      return price; // Devolvemos el original si no podemos procesarlo
    }
  }
  
  // Obtener la tasa de conversión según el idioma
  const conversionRate = languageStore.currentLanguage === 'en' ? 0.0006 : 1;
  
  // Aplicar la conversión
  const convertedValue = numericPrice * conversionRate;
  
  // Formatear según el idioma
  if (languageStore.currentLanguage === 'es') {
    // Formato colombiano: usar puntos como separadores de miles y millones
    // Redondeamos para eliminar decimales en el formato colombiano
    const roundedValue = Math.round(convertedValue);
    
    // Usamos toLocaleString con el formato 'es-CO' para obtener el formato colombiano correcto
    return roundedValue.toLocaleString('es-CO').replace(/,/g, '.');
  } else {
    // Formato inglés: 1,000,000.00 (coma como separador de miles, dos decimales)
    return convertedValue.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }
};

onMounted(async () => {
  // Al montar el componente, cargar los mensajes para la vista "eCommercePrices"
  await Promise.all([
    productStore.init(),
    languageStore.loadMessagesForView('eCommercePrices')
  ]);
  products.value = productStore.getProducts;
});

// Use free resources to ensure images and videos are cleaned up when unmounted
useFreeResources({
  images: products.value.map(product => ref(product.image)),
});
</script>