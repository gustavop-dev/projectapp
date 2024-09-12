<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-md"
  >
    <div @click="hideModal" class="absolute inset-0"></div>
    <form
      ref="modalContent"
      @submit.prevent="handleSubmit"
      class="relative z-50 h-4/5 rounded-xl bg-window-black bg-opacity-60 backdrop-blur-md md:w-4/5 lg:w-1/2 lg:h-2/3 "
    >
      <div
        class="w-full h-10 bg-black rounded-t-xl flex items-center justify-center"
      >
        <h1 class="text-white font-regular text-md inline-block">
          {{ globalMessages.get_in_touch }}
        </h1>
        <div class="absolute flex gap-2 left-0 ps-4">
          <div
            @click="hideModal"
            class="w-3 h-3 bg-red-600 rounded-full cursor-pointer"
          ></div>
          <div
            @click="hideModal"
            class="w-3 h-3 bg-yellow-600 rounded-full cursor-pointer"
          ></div>
          <div
            @click="hideModal"
            class="w-3 h-3 bg-gray-600 rounded-full cursor-pointer"
          ></div>
        </div>
      </div>
      <div class="h-14 border-b border-b-zinc-400 mx-6 flex items-center">
        <h2 class="font-regular text-white text-lg">
          {{ globalMessages.to_label }}
          <span
            class="px-4 py-2 bg-window-black bg-opacity-40 rounded-xl backdrop-blur-md"
            >{{ globalMessages.to_value }}</span
          >
        </h2>
      </div>
      <div class="h-14 border-b border-b-zinc-400 mx-6 flex items-center">
        <label class="font-regular text-white text-lg">{{ globalMessages.from_label }}</label>
        <input
          type="email"
          v-model="form.email"
          class="ms-4 w-full bg-transparent border-none outline-none focus:ring-0 text-white placeholder-white placeholder:text-zinc-400"
          :placeholder="globalMessages.email_placeholder"
          required
        />
      </div>
      <div class="h-14 border-b border-b-zinc-400 mx-6 flex items-center">
        <label class="font-regular text-white text-lg">{{ globalMessages.subject_label }}</label>
        <input
          type="text"
          v-model="form.subject"
          class="ms-4 w-full bg-transparent border-none outline-none focus:ring-0 text-white placeholder-white placeholder:text-zinc-400"
          :placeholder="globalMessages.subject_placeholder"
          required
        />
      </div>
      <div class="mx-6 h-1/2">
        <textarea
          v-model="form.message"
          class="mt-4 w-full h-full bg-transparent border-none outline-none focus:ring-0 text-white resize-none placeholder-white"
          :placeholder="globalMessages.message_placeholder"
          required
        ></textarea>
      </div>
      <div
        class="h-14 border-t border-t-zinc-400 flex items-center justify-end"
      >
        <button
          :disabled="!isFormValid"
          :class="{
            'bg-lemon text-esmerald': isFormValid,
            'bg-zinc-400 text-white': !isFormValid,
          }"
          type="submit"
          class="mt-12 mx-6 px-8 py-4 rounded-xl"
        >
          {{ globalMessages.send_button }}
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
const modalContainer = ref(null); // Reference for the modal container
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