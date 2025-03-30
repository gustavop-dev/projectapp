<template>
  <div class="bg-esmerald">
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar theme="dark" ></Navbar>
    </div>
    <section class="pt-32">
      <h1 class="text-center font-light text-6xl text-lemon lg:text-8xl">
        {{ messages.main_title }}
        <br/>
        {{ messages.main_subtitle }}
      </h1>
    </section>
    <section class="p-3 mt-32 grid md:grid-cols-2 gap-16 max-w-7xl mx-auto">
      <h2 class="text-4xl text-esmerald-light font-light lg:text-6xl">
        {{ messages.section_title }}
        <br />
        {{ messages.section_subtitle }}
      </h2>
      <p class="font-regular text-lg text-esmerald-light">
        {{ messages.description }}
      </p>
    </section>
    <section class="mt-16">
      <Vue3Marquee :pause-on-hover="true" direction="reverse" duration="35">
        <div
          class="w-72 h-full mx-auto px-4"
          v-for="(benefit, index) in messages.hostingBenefits"
          :key="index"
        >
          <div class="bg-esmerald-light rounded-xl relative h-full">
            <component
              :is="hostingBenefits[index].icon"
              class="w-16 h-16 text-esmerald text-center p-4"
            ></component>
            <p class="text-esmerald m-4 font-regular">{{ benefit.text }}</p>
          </div>
        </div>
      </Vue3Marquee>
    </section>
    <section>
      <div class="py-24 sm:py-32 px-3">
        <div class="mx-auto max-w-max px-6 lg:px-8">
          <div class="grid justify-end">
            <div class="max-w-4xl text-end">
              <h2 class="mt-2 text-4xl font-light text-lemon sm:text-6xl">
                {{ messages.pricing_title }}
              </h2>
            </div>
            <div class="flex justify-end">
              <p
                class="mt-6 max-w-2xl text-end text-lg leading-8 text-esmerald-light"
              >
                {{ messages.pricing_subtitle }}
              </p>
            </div>
            <div class="mt-16 flex justify-end">
              <fieldset aria-label="Payment frequency">
                <RadioGroup
                  v-model="frequency"
                  class="grid grid-cols-2 gap-x-1 rounded-full p-1 text-center text-sm font-regular leading-5 ring-1 ring-inset ring-esmerald-light bg-window-black bg-opacity-40 backdrop-blur-md"
                >
                  <RadioGroupOption
                    as="template"
                    v-for="option in messages.frequencies"
                    :key="option.value"
                    :value="option"
                    v-slot="{ checked }"
                  >
                    <div
                      :class="[checked ? 'bg-lemon text-esmerald' : 'text-esmerald-light', 'cursor-pointer rounded-full px-2.5 py-1']"
                    >
                      {{ option.label }}
                    </div>
                  </RadioGroupOption>
                </RadioGroup>
              </fieldset>
            </div>
          </div>
          <div
            class="isolate mx-auto mt-10 grid max-w-md grid-cols-1 gap-8 md:max-w-2xl md:grid-cols-2 lg:max-w-4xl xl:mx-0 xl:max-w-none xl:grid-cols-4"
          >
            <div
              v-for="(hosting, index) in hostings"
              :key="hosting.title"
              :id="`hosting_plan_${index + 1}`"
              :class="[index === 2 ? 'ring-2 ring-lemon bg-lemon' : 'ring-1 ring-esmerald-light bg-esmerald-light', 'rounded-xl p-8']"
            >
              <h3 class="text-2xl font-light leading-8 text-esmerald">
                {{ hosting.title }}
              </h3>
              <p class="mt-4 text-md font-regular leading-6 text-esmerald">
                {{ hosting.description }}
              </p>
              <!-- Hosting Price / Free Indicator -->
              <p 
                v-if="parseFloat(frequency.value === 'semi_annually' 
                  ? hosting.semi_annually_price 
                  : hosting.annual_price) === 0" 
                class="mt-6 flex flex-col gap-y-1 items-start"
              >
                <!-- Large 'Free' text -->
                <span class="text-4xl font-medium tracking-tight text-esmerald">
                  {{ messages.free_price }}
                </span>
                <!-- Asterisk note -->
                <span class="text-sm font-regular text-gray-600 mt-1">
                  *{{ messages.free_condition }}
                </span>
              </p>

              <p v-else class="mt-4 flex flex-col items-start">
                <!-- Save Badge -->
                <p class="mt-4 font-regular text-md text-esmerald flex items-center space-x-2">
                  <span v-if="frequency.value === 'annually'" class="line-through">
                    {{ formatHostingPrice(hosting.semi_annually_price) }}
                    {{ languageStore.currentLanguage === 'en' ? 'USD' : 'COP' }}
                  </span>
                  <span v-else>{{ messages.save_plan.text }}</span>
                  <span :class="[index === 2 ? 'bg-esmerald-light' : 'bg-lemon', 'px-4 py-0 rounded-2xl']">{{ messages.save_plan.badge }} 40%</span>
                </p>
                <!-- Price per month block -->
                <div class="mt-2 flex items-baseline gap-x-1">
                  <span class="text-4xl font-medium tracking-tight text-esmerald">
                    {{ formatHostingPrice(
                        frequency.value === "semi_annually" 
                          ? hosting.semi_annually_price 
                          : hosting.annual_price
                    ) }}
                  </span>
                  <span class="text-sm font-semibold leading-6 text-gray-600">
                    {{ languageStore.currentLanguage === 'en' ? 'USD/ Month' : 'COP/ Mensual' }} {{ frequency.priceSuffix }}
                  </span>
                </div>
                <!-- Single payment note -->
                <span class="text-sm font-regular text-gray-600 mt-1">
                  *{{ languageStore.currentLanguage === 'en' ? 'Single payment: ' : 'Pago único: ' }}
                  {{ formatHostingPrice(
                        frequency.value === "semi_annually" 
                          ? hosting.semi_annually_price * 6 
                          : hosting.annual_price * 12
                  ) }}
                  {{ languageStore.currentLanguage === 'en' ? 'USD' : 'COP' }}
                </span>
              </p>
              <a
                @click="showEmailForPlan(hosting)"
                class="mt-6 block rounded-md px-3 py-2 text-center text-sm font-semibold leading-6 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 cursor-pointer"
                :class="[index === 2 ? 'bg-esmerald-light text-esmerald shadow-sm' : 'bg-lemon text-esmerald ring-indigo-200 hover:ring-indigo-300']"
              >
                {{ messages.contact_sales }}
              </a>
              <ul role="list" class="mt-8 space-y-3 text-sm leading-6 text-gray-600">
                <li class="flex gap-x-3">
                  <CheckIcon class="h-6 w-5 flex-none text-esmerald" aria-hidden="true" />
                  {{ hosting.cpu_cores }}
                </li>
                <li class="flex gap-x-3">
                  <CheckIcon class="h-6 w-5 flex-none text-esmerald" aria-hidden="true" />
                  {{ hosting.ram }}
                </li>
                <li class="flex gap-x-3">
                  <CheckIcon class="h-6 w-5 flex-none text-esmerald" aria-hidden="true" />
                  {{ hosting.storage }}
                </li>
                <li class="flex gap-x-3">
                  <CheckIcon class="h-6 w-5 flex-none text-esmerald" aria-hidden="true" />
                  {{ hosting.bandwidth }}
                </li>
                <li class="flex gap-x-3">
                  <CheckIcon class="h-6 w-5 flex-none text-esmerald" aria-hidden="true" />
                  {{ hosting.data_center_location }}
                </li>
                <li class="flex gap-x-3">
                  <CheckIcon class="h-6 w-5 flex-none text-esmerald" aria-hidden="true" />
                  {{ hosting.operating_system }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
    <div class="p-3 bg-white">
      <Contact></Contact>
    </div>
    <div class="mt-6">
      <Footer></Footer>
    </div>
    
    <!-- Modal de Email -->
    <Email :visible="showEmailModal" :selectedPlan="selectedPlan" @update:visible="showEmailModal = $event"></Email>
  </div>
</template>

<script setup>
import Navbar from "@/components/layouts/Navbar.vue";
import Footer from "@/components/layouts/Footer.vue";
import Contact from "@/components/layouts/Contact.vue";
import Email from "@/components/layouts/Email.vue"; // Importar componente Email
import { Vue3Marquee } from "vue3-marquee";
import { ref, onMounted, nextTick, watch} from "vue";
import { RadioGroup, RadioGroupOption } from "@headlessui/vue";
import { CheckIcon } from "@heroicons/vue/20/solid";
import {
  CheckCircleIcon,
  ServerIcon,
  ShieldCheckIcon,
  ArrowTrendingUpIcon,
  UsersIcon,
  CodeBracketIcon,
} from "@heroicons/vue/24/outline";
import { useHostingStore } from "@/stores/hosting";
import { useMessages } from "@/composables/useMessages";
import { useLanguageStore } from '@/stores/language';
import { useRoute } from 'vue-router';

const { messages } = useMessages();
const hostingStore = useHostingStore();
const languageStore = useLanguageStore();
const hostings = ref([]);
const route = useRoute(); // Get access to the route object

// Define the selected frequency
const frequency = ref(messages.value.frequencies[1]);

// Estado para controlar la visibilidad del modal de Email
const showEmailModal = ref(false);
// Estado para guardar el plan seleccionado
const selectedPlan = ref(null);

// Función para abrir el modal de Email con el plan seleccionado
const showEmailForPlan = (plan) => {
  selectedPlan.value = {
    name: plan.title,
    price: formatHostingPrice(frequency.value === "semi_annually" ? plan.semi_annually_price : plan.annual_price),
    currency: languageStore.currentLanguage === 'en' ? 'USD' : 'COP',
    period: frequency.value === "semi_annually" ? messages.value.frequencies[0].label : messages.value.frequencies[1].label
  };
  showEmailModal.value = true;
};

const hostingBenefits = [
  { icon: CodeBracketIcon },
  { icon: ServerIcon },
  { icon: CheckCircleIcon },
  { icon: ShieldCheckIcon },
  { icon: ArrowTrendingUpIcon },
  { icon: UsersIcon },
];

// Función para formatear el precio según el idioma actual
const formatHostingPrice = (price) => {
  
  // Verificar el tipo y formato del precio
  let numericPrice;
  
  if (typeof price === 'string') {
    // Si el precio viene como "50.000" (formato colombiano) 
    // necesitamos eliminar los puntos para convertirlo correctamente
    // pero solo si los puntos son separadores de miles
    
    // Comprobamos si tiene formato colombiano (puntos como separador de miles)
    if (price.match(/^\d{1,3}(\.\d{3})+$/)) {
      // Es un formato colombiano con puntos como separadores
      const cleanPrice = price.replace(/\./g, '');
      numericPrice = parseFloat(cleanPrice);
    }
    // Si termina en ".00" podría ser un decimal normal, no un separador
    else if (price.endsWith('.00')) {
      numericPrice = parseFloat(price);
    }
    // En cualquier otro caso, intentamos parsear directamente
    else {
      numericPrice = parseFloat(price);
    }
  } else {
    // Si es número, lo usamos directamente
    numericPrice = parseFloat(price);
  }
  
  if (isNaN(numericPrice)) {
    console.error('Valor de precio inválido:', price);
    return price;
  }
  
  
  // Aplicar tasa de conversión según idioma
  const conversionRate = languageStore.currentLanguage === 'en' ? 0.0006 : 1;
  const convertedValue = numericPrice * conversionRate;
  
  // Formatear según el idioma
  if (languageStore.currentLanguage === 'es') {
    // Formato colombiano: usar puntos como separadores de miles
    const roundedValue = Math.round(convertedValue);
    return roundedValue.toLocaleString('es-CO').replace(/,/g, '.');
  } else {
    // Formato inglés: usar comas como separadores y mostrar 2 decimales
    return convertedValue.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }
};

/**
 * Scrolls to the specified hosting plan with a smooth animation.
 * 
 * @param {string} planId - The ID of the plan to scroll to
 */
 const scrollToPlan = async (planId) => {
  // Wait for the DOM to be updated
  await nextTick();
  
  // Find the plan element by its ID
  const planElement = document.getElementById(planId);
  
  if (planElement) {
    // Scroll to the element with a smooth animation
    planElement.scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    });
    
    // Highlight the plan temporarily
    planElement.classList.add('highlight-plan');
    setTimeout(() => {
      planElement.classList.remove('highlight-plan');
    }, 2000);
  }
};

onMounted(async () => {
  await Promise.all([
    hostingStore.init(),
    languageStore.loadMessagesForView('hosting')
  ]);
  hostings.value = hostingStore.getHostings;
  
  
  // Verificamos específicamente los valores de precio
  if (hostings.value && hostings.value.length > 0) {
    hostings.value.forEach((hosting, index) => {
      
      // Verificamos si es posible que haya un problema con decimales
      if (typeof hosting.semi_annually_price === 'string' && hosting.semi_annually_price.includes('.')) {
        const parts = hosting.semi_annually_price.split('.');
        if (parts[1].length > 2) {
          console.warn('Posible error de formato: el precio tiene más de 2 decimales');
        }
      }
    });
  }

  // Check if we need to scroll to a specific plan
  if (route.params.plan) {
    // Allow some time for the component to fully render
    setTimeout(() => {
      scrollToPlan(route.params.plan);
    }, 500); 
  }
});

// Watch for changes in the route params to handle direct navigation
watch(
  () => route.params.plan,
  (newPlanId) => {
    if (newPlanId && hostings.value.length > 0) {
      scrollToPlan(newPlanId);
    }
  }
);
</script>