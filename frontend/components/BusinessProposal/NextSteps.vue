<template>
  <section ref="sectionRef" class="next-steps py-16 md:py-24 bg-white">
    <div class="container mx-auto px-4 max-w-5xl">
      <div class="section-header mb-12">
        <div data-animate="fade-up" class="flex items-baseline gap-4 mb-10">
          <span class="text-green-light font-light tracking-[0.25em] text-xs md:text-sm">
            11
          </span>
          <h2 class="text-esmerald font-light leading-tight text-4xl md:text-6xl">
            Cierre y Próximos Pasos
          </h2>
        </div>
      </div>

      <div class="intro-message mb-12 text-center">
        <p class="text-2xl text-gray-700 leading-relaxed font-light">
          {{ introMessage }}
        </p>
      </div>

      <div class="steps-container mb-12">
        <div class="grid md:grid-cols-3 gap-8">
          <div v-for="(step, index) in steps" :key="index"
               class="step-card bg-gradient-to-br from-emerald-50 to-white p-8 rounded-2xl border-2 border-emerald-100 hover:border-emerald-500 transition-all text-center">
            <div class="step-number w-16 h-16 bg-emerald-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-6 shadow-lg">
              {{ index + 1 }}
            </div>
            <h3 class="text-xl font-bold text-gray-900 mb-3">{{ step.title }}</h3>
            <p class="text-gray-600 leading-relaxed">{{ step.description }}</p>
          </div>
        </div>
      </div>

      <div class="cta-section bg-gradient-to-br from-emerald-600 to-emerald-700 p-8 md:p-12 rounded-3xl text-white text-center mb-12 shadow-2xl">
        <h3 class="text-3xl md:text-4xl font-bold mb-4">¿Listo para Comenzar?</h3>
        <p class="text-xl text-emerald-100 mb-8 max-w-2xl mx-auto">
          {{ ctaMessage }}
        </p>
        
        <div class="cta-buttons flex flex-col md:flex-row gap-4 justify-center">
          <a :href="primaryCTA.link"
             class="inline-flex items-center justify-center px-8 py-4 bg-white text-emerald-600 rounded-xl font-bold text-lg hover:bg-emerald-50 transition-all shadow-lg hover:shadow-xl">
            <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
            </svg>
            {{ primaryCTA.text }}
          </a>
          
          <a :href="secondaryCTA.link"
             class="inline-flex items-center justify-center px-8 py-4 bg-emerald-800 text-white rounded-xl font-bold text-lg hover:bg-emerald-900 transition-all">
            <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
            {{ secondaryCTA.text }}
          </a>
        </div>
      </div>

      <div class="contact-info grid md:grid-cols-3 gap-6 mb-12">
        <div v-for="(contact, index) in contactMethods" :key="index"
             class="contact-card bg-gray-50 p-6 rounded-xl text-center hover:bg-emerald-50 transition-colors">
          <div class="text-4xl mb-3">{{ contact.icon }}</div>
          <h4 class="font-bold text-gray-900 mb-2">{{ contact.title }}</h4>
          <a :href="contact.link" class="text-emerald-600 hover:text-emerald-700 font-medium">
            {{ contact.value }}
          </a>
        </div>
      </div>

      <div class="validity-notice bg-yellow-50 border-2 border-yellow-200 p-6 rounded-xl">
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

      <div class="thank-you-message mt-12 text-center">
        <h3 class="text-3xl font-bold text-gray-900 mb-4">¡Gracias por tu Tiempo!</h3>
        <p class="text-lg text-gray-600 max-w-2xl mx-auto">
          {{ thankYouMessage }}
        </p>
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
  introMessage: {
    type: String,
    default: 'Estamos listos para comenzar este viaje juntos. Aquí te explicamos cómo dar el siguiente paso:'
  },
  steps: {
    type: Array,
    default: () => [
      {
        title: 'Revisión y Preguntas',
        description: 'Revisa la propuesta y envíanos cualquier pregunta o ajuste que necesites.'
      },
      {
        title: 'Reunión de Confirmación',
        description: 'Agendamos una llamada para alinear detalles finales y firmar el contrato.'
      },
      {
        title: '¡Comenzamos!',
        description: 'Iniciamos el proyecto con la reunión de kickoff y arrancamos la fase de Discovery.'
      }
    ]
  },
  ctaMessage: {
    type: String,
    default: 'Contáctanos hoy mismo y comencemos a trabajar en tu proyecto. Estamos a solo un mensaje de distancia.'
  },
  primaryCTA: {
    type: Object,
    default: () => ({
      text: 'Contactar por WhatsApp',
      link: 'https://wa.me/1234567890'
    })
  },
  secondaryCTA: {
    type: Object,
    default: () => ({
      text: 'Agendar Reunión',
      link: 'https://calendly.com/projectapp'
    })
  },
  contactMethods: {
    type: Array,
    default: () => [
      {
        icon: '📧',
        title: 'Email',
        value: 'hola@projectapp.com',
        link: 'mailto:hola@projectapp.com'
      },
      {
        icon: '📱',
        title: 'WhatsApp',
        value: '+57 123 456 7890',
        link: 'https://wa.me/571234567890'
      },
      {
        icon: '🌐',
        title: 'Website',
        value: 'www.projectapp.com',
        link: 'https://www.projectapp.com'
      }
    ]
  },
  validityMessage: {
    type: String,
    default: 'Esta propuesta es válida por 30 días a partir de la fecha de emisión. Los precios y condiciones pueden estar sujetos a cambios después de este período.'
  },
  thankYouMessage: {
    type: String,
    default: 'Apreciamos sinceramente la oportunidad de presentarte esta propuesta. Esperamos con entusiasmo la posibilidad de trabajar contigo y ayudarte a alcanzar tus objetivos.'
  }
});
</script>

<style scoped>
.step-card {
  transition: all 0.3s ease;
}

.step-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(16, 185, 129, 0.2);
}

.step-number {
  transition: transform 0.3s ease;
}

.step-card:hover .step-number {
  transform: scale(1.1) rotate(5deg);
}

.contact-card {
  transition: all 0.3s ease;
}

.contact-card:hover {
  transform: scale(1.05);
}

.cta-buttons a {
  transition: all 0.3s ease;
}

.cta-buttons a:hover {
  transform: translateY(-2px);
}
</style>
