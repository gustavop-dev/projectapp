<template>
  <!-- Main container for the eCommerce Prices page -->
  <div class="bg-esmerald-light" itemscope itemtype="https://schema.org/WebPage">
    <!-- Fixed Navbar at the top -->
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar></Navbar>
    </div>
    <!-- Spacer to account for the fixed navbar -->
    <div class="h-32"></div>
    <!-- Hero Section -->
    <section aria-labelledby="main-heading" itemscope itemtype="https://schema.org/PriceSpecification">
      <h1 id="main-heading" class="text-center font-light text-6xl text-esmerald lg:text-8xl" itemprop="name">
        {{ messages.hero_section.title_line1 }}
        <span class="sr-only">Project App.</span>
        <br />
        {{ messages.hero_section.title_line2 }}
        <span class="sr-only">- Project App. e-Commerce Solutions</span>
      </h1>
    </section>
    <!-- Wordpress Component -->
    <section aria-label="Why Project App. custom solutions vs WordPress" itemscope itemtype="https://schema.org/Article">
      <Wordpress></Wordpress>
    </section>
    
    <!-- Products Section -->
    <div v-if="products.length" role="region" aria-label="E-Commerce Products and Pricing">
      <!-- Loop through each product -->
      <div v-for="(product, index) in products" :key="index" itemscope itemtype="https://schema.org/Offer">
        <!-- Even-indexed product layout -->
        <section v-if="index % 2 === 0" class="mt-32 w-full px-3" :aria-labelledby="`product-title-${index}`">
          <div class="max-w-7xl mx-auto sm:px-6 lg:px-8 flex flex-col lg:flex-row justify-between">
            <!-- Left column (Product info) -->
            <div class="lg:w-5/12 w-full mb-16 lg:mb-0">
              <h2 :id="`product-title-${index}`" class="text-6xl lg:text-9xl font-light mb-8 text-esmerald" itemprop="name">
                {{ product.title }}
                <span class="sr-only"> - Project App. solution</span>
              </h2>
              <p class="font-regular text-esmerald text-xl mb-8" itemprop="description">
                {{ product.description }}
                <span class="sr-only"> from Project App.</span>
              </p>
              
              <div class="flex flex-col md:flex-row justify-between">
                <!-- Left pricing column -->
                <div class="md:w-5/12 w-full mb-8 md:mb-0">
                  <p class="text-lemon text-5xl lg:text-6xl font-light" itemprop="price">
                    {{ product.price }}
                  </p>
                  <meta itemprop="priceCurrency" content="EUR" />
                  
                  <p v-if="product.price_monthly" class="text-lemon text-xl mt-4">
                    {{ product.price_monthly }}
                  </p>
                </div>
                
                <!-- Right feature list column -->
                <div class="md:w-6/12 w-full">
                  <p class="mb-4 text-xl text-esmerald">
                    {{ messages.product_section.includes }}:
                  </p>
                  <ul class="text-esmerald list-disc pl-5" itemprop="additionalProperty">
                    <li v-for="(feature, featureIndex) in product.features" :key="`feature-${index}-${featureIndex}`" itemprop="value">
                      {{ feature }}
                    </li>
                  </ul>
                </div>
              </div>
              
              <div class="mt-8">
                <button class="px-6 py-3 bg-lemon text-esmerald hover:bg-lemon-dark transition-colors duration-300" @click="showModalEmail = true" itemprop="url">
                  {{ messages.product_section.cta_button }}
                  <span class="sr-only"> - Project App. {{ product.title }}</span>
                </button>
              </div>
            </div>
            
            <!-- Right column (Product image) -->
            <div class="lg:w-6/12 w-full">
              <img :src="product.image" alt="Project App. eCommerce solution" class="w-full h-auto" itemprop="image" />
            </div>
          </div>
        </section>
    
        <!-- Odd-indexed product layout -->
        <section v-else class="mt-32 w-full px-3 bg-esmerald py-16" :aria-labelledby="`product-title-${index}`">
          <div class="max-w-7xl mx-auto sm:px-6 lg:px-8 flex flex-col-reverse lg:flex-row justify-between">
            <!-- Left column (Product image) -->
            <div class="lg:w-6/12 w-full">
              <img :src="product.image" alt="Project App. web development service" class="w-full h-auto" itemprop="image" />
            </div>
            
            <!-- Right column (Product info) -->
            <div class="lg:w-5/12 w-full mb-16 lg:mb-0">
              <h2 :id="`product-title-${index}`" class="text-6xl lg:text-9xl font-light mb-8 text-white" itemprop="name">
                {{ product.title }}
                <span class="sr-only"> - Project App. solution</span>
              </h2>
              <p class="font-regular text-white text-xl mb-8" itemprop="description">
                {{ product.description }}
                <span class="sr-only"> from Project App.</span>
              </p>
              
              <div class="flex flex-col md:flex-row justify-between">
                <!-- Left pricing column -->
                <div class="md:w-5/12 w-full mb-8 md:mb-0">
                  <p class="text-lemon text-5xl lg:text-6xl font-light" itemprop="price">
                    {{ product.price }}
                  </p>
                  <meta itemprop="priceCurrency" content="EUR" />
                  
                  <p v-if="product.price_monthly" class="text-lemon text-xl mt-4">
                    {{ product.price_monthly }}
                  </p>
                </div>
                
                <!-- Right feature list column -->
                <div class="md:w-6/12 w-full">
                  <p class="mb-4 text-xl text-white">
                    {{ messages.product_section.includes }}:
                  </p>
                  <ul class="text-white list-disc pl-5" itemprop="additionalProperty">
                    <li v-for="(feature, featureIndex) in product.features" :key="`feature-${index}-${featureIndex}`" itemprop="value">
                      {{ feature }}
                    </li>
                  </ul>
                </div>
              </div>
              
              <div class="mt-8">
                <button class="px-6 py-3 bg-lemon text-esmerald hover:bg-lemon-dark transition-colors duration-300" @click="showModalEmail = true" itemprop="url">
                  {{ messages.product_section.cta_button }}
                  <span class="sr-only"> - Project App. {{ product.title }}</span>
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Contact Component -->
    <section aria-label="Contact Project App. for e-Commerce Solutions" itemscope itemtype="https://schema.org/ContactPoint">
      <Contact></Contact>
    </section>

    <!-- Footer Component -->
    <footer class="mt-16" itemscope itemtype="https://schema.org/WPFooter">
      <Footer></Footer>
    </footer>

    <!-- Email Modal -->
    <Email :visible="showModalEmail" @update:visible="showModalEmail = $event"></Email>
  </div>
</template>

<script setup>
// Project App. - E-Commerce Solutions and Pricing
// Professional web development services with transparent pricing

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
import Email from "@/components/layouts/Email.vue";

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

// Show Email Modal
const showModalEmail = ref(false);

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
