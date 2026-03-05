<template>
  <section ref="sectionRef" class="proposal-closing h-full w-full bg-white flex items-center">
    <div class="w-full px-6 md:px-12 lg:px-24">
      <div class="max-w-4xl mx-auto text-center">
        <!-- Validity notice -->
        <div v-if="validityMessage" data-animate="fade-up" class="validity-notice bg-yellow-50 border-2 border-yellow-200 p-6 rounded-xl mb-10 text-left">
          <div class="flex items-start">
            <svg class="w-6 h-6 text-yellow-600 mr-3 flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
            </svg>
            <div>
              <h4 class="font-bold text-gray-900 mb-1">Validez de la Propuesta</h4>
              <p class="text-sm text-gray-600">{{ validityMessage }}</p>
            </div>
          </div>
        </div>

        <!-- Thank you message -->
        <div v-if="thankYouMessage" data-animate="fade-up" class="mb-12">
          <h3 class="text-3xl font-bold text-gray-900 mb-4">¡Gracias por tu Tiempo!</h3>
          <p class="text-lg text-gray-600 max-w-2xl mx-auto">{{ thankYouMessage }}</p>
        </div>

        <!-- Accept / Reject buttons -->
        <div v-if="canRespond" data-animate="scale-in" class="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <button
            class="px-8 py-4 bg-emerald-600 text-white rounded-xl font-medium text-base
                   hover:bg-emerald-700 transition-colors shadow-lg flex items-center gap-2"
            :disabled="isSubmitting"
            @click="$emit('accept')"
          >
            <span>✅</span> Acepto la propuesta
          </button>
          <button
            class="px-8 py-4 bg-white text-gray-600 rounded-xl font-medium text-base
                   border-2 border-gray-200 hover:bg-gray-50 hover:text-red-600 hover:border-red-200
                   transition-colors flex items-center gap-2"
            :disabled="isSubmitting"
            @click="$emit('reject')"
          >
            <span>❌</span> Rechazar propuesta
          </button>
        </div>

        <!-- Already responded -->
        <div v-if="proposal?.status === 'accepted'" data-animate="fade-up" class="py-8">
          <div class="text-5xl mb-4">🎉</div>
          <p class="text-xl font-bold text-emerald-600">¡Propuesta aceptada!</p>
          <p class="text-gray-500 mt-2">Nos pondremos en contacto contigo pronto.</p>
        </div>
        <div v-else-if="proposal?.status === 'rejected'" data-animate="fade-up" class="py-8">
          <p class="text-lg text-gray-500">Propuesta rechazada. Gracias por tu tiempo.</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useSectionAnimations } from '~/composables/useSectionAnimations';

const sectionRef = ref(null);
useSectionAnimations(sectionRef);

const props = defineProps({
  proposal: { type: Object, default: null },
  validityMessage: { type: String, default: '' },
  thankYouMessage: { type: String, default: '' },
  isSubmitting: { type: Boolean, default: false },
});

defineEmits(['accept', 'reject']);

const canRespond = computed(() => {
  const s = props.proposal?.status;
  return s === 'sent' || s === 'viewed';
});
</script>
