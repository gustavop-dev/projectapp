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
