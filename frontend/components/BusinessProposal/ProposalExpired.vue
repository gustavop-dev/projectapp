<template>
  <section class="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-white px-6">
    <div class="max-w-lg text-center">
      <div class="w-20 h-20 mx-auto mb-8 rounded-full bg-yellow-100 flex items-center justify-center">
        <svg class="w-10 h-10 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>

      <h1 class="text-3xl md:text-4xl font-light text-gray-900 mb-4">
        {{ clientName ? `${clientName}, esta` : 'Esta' }} propuesta ha expirado
      </h1>

      <p class="text-gray-500 text-lg mb-4 leading-relaxed">
        La propuesta <strong v-if="proposalTitle" class="text-gray-700">"{{ proposalTitle }}"</strong>
        ya no está vigente, pero podemos reactivarla o preparar una versión actualizada.
      </p>

      <p class="text-gray-400 text-sm mb-10">
        Escríbenos y en menos de 24 horas tendrás una nueva propuesta lista.
      </p>

      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <a
          :href="whatsappReactivationUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center justify-center gap-2 px-6 py-3
                 bg-emerald-600 text-white rounded-xl font-medium
                 hover:bg-emerald-700 transition-colors shadow-lg"
        >
          <svg class="w-5 h-5" viewBox="0 0 448 512" fill="currentColor">
            <path d="M380.9 97.1C339 55.1 283.2 32 223.9 32c-122.4 0-222 99.6-222 222
              0 39.1 10.2 77.3 29.6 111L0 480l117.7-30.9c32.4 17.7 68.9 27 106.1 27h.1
              c122.3 0 224.1-99.6 224.1-222 0-59.3-25.2-115-67.1-157" />
          </svg>
          Solicitar reactivación
        </a>

        <a
          href="mailto:team@projectapp.co"
          class="inline-flex items-center justify-center gap-2 px-6 py-3
                 bg-white text-gray-700 rounded-xl font-medium border border-gray-200
                 hover:bg-gray-50 transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          Email
        </a>
      </div>

      <p class="mt-12 text-xs text-gray-400">
        Project App. — projectapp.co
      </p>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  proposal: {
    type: Object,
    default: null,
  },
});

const clientName = computed(() => props.proposal?.client_name || '');
const proposalTitle = computed(() => props.proposal?.title || '');

const whatsappReactivationUrl = computed(() => {
  const title = proposalTitle.value;
  const name = clientName.value;
  const greeting = name ? `Hola, soy ${name}. ` : 'Hola. ';
  const msg = title
    ? `${greeting}La propuesta "${title}" expiró y me gustaría reactivarla o recibir una versión actualizada.`
    : `${greeting}Mi propuesta expiró y me gustaría reactivarla o recibir una versión actualizada.`;
  return `https://wa.me/573238122373?text=${encodeURIComponent(msg)}`;
});
</script>
