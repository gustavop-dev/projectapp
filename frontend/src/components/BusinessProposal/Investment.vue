<template>
  <section class="investment py-16 md:py-24 bg-white">
    <div class="container mx-auto px-4 max-w-5xl">
      <div class="section-header mb-12">
        <span class="text-sm font-semibold text-emerald-600 uppercase tracking-wider">09</span>
        <h2 class="text-4xl md:text-5xl font-bold text-gray-900 mt-2 mb-6">
          Inversión y Formas de Pago
        </h2>
        <div class="h-1 w-20 bg-emerald-600"></div>
      </div>

      <div class="investment-intro mb-12">
        <p class="text-xl text-gray-600 leading-relaxed">
          {{ introText }}
        </p>
      </div>

      <div class="pricing-card bg-gradient-to-br from-emerald-600 to-emerald-700 p-8 md:p-12 rounded-3xl text-white mb-12 shadow-2xl">
        <div class="text-center mb-8">
          <div class="text-sm font-semibold uppercase tracking-wider mb-4 text-emerald-200">Inversión Total</div>
          <div class="text-6xl md:text-7xl font-bold mb-2">{{ totalInvestment }}</div>
          <div class="text-emerald-200">{{ currency }}</div>
        </div>
        
        <div class="grid md:grid-cols-3 gap-6 mt-8">
          <div v-for="(item, index) in whatsIncluded" :key="index"
               class="text-center p-4 bg-white/10 backdrop-blur-sm rounded-xl">
            <div class="text-3xl mb-2">{{ item.icon }}</div>
            <div class="font-bold mb-1">{{ item.title }}</div>
            <div class="text-sm text-emerald-100">{{ item.description }}</div>
          </div>
        </div>
      </div>

      <div class="payment-options grid md:grid-cols-2 gap-8 mb-12">
        <div v-for="(option, index) in paymentOptions" :key="index"
             class="payment-option-card bg-gray-50 p-8 rounded-2xl border-2 border-gray-200 hover:border-emerald-500 transition-all">
          <div class="flex items-center mb-4">
            <div class="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center mr-4">
              <span class="text-2xl">{{ option.icon }}</span>
            </div>
            <h3 class="text-2xl font-bold text-gray-900">{{ option.title }}</h3>
          </div>
          <p class="text-gray-600 mb-6">{{ option.description }}</p>
          
          <div class="payment-breakdown space-y-3">
            <div v-for="(payment, idx) in option.breakdown" :key="idx"
                 class="flex items-center justify-between p-3 bg-white rounded-lg">
              <span class="text-gray-700">{{ payment.label }}</span>
              <span class="font-bold text-gray-900">{{ payment.amount }}</span>
            </div>
          </div>

          <div v-if="option.benefit" class="benefit-badge mt-6 p-4 bg-emerald-50 rounded-xl border border-emerald-200">
            <div class="flex items-center">
              <svg class="w-5 h-5 text-emerald-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              <span class="text-sm font-medium text-emerald-700">{{ option.benefit }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="payment-methods bg-gray-50 p-8 md:p-10 rounded-2xl mb-12">
        <h3 class="text-2xl font-bold text-gray-900 mb-6">Métodos de Pago Aceptados</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div v-for="(method, index) in paymentMethods" :key="index"
               class="payment-method-card bg-white p-6 rounded-xl text-center hover:shadow-md transition-shadow">
            <div class="text-4xl mb-2">{{ method.icon }}</div>
            <div class="text-sm font-medium text-gray-900">{{ method.name }}</div>
          </div>
        </div>
      </div>

      <div class="value-proposition bg-gradient-to-br from-gray-900 to-gray-800 p-8 md:p-12 rounded-2xl text-white">
        <h3 class="text-2xl font-bold mb-6">¿Por Qué Esta Inversión Vale la Pena?</h3>
        <div class="grid md:grid-cols-2 gap-6">
          <div v-for="(reason, index) in valueReasons" :key="index"
               class="value-reason flex items-start">
            <div class="flex-shrink-0 w-10 h-10 bg-emerald-600 rounded-lg flex items-center justify-center mr-4">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="reason.icon"></path>
              </svg>
            </div>
            <div>
              <h4 class="font-bold mb-2">{{ reason.title }}</h4>
              <p class="text-sm text-gray-300">{{ reason.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  introText: {
    type: String,
    default: 'Esta inversión representa mucho más que un sitio web: es una herramienta estratégica que trabajará 24/7 para hacer crecer tu negocio. Ofrecemos opciones flexibles de pago para adaptarnos a tu flujo de caja.'
  },
  totalInvestment: {
    type: String,
    default: '$15,000'
  },
  currency: {
    type: String,
    default: 'USD + IVA'
  },
  whatsIncluded: {
    type: Array,
    default: () => [
      { icon: '🎨', title: 'Diseño Premium', description: 'Diseño personalizado y moderno' },
      { icon: '⚙️', title: 'Desarrollo Completo', description: 'Código limpio y optimizado' },
      { icon: '🚀', title: 'Hosting 1 Año', description: 'Incluido en la inversión' }
    ]
  },
  paymentOptions: {
    type: Array,
    default: () => [
      {
        title: 'Plan Estándar',
        icon: '💳',
        description: 'Pago en 3 cuotas durante el desarrollo del proyecto.',
        breakdown: [
          { label: 'Al inicio (40%)', amount: '$6,000' },
          { label: 'A mitad (30%)', amount: '$4,500' },
          { label: 'Al lanzamiento (30%)', amount: '$4,500' }
        ],
        benefit: null
      },
      {
        title: 'Plan Anticipado',
        icon: '⚡',
        description: 'Pago completo por adelantado con descuento especial.',
        breakdown: [
          { label: 'Pago único', amount: '$13,500' },
          { label: 'Ahorro', amount: '-$1,500' }
        ],
        benefit: '10% de descuento + prioridad en el cronograma'
      }
    ]
  },
  paymentMethods: {
    type: Array,
    default: () => [
      { name: 'Transferencia', icon: '🏦' },
      { name: 'Tarjeta', icon: '💳' },
      { name: 'PayPal', icon: '💰' },
      { name: 'Stripe', icon: '💵' }
    ]
  },
  valueReasons: {
    type: Array,
    default: () => [
      {
        title: 'ROI Comprobado',
        icon: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
        description: 'Nuestros clientes recuperan su inversión en promedio en 6-8 meses gracias al aumento en conversiones.'
      },
      {
        title: 'Trabajo 24/7',
        icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
        description: 'Tu sitio web trabaja constantemente generando leads y ventas, incluso mientras duermes.'
      },
      {
        title: 'Activo Apreciable',
        icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
        description: 'A diferencia de la publicidad, esta inversión crea un activo que aumenta su valor con el tiempo.'
      },
      {
        title: 'Ventaja Competitiva',
        icon: 'M13 10V3L4 14h7v7l9-11h-7z',
        description: 'Un sitio profesional te posiciona por encima de competidores con presencia digital deficiente.'
      }
    ]
  }
});
</script>

<style scoped>
.payment-option-card {
  transition: all 0.3s ease;
}

.payment-option-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.payment-method-card {
  transition: all 0.3s ease;
}

.payment-method-card:hover {
  transform: scale(1.05);
}

.value-reason {
  transition: transform 0.3s ease;
}

.value-reason:hover {
  transform: translateX(8px);
}
</style>
