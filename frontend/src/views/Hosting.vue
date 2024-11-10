<template>
  <div class="bg-esmerald">
    <div class="fixed top-0 left-0 w-full z-50">
      <Navbar></Navbar>
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
              :class="[index === 2 ? 'ring-2 ring-lemon bg-lemon' : 'ring-1 ring-esmerald-light bg-esmerald-light', 'rounded-xl p-8']"
            >
              <h3 class="text-2xl font-LIGHT leading-8 text-esmerald">
                {{ hosting.title }}
              </h3>
              <p class="mt-4 text-md font-regular leading-6 text-esmerald">
                {{ hosting.description }}
              </p>
              <p class="mt-6 flex items-baseline gap-x-1">
                <span class="text-4xl font-medium tracking-tight text-esmerald">
                  {{ frequency.value === "monthly" ? hosting.monthly_price : hosting.annual_price }}
                </span>
                <span class="text-sm font-semibold leading-6 text-gray-600">
                  {{ frequency.priceSuffix }}
                </span>
              </p>
              <a
                :href="hosting.href"
                class="mt-6 block rounded-md px-3 py-2 text-center text-sm font-semibold leading-6 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
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
  </div>
</template>

<script setup>
import Navbar from "@/components/layouts/Navbar.vue";
import Footer from "@/components/layouts/Footer.vue";
import Contact from "@/components/layouts/Contact.vue";
import { Vue3Marquee } from "vue3-marquee";
import { ref, onMounted } from "vue";
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
import FooterMobile from '@/components/layouts/FooterMobile.vue';

const { messages } = useMessages();
const hostingStore = useHostingStore();
const hostings = ref([]);

// Define the selected frequency
const frequency = ref(messages.value.frequencies[0]);

const hostingBenefits = [
  { icon: CodeBracketIcon },
  { icon: ServerIcon },
  { icon: CheckCircleIcon },
  { icon: ShieldCheckIcon },
  { icon: ArrowTrendingUpIcon },
  { icon: UsersIcon },
];

onMounted(async () => {
  await hostingStore.init();
  hostings.value = hostingStore.getHostings;
});
</script>

