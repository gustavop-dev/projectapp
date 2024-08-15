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
          Get in touch
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
          To
          <span
            class="px-4 py-2 bg-window-black bg-opacity-40 rounded-xl backdrop-blur-md"
            >Project App</span
          >
          (hello@proejctapp.co)
        </h2>
      </div>
      <div class="h-14 border-b border-b-zinc-400 mx-6 flex items-center">
        <label class="font-regular text-white text-lg">From</label>
        <input
          type="email"
          v-model="form.email"
          class="ms-4 w-full bg-transparent border-none outline-none focus:ring-0 text-white placeholder-white placeholder:text-zinc-400"
          placeholder="Email"
          required
        />
      </div>
      <div class="h-14 border-b border-b-zinc-400 mx-6 flex items-center">
        <label class="font-regular text-white text-lg">Subject</label>
        <input
          type="text"
          v-model="form.subject"
          class="ms-4 w-full bg-transparent border-none outline-none focus:ring-0 text-white placeholder-white placeholder:text-zinc-400"
          placeholder="Give your idea a title"
          required
        />
      </div>
      <div class="mx-6 h-1/2">
        <textarea
          v-model="form.message"
          class="mt-4 w-full h-full bg-transparent border-none outline-none focus:ring-0 text-white resize-none"
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
          Send
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from "vue";
import { gsap } from "gsap";
import { submitHandler } from "@/shared/submit_handler.js";

const props = defineProps({
  visible: Boolean,
});

const emit = defineEmits(["update:visible"]);
const modalContainer = ref(null);
const modalContent = ref(null);

const form = ref({
  email: "",
  subject: "",
  message: "",
});

const isEmailValid = computed(() => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(form.value.email);
});

const isFormValid = computed(() => {
  return (
    form.value.email &&
    isEmailValid.value &&
    form.value.subject &&
    form.value.message
  );
});

const hideModal = () => {
  gsap.to(modalContent.value, {
    opacity: 0,
    y: -50,
    duration: 0.5,
    onComplete: () => emit("update:visible", false),
  });
};

const animateModalIn = () => {
  gsap.fromTo(
    modalContent.value,
    { opacity: 0, y: -50 },
    { opacity: 1, y: 0, duration: 0.5 }
  );
};

const handleSubmit = async () => {
  if (isFormValid.value) {
    const response = await submitHandler(form.value);
    if (response && response.status === 201) {
      hideModal();
    }
  }
};

watch(
  () => props.visible,
  async (newVal) => {
    if (newVal) {
      await nextTick();
      animateModalIn();
    }
  }
);
</script>
