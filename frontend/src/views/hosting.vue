<template>
    <div class="bg-esmerald"> 
        <div class="fixed top-0 left-0 w-full z-50">
            <Navbar></Navbar>
        </div>
        <section class="pt-32">
          <h1 class="text-center font-light text-6xl text-lemon lg:text-8xl">
            Exclusive Hosting, Exclusive Performance
            <br />
            Not Shared, Just Superior
          </h1>
        </section>
        <section class="p-3 mt-32 grid md:grid-cols-2 gap-16 max-w-7xl mx-auto">
          <h2 class="text-4xl text-esmerald-light font-light lg:text-6xl">
            Our Hosting Stands Out
            <br>
            Experience the Difference of Dedicated Hosting
          </h2>
          <p class="font-regular text-lg text-esmerald-light">
            At Project App, we understand the importance of reliable and high-performing hosting for web applications developed with custom code. That's why our dedicated hosting solutions are tailored to meet the needs of professional developers and businesses seeking top-notch performance and security.
          </p>
        </section>
        <section class="mt-16">
          <Vue3Marquee :pause-on-hover="true" direction="reverse" duration="35">
            <div class="w-72 h-full mx-auto px-4" v-for="reason in hostingBenefits">
              <div class="bg-esmerald-light rounded-xl relative h-full">
                <component :is="reason.icon" class="w-16 h-16 text-esmerald text-center p-4"></component>
                <p class="text-esmerald m-4 font-regular">{{ reason.text }}</p>
               </div>
            </div>
          </Vue3Marquee>
        </section>
        <section>
          <div class="py-24 sm:py-32 px-3">
            <div class="mx-auto max-w-max px-6 lg:px-8">
              <div class="grid justify-end">
                <div class="max-w-4xl text-end">
                  <h2 class="mt-2 text-4xl font-light text-lemon sm:text-6xl">Pricing plans for teams of&nbsp;all&nbsp;sizes</h2>
                </div>
                <div class="flex justify-end">
                  <p class="mt-6 max-w-2xl text-end text-lg leading-8 text-esmerald-light">
                    Choose an affordable plan that’s packed with the best features for engaging your audience, creating customer loyalty, and driving sales.
                  </p>
                </div>
                <div class="mt-16 flex justify-end">
                  <fieldset aria-label="Payment frequency">
                    <RadioGroup 
                      v-model="frequency" 
                      class="grid grid-cols-2 gap-x-1 rounded-full p-1 text-center text-sm font-regular leading-5 ring-1 ring-inset ring-esmerald-light bg-window-black bg-opacity-40 backdrop-blur-md"
                      >
                      <RadioGroupOption as="template" v-for="option in frequencies" :key="option.value" :value="option" v-slot="{ checked }">
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
              <div class="isolate mx-auto mt-10 grid max-w-md grid-cols-1 gap-8 md:max-w-2xl md:grid-cols-2 lg:max-w-4xl xl:mx-0 xl:max-w-none xl:grid-cols-4">
                <div 
                  v-for="tier in tiers" 
                  :key="tier.id" 
                    Q:class="[tier.mostPopular ? 'ring-2 ring-lemon bg-lemon' : 'ring-1 ring-esmerald-light bg-esmerald-light', 'rounded-xl p-8']">
                  <h3 :id="tier.id" class="text-2xl font-LIGHT leading-8 text-esmerald">
                    {{ tier.name }}
                  </h3>
                  <p class="mt-4 text-md font-regular leading-6 text-esmerald">
                    {{ tier.description }}
                  </p>
                  <p class="mt-6 flex items-baseline gap-x-1">
                    <span class="text-4xl font-medium tracking-tight text-esmerald">
                      {{ tier.price[frequency.value] }}
                    </span>
                    <span class="text-sm font-semibold leading-6 text-gray-600">
                      {{ frequency.priceSuffix }}
                    </span>
                  </p>
                  <a 
                    :href="tier.href" 
                    :aria-describedby="tier.id" 
                    :class="[tier.mostPopular ? 'bg-esmerald-light text-esmerald shadow-sm' : 'bg-lemon text-esmerald ring-indigo-200 hover:ring-indigo-300', 'mt-6 block rounded-md px-3 py-2 text-center text-sm font-semibold leading-6 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2']"
                    >
                    Contact Sales
                  </a>
                  <ul role="list" class="mt-8 space-y-3 text-sm leading-6 text-gray-600">
                    <li v-for="feature in tier.features" :key="feature" class="flex gap-x-3">
                      <CheckIcon class="h-6 w-5 flex-none text-esmerald" aria-hidden="true" />
                      {{ feature }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>
        <div class="p-3 bg-white">
          <Contact></Contact>
          <div class="mt-6">
            <Footer></Footer>
          </div>
        </div>
    </div>
</template>
<script setup>
import Navbar from '@/components/layouts/Navbar.vue';
import Footer from '@/components/layouts/Footer.vue';
import Contact from '@/components/layouts/Contact.vue';
import { Vue3Marquee } from 'vue3-marquee';
import { ref } from 'vue';
import { RadioGroup, RadioGroupOption } from '@headlessui/vue';
import { CheckIcon } from '@heroicons/vue/20/solid';
import { CheckCircleIcon, ServerIcon, ShieldCheckIcon, ArrowTrendingUpIcon, UsersIcon, CodeBracketIcon } from '@heroicons/vue/24/outline';

const frequencies = [
  { value: 'SemiAnnually', label: 'Semi-Annually', priceSuffix: '/COP Semi-Annually' },
  { value: 'annually', label: 'Annually', priceSuffix: '/COP year' },
]
const tiers = [
  {
    name: 'E-Commerce Landing Page V1.0',
    id: 'tier-hobby',
    href: '#',
    price: { SemiAnnually: '$84,000', annually: '$144,000' },
    description: 'The essentials to provide your best work for clients.',
    features: ['5 products', 'Up to 1,000 subscribers', 'Basic analytics'],
    mostPopular: false,
  },
  {
    name: 'E-Commerce Standard V2.0',
    id: 'tier-freelancer',
    href: '#',
    price: { SemiAnnually: '$168,000', annually: '$288,000' },
    description: 'The essentials to provide your best work for clients.',
    features: ['5 products', 'Up to 1,000 subscribers', 'Basic analytics', '48-hour support response time'],
    mostPopular: false,
  },
  {
    name: 'E-Commerce Premium V3.0',
    id: 'tier-startup',
    href: '#',
    price: { SemiAnnually: '$268,800', annually: '$460,800' },
    description: 'A plan that scales with your rapidly growing business.',
    features: [
      '25 products',
      'Up to 10,000 subscribers',
      'Advanced analytics',
      '24-hour support response time',
      'Marketing automations',
    ],
    mostPopular: true,
  },
  {
    name: 'E-Commerce Gold V4.0',
    id: 'tier-enterprise',
    href: '#',
    price: { SemiAnnually: '$349,440', annually: '$599,000' },
    description: 'Dedicated support and infrastructure for your company.',
    features: [
      'Unlimited products',
      'Unlimited subscribers',
      'Advanced analytics',
      '1-hour, dedicated support response time',
      'Marketing automations',
      'Custom reporting tools',
    ],
    mostPopular: false,
  },
]

const frequency = ref(frequencies[0])

const hostingBenefits = [
  {
    icon: CodeBracketIcon,
    text: "Tailored for Code-Based Applications: Optimized for websites and applications developed from scratch, ensuring seamless integration and superior performance."
  },
  {
    icon: ServerIcon,
    text: "Exclusive Resources: Enjoy the benefits of dedicated bandwidth, storage, and processing power, without the limitations of shared hosting."
  },
  {
    icon: CheckCircleIcon,
    text: "Unmatched Performance: Our hosting solutions are designed to deliver fast load times and consistent reliability, crucial for the success of your web applications."
  },
  {
    icon: ShieldCheckIcon,
    text: "Enhanced Security: Protect your applications with our robust security measures, providing peace of mind against potential threats."
  },
  {
    icon: ArrowTrendingUpIcon,
    text: "Scalability: Easily scale your hosting resources as your business and application demands grow."
  },
  {
    icon: UsersIcon,
    text: "Expert Support: Our team of experienced professionals is always ready to assist you with any technical issues or questions."
  }
];
</script>