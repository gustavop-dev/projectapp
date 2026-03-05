<template>
  <section ref="sectionRef" class="final-note py-16 md:py-24 bg-gray-50">
    <div class="container mx-auto px-4 max-w-4xl">
      <div class="section-header mb-12">
        <div data-animate="fade-up" class="flex items-baseline gap-4 mb-10">
          <span class="text-green-light font-light tracking-[0.25em] text-xs md:text-sm">
            {{ index }}
          </span>
          <h2 class="text-esmerald font-light leading-tight text-4xl md:text-6xl">
            {{ title }}
          </h2>
        </div>
      </div>

      <div class="note-content bg-white p-8 md:p-12 rounded-2xl shadow-sm mb-8">
        <div class="quote-icon mb-6">
          <svg class="w-12 h-12 text-emerald-600 opacity-50" fill="currentColor" viewBox="0 0 24 24">
            <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z"/>
          </svg>
        </div>

        <div class="message-text space-y-6 text-lg text-gray-700 leading-relaxed">
          <p>{{ message }}</p>
          
          <p v-if="personalNote" class="italic text-gray-600">
            {{ personalNote }}
          </p>
        </div>

        <div class="signature mt-12 pt-8 border-t border-gray-200">
          <div class="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <p class="text-xl font-bold text-gray-900 mb-2">{{ teamName }}</p>
              <p class="text-gray-600">{{ teamRole }}</p>
              <p class="text-sm text-gray-500 mt-2">{{ contactEmail }}</p>
            </div>
            <div class="mt-6 md:mt-0">
              <img v-if="signature" :src="signature" alt="Firma" class="h-16" />
            </div>
          </div>
        </div>
      </div>

      <div class="commitment-badges grid md:grid-cols-3 gap-6">
        <div v-for="(badge, index) in commitmentBadges" :key="index"
             class="badge-card bg-white p-6 rounded-xl shadow-sm text-center hover:shadow-md transition-shadow">
          <div class="text-4xl mb-3">{{ badge.icon }}</div>
          <h4 class="font-bold text-gray-900 mb-2">{{ badge.title }}</h4>
          <p class="text-sm text-gray-600">{{ badge.description }}</p>
        </div>
      </div>

      <div v-if="validityMessage" class="validity-notice mt-12 bg-yellow-50 border-2 border-yellow-200 p-6 rounded-xl">
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

      <div v-if="thankYouMessage" class="thank-you-message mt-12 text-center">
        <h3 class="text-3xl font-bold text-gray-900 mb-4">¡Gracias por tu Tiempo!</h3>
        <p class="text-lg text-gray-600 max-w-2xl mx-auto">{{ thankYouMessage }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue';
import { useSectionAnimations } from '~/composables/useSectionAnimations';

const sectionRef = ref(null);
useSectionAnimations(sectionRef);

const props = defineProps({
  index: {
    type: String,
    default: '10'
  },
  title: {
    type: String,
    default: 'Nota Final'
  },
  message: {
    type: String,
    default: 'Creemos firmemente que esta propuesta representa una oportunidad excepcional para transformar tu presencia digital y alcanzar tus objetivos de negocio. Cada elemento ha sido cuidadosamente diseñado pensando en tus necesidades específicas y en los resultados que buscas lograr. Estamos comprometidos no solo con entregar un proyecto excepcional, sino con construir una relación de largo plazo donde tu éxito sea nuestro éxito.'
  },
  personalNote: {
    type: String,
    default: 'Estamos emocionados por la posibilidad de trabajar contigo y ayudarte a llevar tu negocio al siguiente nivel. Esta propuesta es solo el comienzo de lo que podemos lograr juntos.'
  },
  teamName: {
    type: String,
    default: 'El equipo de Project App'
  },
  teamRole: {
    type: String,
    default: 'Tu socio en transformación digital'
  },
  contactEmail: {
    type: String,
    default: 'hola@projectapp.com'
  },
  signature: {
    type: String,
    default: null
  },
  commitmentBadges: {
    type: Array,
    default: () => [
      {
        icon: '🤝',
        title: 'Compromiso Total',
        description: 'Dedicación completa a tu proyecto hasta lograr resultados excepcionales'
      },
      {
        icon: '💯',
        title: 'Garantía de Calidad',
        description: 'Revisiones ilimitadas hasta tu completa satisfacción'
      },
      {
        icon: '🎯',
        title: 'Enfoque en Resultados',
        description: 'Medimos nuestro éxito por el impacto en tu negocio'
      }
    ]
  },
  validityMessage: {
    type: String,
    default: ''
  },
  thankYouMessage: {
    type: String,
    default: ''
  }
});
</script>

<style scoped>
.badge-card {
  transition: all 0.3s ease;
}

.badge-card:hover {
  transform: translateY(-4px);
}

.message-text p {
  text-align: justify;
}
</style>
