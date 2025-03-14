<template>
  <!-- Main container for the eCommerce Prices page -->
  <div class="bg-esmerald-light">
    <!-- Fixed Navbar at the top -->
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar></Navbar>
    </div>
    <!-- Spacer to account for the fixed navbar -->
    <div class="h-32"></div>
    <!-- Hero Section -->
    <section>
      <h1 class="text-center font-light text-6xl text-esmerald lg:text-8xl">
        {{ messages.hero_section.title_line1 }}
        <br />
        {{ messages.hero_section.title_line2 }}
      </h1>
    </section>
    <!-- Wordpress Component -->
    <Wordpress></Wordpress>
    
    <!-- Products Section -->
    <div v-if="products.length">
      <!-- Loop through each product -->
      <div v-for="(product, index) in products" :key="index">
        <!-- Even-indexed product layout -->
        <section v-if="index % 2 === 0" class="mt-32 w-full px-3">
          <h2 class="text-esmerald text-4xl font-light lg:text-6xl">
            {{ product.title }}
          </h2>
          <div class="grid mt-6 lg:grid-cols-3">
            <!-- Left Column: Product details -->
            <div class="bg-esmerald rounded-b-xl p-6 grid order-2 gap-2 md:grid-cols-2 lg:rounded-r-none lg:rounded-l-xl lg:col-span-2 lg:order-1">
              <!-- Categories and items -->
              <div class="grid gap-3 mt-6 order-2 lg:mt-0 lg:order-1">
                <div v-for="(category, catIndex) in (product.categories || [])" :key="catIndex">
                  <h3 class="text-xl text-white font-light">{{ category.name }}</h3>
                  <ul class="font-regular text-lg text-green-light ps-6">
                    <li v-for="(item, itemIndex) in (category.items || [])" :key="itemIndex" class="flex items-center gap-2">
                      <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                      {{ item.name }}
                    </li>
                  </ul>
                </div>
              </div>
              <!-- Product description and additional details -->
              <div class="border-l border-l-green-light ps-4 order-1 lg:order-2 space-y-2">
                <!-- Product description -->
                <p class="text-lg text-green-light font-regular whitespace-pre-line">
                  {{ product.description }}
                </p>
                <br />
                <!-- Figma Design Information with Tooltip (checkbox checked & disabled) -->
                <p class="text-md font-regular text-white flex gap-2 items-center">
                  <div class="flex h-6 shrink-0 items-center text-esmerald">
                    <div class="group grid size-6 grid-cols-1">
                      <input id="comments" aria-describedby="comments-description" name="comments" type="checkbox" checked disabled class="cursor-not-allowed col-start-1 row-start-1 appearance-none rounded border border-lemon bg-esmerald checked:border-lemon checked:bg-lemon focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:checked:bg-lemon" />
                      <svg class="pointer-events-none col-start-1 row-start-1 size-4 self-center justify-self-center stroke-esmerald group-has-[:disabled]:stroke-esmerald" viewBox="0 0 14 14" fill="none">
                        <path class="opacity-0 group-has-[:checked]:opacity-100" d="M3 8L6 11L11 3.5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                        <path class="opacity-0 group-has-[:indeterminate]:opacity-100" d="M3 7H11" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                    </div>
                  </div>
                  {{ messages.product_details.figma_design.title }} 
                  <Tooltip width="w-60" backgroundColor="bg-lemon" textColor="text-esmerald">
                    <div>
                      <p>{{ messages.product_details.figma_design.description }}</p>
                    </div>
                  </Tooltip>
                </p>
                <!-- Responsive Design Information with Tooltip (checkbox checked & disabled) -->
                <p class="text-md font-regular text-white flex gap-2 items-center">
                  <div class="flex h-6 shrink-0 items-center text-esmerald">
                    <div class="group grid size-6 grid-cols-1">
                      <input id="comments" aria-describedby="comments-description" name="comments" type="checkbox" checked disabled class="cursor-not-allowed col-start-1 row-start-1 appearance-none rounded border border-lemon bg-esmerald checked:border-lemon checked:bg-lemon focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:checked:bg-lemon" />
                      <svg class="pointer-events-none col-start-1 row-start-1 size-4 self-center justify-self-center stroke-esmerald group-has-[:disabled]:stroke-esmerald" viewBox="0 0 14 14" fill="none">
                        <path class="opacity-0 group-has-[:checked]:opacity-100" d="M3 8L6 11L11 3.5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                        <path class="opacity-0 group-has-[:indeterminate]:opacity-100" d="M3 7H11" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                    </div>
                  </div>
                  {{ messages.product_details.responsive_design.title }} 
                  <Tooltip width="w-60" backgroundColor="bg-lemon" textColor="text-esmerald">
                    <div>
                      <p>{{ messages.product_details.responsive_design.description }}</p>
                    </div>
                  </Tooltip>
                </p>
                <!-- Animations Information with Tooltip and Router Link (interactive checkbox) -->
                <p class="text-md font-regular text-white flex gap-2 items-center">
                  <div class="flex h-6 shrink-0 items-center text-esmerald">
                    <div class="group grid size-6 grid-cols-1">
                      <input  v-model="productStates[index].animationChecked" id="comments" aria-describedby="comments-description" name="comments" type="checkbox" class="cursor-pointer col-start-1 row-start-1 appearance-none rounded border border-lemon bg-esmerald checked:border-lemon checked:bg-lemon focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:checked:bg-lemon" />
                      <svg class="pointer-events-none col-start-1 row-start-1 size-4 self-center justify-self-center stroke-esmerald group-has-[:disabled]:stroke-esmerald" viewBox="0 0 14 14" fill="none">
                        <path class="opacity-0 group-has-[:checked]:opacity-100" d="M3 8L6 11L11 3.5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                        <path class="opacity-0 group-has-[:indeterminate]:opacity-100" d="M3 7H11" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                    </div>
                  </div>
                  {{ messages.product_details.animations.title }} 
                  <router-link :to="{name: 'portfolioWorks', params: { example: 'see-dynamic-webs' }}">
                    <Tooltip width="w-60" backgroundColor="bg-lemon" textColor="text-esmerald">
                      <div>
                        <p>{{ messages.product_details.animations.description }}</p>
                        <p>{{ messages.product_details.animations.click }}</p>
                      </div>
                    </Tooltip>
                  </router-link>
                </p>
                <!-- Mobile App Information with Tooltip (interactive checkbox) -->
                <p class="text-md font-regular text-white flex gap-2 items-center">
                  <div class="flex h-6 shrink-0 items-center text-esmerald">
                    <div class="group grid size-6 grid-cols-1">
                      <input v-model="productStates[index].mobileAppChecked" id="comments" aria-describedby="comments-description" name="comments" type="checkbox" class="cursor-pointer col-start-1 row-start-1 appearance-none rounded border border-lemon bg-esmerald checked:border-lemon checked:bg-lemon focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:checked:bg-lemon" />
                      <svg class="pointer-events-none col-start-1 row-start-1 size-4 self-center justify-self-center stroke-esmerald group-has-[:disabled]:stroke-esmerald" viewBox="0 0 14 14" fill="none">
                        <path class="opacity-0 group-has-[:checked]:opacity-100" d="M3 8L6 11L11 3.5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                        <path class="opacity-0 group-has-[:indeterminate]:opacity-100" d="M3 7H11" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                    </div>
                  </div>
                  {{ messages.product_details.mobile_app.title }} 
                  <Tooltip width="w-60" backgroundColor="bg-lemon" textColor="text-esmerald">
                    <div>
                      <p>{{ messages.product_details.mobile_app.description }}</p>
                    </div>
                  </Tooltip>
                </p>
                <!-- Product Price -->
                <p class="text-md font-regular text-white flex gap-2">
                  <BanknotesIcon class="w-6 h-6 text-lemon"></BanknotesIcon> 
                  {{ messages.product_details?.price_label || '$' }} {{ formatPrice(calculateTotalPrice(product, productStates[index])) }} {{ languageStore.currentLanguage === 'en' ? 'USD' : 'COP' }}
                </p>
                <!-- Development Time -->
                <p class="text-md font-regular text-white flex gap-2 mt-2">
                  <ClockIcon class="w-6 h-6 text-lemon"></ClockIcon> {{ product.development_time }}
                </p>
                <!-- Hosting Information with Router Link -->
                <router-link 
                  v-if="product.hosting_name" 
                  :to="{name: 'hosting', params: { plan: `hosting_plan_${product.hosting_id || '1'}` }}"
                  class="text-md font-regular text-white flex gap-2 mt-2 cursor-pointer hover:text-lemon transition-colors"
                >
                  <ServerStackIcon class="w-6 h-6 text-lemon"></ServerStackIcon>
                  {{ messages.product_details.server }} ({{ product.hosting_name }})
                </router-link>
              </div>
            </div>
            <!-- Right Column: Product Image -->
            <div class="flex justify-center items-center order-1 lg:order-2">
              <img
                :src="product.image"
                loading="lazy"
                class="w-full h-full object-cover rounded-t-xl lg:rounded-l-none lg:rounded-r-xl"
              />
            </div>
          </div>
        </section>
    
        <!-- Odd-indexed product layout -->
        <section v-else class="mt-32 w-full px-3">
          <h2 class="text-esmerald text-end text-4xl font-light lg:text-6xl">
            {{ product.title }}
          </h2>
          <div class="grid mt-6 lg:grid-cols-3">
            <!-- Left Column: Product Image -->
            <div class="flex justify-center items-center">
              <img
                :src="product.image"
                loading="lazy"
                class="w-full h-full object-cover rounded-t-xl lg:rounded-r-none lg:rounded-l-xl"
              />
            </div>
            <!-- Right Column: Product details -->
            <div class="bg-esmerald rounded-b-xl p-6 grid order-2 gap-2 md:grid-cols-2 lg:rounded-l-none lg:rounded-r-xl lg:col-span-2 lg:order-2">
              <div class="border-r border-r-green-light pe-4 space-y-2">
                <!-- Product description -->
                <p class="text-lg text-green-light font-regular text-end whitespace-pre-line">
                  {{ product.description }}
                </p>
                <br />
                <!-- Figma Design Information with Tooltip (checkbox checked & disabled) -->
                <p class="text-md font-regular text-white flex gap-2 justify-end items-center">
                  <Tooltip width="w-60" backgroundColor="bg-lemon" textColor="text-esmerald">
                    <div>
                      <p>{{ messages.product_details.figma_design.description }}</p>
                    </div>
                  </Tooltip>
                  {{ messages.product_details.figma_design.title }} 
                  <div class="flex h-6 shrink-0 items-center text-esmerald">
                    <div class="group grid size-6 grid-cols-1">
                      <input id="comments" aria-describedby="comments-description" name="comments" type="checkbox" checked disabled class="cursor-not-allowed col-start-1 row-start-1 appearance-none rounded border border-lemon bg-esmerald checked:border-lemon checked:bg-lemon focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:checked:bg-lemon" />
                      <svg class="pointer-events-none col-start-1 row-start-1 size-4 self-center justify-self-center stroke-esmerald group-has-[:disabled]:stroke-esmerald" viewBox="0 0 14 14" fill="none">
                        <path class="opacity-0 group-has-[:checked]:opacity-100" d="M3 8L6 11L11 3.5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                        <path class="opacity-0 group-has-[:indeterminate]:opacity-100" d="M3 7H11" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                    </div>
                  </div>
                </p>
                <!-- Responsive Design Information with Tooltip (checkbox checked & disabled) -->
                <p class="text-md font-regular text-white flex gap-2 justify-end items-center">
                  <Tooltip width="w-60" backgroundColor="bg-lemon" textColor="text-esmerald">
                    <div>
                      <p>{{ messages.product_details.responsive_design.description }}</p>
                    </div>
                  </Tooltip>
                  {{ messages.product_details.responsive_design.title }} 
                  <div class="flex h-6 shrink-0 items-center text-esmerald">
                    <div class="group grid size-6 grid-cols-1">
                      <input id="comments" aria-describedby="comments-description" name="comments" type="checkbox" checked disabled class="cursor-not-allowed col-start-1 row-start-1 appearance-none rounded border border-lemon bg-esmerald checked:border-lemon checked:bg-lemon focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:checked:bg-lemon" />
                      <svg class="pointer-events-none col-start-1 row-start-1 size-4 self-center justify-self-center stroke-esmerald group-has-[:disabled]:stroke-esmerald" viewBox="0 0 14 14" fill="none">
                        <path class="opacity-0 group-has-[:checked]:opacity-100" d="M3 8L6 11L11 3.5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                        <path class="opacity-0 group-has-[:indeterminate]:opacity-100" d="M3 7H11" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                    </div>
                  </div>
                </p>
                <!-- Animations Information with Tooltip and Router Link (interactive checkbox) -->
                <p class="text-md font-regular text-white flex gap-2 justify-end items-center">
                  <router-link :to="{name: 'portfolioWorks', params: { example: 'see-dynamic-webs' }}">
                    <Tooltip width="w-60" backgroundColor="bg-lemon" textColor="text-esmerald">
                      <div>
                        <p>{{ messages.product_details.animations.description }}</p>
                        <p>{{ messages.product_details.animations.click }}</p>
                      </div>
                    </Tooltip>
                  </router-link>
                  {{ messages.product_details.animations.title }} 
                  <div class="flex h-6 shrink-0 items-center text-esmerald">
                    <div class="group grid size-6 grid-cols-1">
                      <input v-model="productStates[index].animationChecked" id="comments" aria-describedby="comments-description" name="comments" type="checkbox" class="cursor-pointer col-start-1 row-start-1 appearance-none rounded border border-lemon bg-esmerald checked:border-lemon checked:bg-lemon focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:checked:bg-lemon" />
                      <svg class="pointer-events-none col-start-1 row-start-1 size-4 self-center justify-self-center stroke-esmerald group-has-[:disabled]:stroke-esmerald" viewBox="0 0 14 14" fill="none">
                        <path class="opacity-0 group-has-[:checked]:opacity-100" d="M3 8L6 11L11 3.5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                        <path class="opacity-0 group-has-[:indeterminate]:opacity-100" d="M3 7H11" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                    </div>
                  </div>
                </p>
                <!-- Mobile App Information with Tooltip (interactive checkbox) -->
                <p class="text-md font-regular text-white flex gap-2 justify-end items-center">
                  <Tooltip width="w-60" backgroundColor="bg-lemon" textColor="text-esmerald">
                    <div>
                      <p>{{ messages.product_details.mobile_app.description }}</p>
                    </div>
                  </Tooltip>
                  {{ messages.product_details.mobile_app.title }} 
                  <div class="flex h-6 shrink-0 items-center text-esmerald">
                    <div class="group grid size-6 grid-cols-1">
                      <input v-model="productStates[index].mobileAppChecked" id="comments" aria-describedby="comments-description" name="comments" type="checkbox" class="cursor-pointer col-start-1 row-start-1 appearance-none rounded border border-lemon bg-esmerald checked:border-lemon checked:bg-lemon focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:checked:bg-lemon" />
                      <svg class="pointer-events-none col-start-1 row-start-1 size-4 self-center justify-self-center stroke-esmerald group-has-[:disabled]:stroke-esmerald" viewBox="0 0 14 14" fill="none">
                        <path class="opacity-0 group-has-[:checked]:opacity-100" d="M3 8L6 11L11 3.5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                        <path class="opacity-0 group-has-[:indeterminate]:opacity-100" d="M3 7H11" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                    </div>
                  </div>
                </p>
                <!-- Product Price -->
                <p class="text-md font-regular text-white flex gap-2 justify-end">
                  {{ messages.product_details?.price_label || '$' }} {{ formatPrice(calculateTotalPrice(product, productStates[index])) }} {{ languageStore.currentLanguage === 'en' ? 'USD' : 'COP' }}
                  <BanknotesIcon class="w-6 h-6 text-lemon"></BanknotesIcon>
                </p>
                <!-- Development Time -->
                <p class="text-md font-regular text-white flex gap-2 mt-2 justify-end">
                  {{ product.development_time }} <ClockIcon class="w-6 h-6 text-lemon"></ClockIcon>
                </p>
                <!-- Hosting Information with Router Link -->
                <router-link 
                  v-if="product.hosting_name" 
                  :to="{name: 'hosting', params: { plan: `hosting_plan_${product.hosting_id || '1'}` }}"
                  class="text-md font-regular text-white flex gap-2 mt-2 justify-end cursor-pointer hover:text-lemon transition-colors"
                >
                  {{ messages.product_details.server }} ({{ product.hosting_name }}) <ServerStackIcon class="w-6 h-6 text-lemon"></ServerStackIcon>
                </router-link>
              </div>
              <!-- Categories list -->
              <div class="grid text-end mt-6 lg:mt-0">
                <div v-for="(category, catIndex) in (product.categories || [])" :key="catIndex">
                  <h3 class="text-xl text-white font-light">{{ category.name }}</h3>
                  <ul class="font-regular text-lg text-green-light ps-6">
                    <li v-for="(item, itemIndex) in (category.items || [])" :key="itemIndex" class="flex items-center gap-2 justify-end">
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
    </div>

    <!-- Contact Component -->
    <Contact></Contact>

    <!-- Footer Component -->
    <div class="mt-16">
      <Footer></Footer>
    </div>
  </div>
</template>

<script setup>
// Import necessary components for layout and UI
import Navbar from "@/components/layouts/Navbar.vue";
import Footer from "@/components/layouts/Footer.vue";
import Contact from "@/components/layouts/Contact.vue";
import Wordpress from "@/components/utils/Wordpress.vue";
import Tooltip from "@/components/ui/Tooltip.vue";
import {
  BanknotesIcon,
  CheckBadgeIcon,
  ClockIcon,
  ServerStackIcon,
} from "@heroicons/vue/24/outline";

// Import stores and Vue functions
import { useProductStore } from "@/stores/products";
import { onMounted, ref } from "vue";
import { useFreeResources } from "@/composables/useFreeResources";
import { useMessages } from "@/composables/useMessages";
import { useLanguageStore } from "@/stores/language";

// Reactive variable for storing products
const products = ref([]);

// Get instance of the product store
const productStore = useProductStore();

// Get instance of the language store
const languageStore = useLanguageStore();

// Retrieve localized messages for the current view
const { messages } = useMessages();

// Create a reactive array to hold state for each product
const productStates = ref([]);

/**
 * Format the given price based on the current language.
 *
 * This function cleans the input price (removes dots or non-digit characters),
 * converts it to a number, applies a conversion rate, and formats it using the appropriate locale.
 *
 * @param {number|string} price - The raw price value.
 * @returns {string} - The formatted price string.
 */
const formatPrice = (price) => {
  // Remove dots from the price string
  let cleanPrice = String(price).replace(/\./g, '');
  let numericPrice = Number(cleanPrice);
  // If the cleaned value is not a number, try removing non-digit characters
  if (isNaN(numericPrice)) {
    cleanPrice = String(price).replace(/[^\d]/g, '');
    numericPrice = Number(cleanPrice);
    if (isNaN(numericPrice)) {
      console.error('Invalid price value:', price);
      return price;
    }
  }
  // Determine conversion rate based on current language (e.g., for USD conversion)
  const conversionRate = languageStore.currentLanguage === 'en' ? 0.0006 : 1;
  const convertedValue = numericPrice * conversionRate;
  // Format price based on locale
  if (languageStore.currentLanguage === 'es') {
    const roundedValue = Math.round(convertedValue);
    return roundedValue.toLocaleString('es-CO').replace(/,/g, '.');
  } else {
    return convertedValue.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }
};

/**
 * Calculates the total price for a product.
 * - Starts with the base price from product.price.
 * - If the mobile app checkbox is active, adds product.mobile_app_price.
 * - If the animations checkbox is active, adds half of the base price.
 *
 * @param {Object} product - The product object.
 * @returns {number} - The total price before formatting.
 */
 const calculateTotalPrice = (product, state) => {
  let basePrice = parseFloat(String(product.price).replace(/\./g, '').replace(/[^\d\.]/g, ''));
  let mobilePrice = parseFloat(String(product.mobile_app_price).replace(/\./g, '').replace(/[^\d\.]/g, ''));
  console.log(product)
  if (isNaN(basePrice)) basePrice = 0;
  let total = basePrice;
  
  // Add mobile app price if active
  if (state.mobileAppChecked && product.mobile_app_price) {
    if (!isNaN(mobilePrice)) total += mobilePrice;
  }
  
  // Add half of the base price if animations checkbox is active
  if (state.animationChecked) {
    total += mobilePrice / 2;
  }
  
  return total;
};


/**
 * onMounted lifecycle hook:
 * - Initializes the product store.
 * - Loads localized messages for the "eCommercePrices" view.
 * - Assigns the retrieved products to the reactive variable.
 * - Frees resources associated with product images.
 */
onMounted(async () => {
  await Promise.all([
    productStore.init(),
    languageStore.loadMessagesForView("eCommercePrices")
  ]);
  // Determine whether getProducts is a function or a computed property
  const productsData =
    typeof productStore.getProducts === "function"
      ? productStore.getProducts()
      : productStore.getProducts;
  products.value = Array.isArray(productsData) ? productsData : [];

  // Initialize state for each product (using index)
  productStates.value = products.value.map(() => ({
    animationChecked: false,
    mobileAppChecked: false,
  }));
  
  // Free resources for product images to help manage memory
  useFreeResources({
    images: products.value.map((product) => ref(product.image))
  });
});
</script>
