<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-md"
      role="dialog"
      aria-modal="true"
      aria-labelledby="contact-form-title"
    >
      <div @click="hideModal" class="absolute inset-0" aria-label="Close contact form" role="button" tabindex="0"></div>
      <form
        ref="modalContent"
        @submit.prevent="handleSubmit"
        class="relative z-[1000] w-full max-h-[90vh] rounded-xl bg-window-black bg-opacity-60 backdrop-blur-md md:w-4/5 lg:w-1/2 flex flex-col"
        aria-labelledby="contact-form-title"
      >
        <div
          class="w-full h-10 bg-black rounded-t-xl flex items-center justify-center relative"
        >
          <div class="absolute flex gap-2 left-0 ps-4">
            <button
              @click="hideModal"
              class="w-3 h-3 bg-red-600 rounded-full cursor-pointer"
              aria-label="Close contact form"
            ></button>
            <button
              @click="hideModal"
              class="w-3 h-3 bg-yellow-600 rounded-full cursor-pointer"
              aria-label="Close contact form"
            ></button>
            <button
              @click="hideModal"
              class="w-3 h-3 bg-gray-600 rounded-full cursor-pointer"
              aria-label="Close contact form"
            ></button>
          </div>
        </div>
        
        <div class="flex-1 overflow-auto flex flex-col">
          <div class="h-14 border-b border-b-zinc-400 mx-6 flex items-center flex-wrap">
            <h2 class="font-regular text-white text-lg mr-2">
              {{ globalMessages.to_label }}
            </h2>
            <span
              class="px-4 py-2 bg-window-black bg-opacity-40 rounded-xl backdrop-blur-md text-white"
              >{{ globalMessages.to_value }}</span>
          </div>
          
          <div class="h-14 border-b border-b-zinc-400 mx-6 flex items-center flex-wrap">
            <label for="fullname-input" class="font-regular text-white text-lg w-auto min-w-[5rem]">{{ globalMessages.fullname_label || 'Name' }}</label>
            <input
              id="fullname-input"
              type="text"
              v-model="form.fullName"
              class="ms-4 w-full flex-1 bg-transparent border-none outline-none focus:ring-0 text-white placeholder-white placeholder:text-zinc-400"
              :placeholder="globalMessages.fullname_placeholder || 'Full name'"
              required
            />
          </div>

          <div class="h-14 border-b border-b-zinc-400 mx-6 flex items-center flex-wrap">
            <label for="email-input" class="font-regular text-white text-lg w-auto min-w-[5rem]">{{ globalMessages.from_label }}</label>
            <input
              id="email-input"
              type="email"
              v-model="form.email"
              class="ms-4 w-full flex-1 bg-transparent border-none outline-none focus:ring-0 text-white placeholder-white placeholder:text-zinc-400"
              :placeholder="globalMessages.email_placeholder"
              required
            />
          </div>
          
          <div class="h-14 border-b border-b-zinc-400 mx-6 flex items-center flex-wrap">
            <label for="phone-input" class="font-regular text-white text-lg w-auto min-w-[5rem]">{{ globalMessages.phone_label || 'Phone' }}</label>
            <input
              id="phone-input"
              type="tel"
              v-model="form.phone"
              class="ms-4 w-full flex-1 bg-transparent border-none outline-none focus:ring-0 text-white placeholder-white placeholder:text-zinc-400"
              :placeholder="globalMessages.phone_placeholder || 'Phone number'"
            />
          </div>

          <div class="mx-6 flex-1 min-h-[150px] my-4">
            <label for="message-input" class="sr-only">Message</label>
            <textarea
              id="message-input"
              v-model="form.project"
              class="w-full h-full min-h-[120px] bg-transparent border-none outline-none focus:ring-0 text-white resize-none placeholder-white"
              :placeholder="globalMessages.message_placeholder"
              required
            ></textarea>
          </div>

          <div class="mx-6 mb-4">
            <label class="font-regular text-zinc-400 text-sm mb-3 block">{{ globalMessages.budget_label || 'Budget (USD)' }}</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="option in budgetOptions"
                :key="option"
                type="button"
                @click="form.budget = option"
                :class="[
                  'px-4 py-2 text-sm rounded-xl border border-zinc-600 transition-all duration-200 cursor-pointer',
                  form.budget === option
                    ? 'bg-accent-soft text-text-brand border-lemon'
                    : 'bg-transparent text-zinc-300 hover:border-zinc-400'
                ]"
              >
                {{ option }}
              </button>
            </div>
          </div>
        </div>

        <div
          class="border-t border-t-zinc-400 flex items-center justify-end p-4"
        >
          <button
            id="form-submit-btn"
            :disabled="!isFormValid"
            :class="{
              'bg-accent-soft text-text-brand': isFormValid,
              'bg-zinc-400 text-white': !isFormValid,
            }"
            type="submit"
            class="px-6 py-3 rounded-xl text-sm md:text-base md:px-8 md:py-3"
            aria-label="Send message to our web development team"
          >
            {{ globalMessages.send_button }}
            <span class="sr-only">Submit your contact information and message to our web design team</span>
          </button>
        </div>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from "vue";
import { storeToRefs } from 'pinia';
import { gsap } from "gsap";
import { useGlobalMessages } from '~/composables/useMessages';
import { useLanguageStore } from '~/stores/language';
import { useContactsStore } from '~/stores/contacts';
import { useGtagConversions } from '~/composables/useGtagConversions';

const { globalMessages } = useGlobalMessages('email_contact');
const router = useRouter();
const languageStore = useLanguageStore();
const { currentLocale } = storeToRefs(languageStore);
const contactsStore = useContactsStore();
const { isSubmitting } = storeToRefs(contactsStore);
const { trackFormSubmission } = useGtagConversions();

// Props passed to the component
const props = defineProps({
  visible: Boolean,
});

// Emit event to notify parent component about visibility changes
const emit = defineEmits(["update:visible"]);

// Refs for the modal elements and form data
const modalContent = ref(null);

// Reactive form data
const form = ref({
  fullName: "",
  email: "",
  phone: "",
  project: "",
  budget: ""
});

const budgetOptions = ['500-5K', '5-10K', '10-20K', '20-30K', '>30K'];

// Computed property to validate the email format using a regular expression
const isEmailValid = computed(() => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(form.value.email);
});

// Computed property to validate the entire form
const isFormValid = computed(() => {
  return (
    form.value.fullName &&
    form.value.email &&
    isEmailValid.value &&
    form.value.project
  );
});

// Function to hide the modal with a GSAP animation
const hideModal = () => {
  gsap.to(modalContent.value, {
    opacity: 0,
    y: -50,
    duration: 0.5,
    onComplete: () => {
      document.body.style.overflow = '';
      emit("update:visible", false);
    },
  });
};

// Function to animate the modal in when it becomes visible
const animateModalIn = () => {
  gsap.fromTo(
    modalContent.value,
    { opacity: 0, y: -50 },
    { opacity: 1, y: 0, duration: 0.5 }
  );
};

// Function to handle form submission
const handleSubmit = async () => {
  if (isFormValid.value) {
    // Cerrar el teclado virtual en dispositivos móviles
    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur();
    }
    
    const result = await contactsStore.sendContact(form.value);
    
    if (result.success) {
      trackFormSubmission();
      if (typeof window !== 'undefined' && window.fbq) {
        window.fbq('track', 'Contact');
      }
      hideModal();
      const successRoute = currentLocale.value 
        ? `/${currentLocale.value}/contact-success` 
        : '/contact-success';
      
      setTimeout(() => {
        router.push(successRoute);
      }, 600);
    }
  }
};

// Watcher that triggers the modal animation when its visibility changes
watch(
  () => props.visible,
  async (newVal) => {
    if (newVal) {
      await nextTick();
      document.body.style.overflow = 'hidden';
      animateModalIn();
    }
  }
);
</script>