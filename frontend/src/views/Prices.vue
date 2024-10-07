<template>
  <div class="bg-esmerald-light">
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar></Navbar>
    </div>
    <div class="h-32"></div>
    <section>
      <h1 class="text-center font-light text-6xl text-esmerald lg:text-8xl">
        We don't use WordPress
        <br />
        We are real programmers
      </h1>
    </section>
    <Wordpress></Wordpress>
    
    <!-- Products -->
    <div v-for="(product, index) in products" :key="index">
      <section v-if="index % 2 === 0" class="mt-32 w-full px-3">
        <h2 class="text-esmerald text-4xl font-light lg:text-6xl">
          {{ product.title }}
        </h2>
        <div class="grid mt-6 lg:grid-cols-3">
          <div
            class="bg-esmerald rounded-b-xl p-6 grid order-2 gap-2 md:grid-cols-2 lg:rounded-r-none lg:rounded-l-xl lg:col-span-2 lg:order-1"
          >
            <div class="grid gap-3 mt-6 order-2 lg:mt-0 lg:order-1">
              <div v-for="category in product.categories">
                <h3 class="text-xl text-white font-light">{{ category.name }}</h3>
                <ul class="font-regular text-lg text-green-light ps-6">
                  <li v-for="item in category.items" class="flex items-center gap-2">
                    <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon
                    >{{ item.name }}
                  </li>
                </ul>
              </div>
            </div>
            <div class="border-l border-l-green-light ps-4 order-1 lg:order-2">
              <p class="text-lg text-green-light font-regular whitespace-pre-line">
                {{ product.description }}
              </p>
              <br />
              <p class="text-md font-regular text-white flex gap-2">
                <BanknotesIcon class="w-6 h-6 text-lemon"></BanknotesIcon> $
                {{ product.price }} COP
              </p>
              <p class="text-md font-regular text-white flex gap-2 mt-2">
                <ClockIcon class="w-6 h-6 text-lemon"></ClockIcon> {{ product.development_time }}
              </p>
            </div>
          </div>
          <div class="flex justify-center items-center order-1 lg:order-2">
            <img
              :src="product.image"
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
                  $ {{ product.price }} COP
                  <BanknotesIcon class="w-6 h-6 text-lemon"></BanknotesIcon> 
              </p>
              <p
                class="text-md font-regular text-white flex gap-2 mt-2 justify-end"
              >
              {{ product.development_time }} <ClockIcon class="w-6 h-6 text-lemon"></ClockIcon>
              </p>
            </div>
            <div class="grid text-end mt-6 lg:mt-0">
              <div v-for="category in product.categories">
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
import {
  BanknotesIcon,
  CheckBadgeIcon,
  ClockIcon,
} from "@heroicons/vue/24/outline";
import { useProductStore } from "@/stores/products";
import { onMounted, ref } from "vue";

const products = ref([]);

const productStore = useProductStore();

onMounted(async () => {
  await productStore.init();
  products.value = productStore.getProducts;
  console.log(products.value)
})
</script>