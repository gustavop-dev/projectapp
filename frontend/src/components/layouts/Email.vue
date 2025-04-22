<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-md"
    role="dialog"
    aria-modal="true"
    aria-labelledby="contact-form-title"
  >
    <div @click="hideModal" class="absolute inset-0" aria-label="Close contact form" role="button" tabindex="0"></div>
    <form
      ref="modalContent"
      @submit.prevent="handleSubmit"
      class="relative z-50 w-full max-h-[90vh] rounded-xl bg-window-black bg-opacity-60 backdrop-blur-md md:w-4/5 lg:w-1/2 flex flex-col"
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
        <h1 id="contact-form-title" class="text-white font-regular text-md">
          {{ globalMessages.get_in_touch }}
        </h1>
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
          <label for="email-input" class="font-regular text-white text-lg w-auto min-w-[3rem]">{{ globalMessages.from_label }}</label>
          <input
            id="email-input"
            type="email"
            v-model="form.email"
            class="ms-4 w-full flex-1 bg-transparent border-none outline-none focus:ring-0 text-white placeholder-white placeholder:text-zinc-400"
            :placeholder="globalMessages.email_placeholder"
            required
            aria-required="true"
            aria-invalid="false"
            aria-describedby="email-description"
          />
          <span id="email-description" class="sr-only">Enter your email address so we can respond to your inquiry</span>
        </div>
        
        <div class="h-14 border-b border-b-zinc-400 mx-6 flex items-center flex-wrap">
          <label for="subject-input" class="font-regular text-white text-lg w-auto min-w-[4rem]">{{ globalMessages.subject_label }}</label>
          <input
            id="subject-input"
            type="text"
            v-model="form.subject"
            class="ms-4 w-full flex-1 bg-transparent border-none outline-none focus:ring-0 text-white placeholder-white placeholder:text-zinc-400"
            :placeholder="globalMessages.subject_placeholder"
            required
            aria-required="true"
            aria-invalid="false"
            aria-describedby="subject-description"
          />
          <span id="subject-description" class="sr-only">Enter the subject of your message related to web design or development</span>
        </div>
        
        <div class="mx-6 flex-1 min-h-[200px] my-4">
          <label for="message-input" class="sr-only">Message</label>
          <textarea
            id="message-input"
            v-model="form.message"
            class="w-full h-full min-h-[150px] bg-transparent border-none outline-none focus:ring-0 text-white resize-none placeholder-white"
            :placeholder="globalMessages.message_placeholder"
            required
            aria-required="true"
            aria-invalid="false"
            aria-describedby="message-description"
          ></textarea>
          <span id="message-description" class="sr-only">Describe your website design or development needs in detail</span>
        </div>
      </div>

      <div
        class="border-t border-t-zinc-400 flex items-center justify-end p-4"
      >
        <button
          id="form-submit-btn"
          :disabled="!isFormValid"
          :class="{
            'bg-lemon text-esmerald': isFormValid,
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
</template>

<script setup>
import { ref, computed, watch, nextTick } from "vue"; // Import Vue utilities
import { gsap } from "gsap"; // Import GSAP for animations
import { submitHandler } from "@/shared/submit_handler.js"; // Import the submit handler for form submission
import { useGlobalMessages } from '@/composables/useMessages'; // Import the custom composable to get global messages

const { globalMessages } = useGlobalMessages('email_contact'); // Get global messages for the email contact form

// Props passed to the component
const props = defineProps({
  visible: Boolean, // Controls the visibility of the modal
});

// Emit event to notify parent component about visibility changes
const emit = defineEmits(["update:visible"]);

// Refs for the modal elements and form data
const modalContent = ref(null); // Reference for the modal content

// Reactive form data
const form = ref({
  email: "",
  subject: "",
  message: "",
});

// Computed property to validate the email format using a regular expression
const isEmailValid = computed(() => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(form.value.email);
});

// Computed property to validate the entire form
const isFormValid = computed(() => {
  return (
    form.value.email &&
    isEmailValid.value &&
    form.value.subject &&
    form.value.message
  );
});

// Function to hide the modal with a GSAP animation
const hideModal = () => {
  gsap.to(modalContent.value, {
    opacity: 0,
    y: -50,
    duration: 0.5,
    onComplete: () => emit("update:visible", false), // Emit event to hide the modal
  });
};

// Function to animate the modal in when it becomes visible
const animateModalIn = () => {
  gsap.fromTo(
    modalContent.value,
    { opacity: 0, y: -50 }, // Start with the modal off-screen and transparent
    { opacity: 1, y: 0, duration: 0.5 } // Animate the modal sliding into view
  );
};

// Function to handle form submission
const handleSubmit = async () => {
  if (isFormValid.value) { // Check if the form is valid before submitting
    const response = await submitHandler(form.value); // Submit the form using the handler
    if (response && response.status === 201) {
      hideModal(); // Hide the modal if the form submission is successful
    }
  }
};

// Watcher that triggers the modal animation when its visibility changes
watch(
  () => props.visible, // Watch the visibility prop
  async (newVal) => {
    if (newVal) { // If the modal is visible
      await nextTick(); // Wait for the DOM to update
      animateModalIn(); // Animate the modal into view
    }
  }
);
</script>