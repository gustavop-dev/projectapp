<template>
  <section class="mt-32 w-full px-3">
    <!-- Product title with conditional alignment -->
    <h2 :class="[
      'text-esmerald text-4xl font-light lg:text-6xl',
      index % 2 !== 0 ? 'text-end' : ''
    ]">
      {{ source.title }}
    </h2>
    
    <!-- Product layout with conditional grid order -->
    <div class="grid mt-6 lg:grid-cols-3">
      <!-- Product details box -->
      <div :class="[
        'bg-esmerald rounded-b-xl p-6 grid order-2 gap-2 md:grid-cols-2',
        index % 2 === 0 
          ? 'lg:rounded-r-none lg:rounded-l-xl lg:col-span-2 lg:order-1' 
          : 'lg:rounded-l-none lg:rounded-r-xl lg:col-span-2 lg:order-2'
      ]">
        <!-- Product categories section with conditional order -->
        <div :class="[
          'grid gap-3 mt-6 order-2 lg:mt-0',
          index % 2 === 0 ? 'lg:order-1' : 'lg:order-2'
        ]" v-if="source.categories && source.categories.length">
          <div v-for="(category, catIndex) in source.categories" :key="catIndex">
            <h3 class="text-xl text-white font-light">{{ category.name }}</h3>
            <ul class="font-regular text-lg text-green-light ps-6">
              <li v-for="(item, itemIndex) in (category.items || [])" :key="itemIndex" class="flex items-center gap-2">
                <CheckBadgeIcon class="text-lemon w-6 h-6"></CheckBadgeIcon>
                {{ item.name }}
              </li>
            </ul>
          </div>
        </div>
        
        <!-- Product description section with conditional border and alignment -->
        <div :class="[
          'space-y-2 order-1',
          index % 2 === 0 
            ? 'border-l border-l-green-light ps-4 lg:order-2' 
            : 'border-r border-r-green-light pe-4'
        ]">
          <!-- Product description -->
          <p :class="[
            'text-lg text-green-light font-regular whitespace-pre-line',
            index % 2 !== 0 ? 'text-end' : ''
          ]">
            {{ source.description }}
          </p>
          <br />
          
          <!-- Call to action button -->
          <button @click="$emit('modal-show')" class="w-full flex justify-center items-center px-4 py-2 bg-lemon rounded-xl">
            <span class="font-regular text-esmerald text-md">
              {{ messages.product_details.call_to_action }}
            </span>
          </button>
          <br />
          
          <!-- Product options with checkboxes -->
          <div class="space-y-3">
            <!-- Animations option -->
            <div class="flex items-center">
              <input 
                :id="`animations-${index}`" 
                v-model="productStates[index].animationChecked" 
                type="checkbox" 
                class="cursor-pointer w-4 h-4 rounded border-lemon bg-esmerald checked:border-lemon checked:bg-lemon"
              />
              <label :for="`animations-${index}`" class="ml-2 text-md font-regular text-white cursor-pointer">
                {{ messages.product_details.animations.title }}
              </label>
            </div>
            
            <!-- Mobile App option -->
            <div class="flex items-center">
              <input 
                :id="`mobile-app-${index}`" 
                v-model="productStates[index].mobileAppChecked" 
                type="checkbox" 
                class="cursor-pointer w-4 h-4 rounded border-lemon bg-esmerald checked:border-lemon checked:bg-lemon"
              />
              <label :for="`mobile-app-${index}`" class="ml-2 text-md font-regular text-white cursor-pointer">
                {{ messages.product_details.mobile_app.title }}
              </label>
            </div>
          </div>
          
          <!-- Price and details section -->
          <div class="flex flex-col gap-2 mt-4">
            <p class="text-md font-regular text-white flex gap-2 items-center">
              <BanknotesIcon class="w-6 h-6 text-lemon"></BanknotesIcon> 
              {{ messages.product_details?.price_label || '$' }} {{ formatPrice(calculateTotalPrice(source, productStates[index])) }} {{ languageStore.currentLanguage === 'en' ? 'USD' : 'COP' }}
            </p>
            
            <p class="text-md font-regular text-white flex gap-2 mt-2">
              <ClockIcon class="w-6 h-6 text-lemon"></ClockIcon> {{ source.development_time }}
            </p>
            
            <router-link 
              v-if="source.hosting_name" 
              :to="{name: 'hosting', params: { plan: `hosting_plan_${source.hosting_id || '1'}` }}"
              class="text-md font-regular text-white flex gap-2 mt-2 cursor-pointer"
            >
              <ServerStackIcon class="w-6 h-6 text-lemon"></ServerStackIcon>
              <p class="py-px px-3 bg-lemon text-esmerald rounded-xl">
                <span>{{ messages.product_details.server }} ~ </span> 
                <span class="italic">{{ source.hosting_name }}</span>
              </p>
            </router-link>
          </div>
        </div>
      </div>
      
      <!-- Product image -->
      <div :class="[
        'flex justify-center items-center',
        index % 2 === 0 ? 'order-1 lg:order-2' : ''
      ]">
        <img
          :src="source.image"
          loading="lazy"
          decoding="async"
          :alt="source.title"
          fetchpriority="low"
          width="800"
          height="600"
          :class="[
            'w-full h-full object-cover',
            index % 2 === 0 
              ? 'rounded-t-xl lg:rounded-l-none lg:rounded-r-xl' 
              : 'rounded-t-xl lg:rounded-r-none lg:rounded-l-xl'
          ]"
        />
      </div>
    </div>
  </section>
</template>

<script setup>
import { BanknotesIcon, ClockIcon, ServerStackIcon, CheckBadgeIcon } from '@heroicons/vue/24/outline';

// Props definition
defineProps({
  source: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    required: true
  },
  productStates: {
    type: Object,
    required: true
  },
  messages: {
    type: Object,
    required: true
  },
  languageStore: {
    type: Object,
    required: true
  },
  calculateTotalPrice: {
    type: Function,
    required: true
  },
  formatPrice: {
    type: Function,
    required: true
  }
});

// Emits
defineEmits(['modal-show']);
</script>

<style scoped>
section {
  contain: content;
}

@media (prefers-reduced-motion: no-preference) {
  img {
    transition: transform 0.3s ease-in-out;
  }
  
  img:hover {
    transform: scale(1.02);
  }
}
</style> 