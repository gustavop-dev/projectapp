<template>
  <section class="functional-requirements py-16 md:py-24 bg-white">
    <div class="container mx-auto px-4 max-w-5xl">
      <div class="section-header mb-12">
        <span class="text-sm font-semibold text-emerald-600 uppercase tracking-wider">07</span>
        <h2 class="text-4xl md:text-5xl font-bold text-gray-900 mt-2 mb-6">
          Requerimientos Funcionales del Proyecto
        </h2>
        <div class="h-1 w-20 bg-emerald-600"></div>
      </div>

      <div class="requirements-intro mb-12">
        <p class="text-xl text-gray-600 leading-relaxed">
          {{ introText }}
        </p>
      </div>

      <div class="requirements-categories space-y-8">
        <div v-for="(category, index) in categories" :key="index"
             class="category-section">
          <div class="category-header mb-6">
            <div class="flex items-center mb-4">
              <div class="w-12 h-12 rounded-xl flex items-center justify-center mr-4"
                   :class="category.bgColor">
                <span class="text-2xl">{{ category.icon }}</span>
              </div>
              <h3 class="text-2xl font-bold text-gray-900">{{ category.title }}</h3>
            </div>
            <p class="text-gray-600 leading-relaxed pl-16">{{ category.description }}</p>
          </div>

          <div class="requirements-grid grid md:grid-cols-2 gap-4 pl-16">
            <div v-for="(requirement, idx) in category.requirements" :key="idx"
                 class="requirement-card bg-gray-50 p-5 rounded-xl hover:bg-emerald-50 transition-colors border border-gray-100 hover:border-emerald-200">
              <div class="flex items-start">
                <svg class="w-5 h-5 text-emerald-600 mr-3 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
                <div>
                  <h4 class="font-bold text-gray-900 mb-1">{{ requirement.name }}</h4>
                  <p class="text-sm text-gray-600">{{ requirement.description }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="technical-specs mt-12 bg-gradient-to-br from-gray-900 to-gray-800 p-8 md:p-12 rounded-2xl text-white">
        <h3 class="text-2xl font-bold mb-8">Especificaciones Técnicas</h3>
        <div class="grid md:grid-cols-3 gap-8">
          <div v-for="(spec, index) in technicalSpecs" :key="index"
               class="spec-item">
            <div class="flex items-center mb-3">
              <div class="w-10 h-10 bg-emerald-600 rounded-lg flex items-center justify-center mr-3">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="spec.icon"></path>
                </svg>
              </div>
              <h4 class="font-bold">{{ spec.title }}</h4>
            </div>
            <ul class="space-y-2 pl-13">
              <li v-for="(item, idx) in spec.items" :key="idx"
                  class="text-sm text-gray-300 flex items-start">
                <span class="text-emerald-400 mr-2">•</span>
                <span>{{ item }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="integrations mt-8 bg-white p-8 md:p-10 rounded-2xl border-2 border-gray-100">
        <h3 class="text-2xl font-bold text-gray-900 mb-6">Integraciones Disponibles</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div v-for="(integration, index) in integrations" :key="index"
               class="integration-card p-4 bg-gray-50 rounded-xl text-center hover:bg-emerald-50 transition-colors">
            <div class="text-3xl mb-2">{{ integration.icon }}</div>
            <div class="text-sm font-medium text-gray-900">{{ integration.name }}</div>
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
    default: 'Estas son las funcionalidades y características técnicas que incluirá tu proyecto, diseñadas para cumplir tus objetivos de negocio y ofrecer la mejor experiencia a tus usuarios.'
  },
  categories: {
    type: Array,
    default: () => [
      {
        title: 'Funcionalidades Core',
        icon: '⚡',
        bgColor: 'bg-blue-100',
        description: 'Características fundamentales que todo sitio moderno debe tener.',
        requirements: [
          { name: 'Diseño Responsive', description: 'Adaptación perfecta a móviles, tablets y desktop' },
          { name: 'Optimización SEO', description: 'Estructura y metadatos optimizados para buscadores' },
          { name: 'Formularios de Contacto', description: 'Con validación y protección anti-spam' },
          { name: 'Google Analytics', description: 'Seguimiento completo de métricas y conversiones' },
          { name: 'Mapa Interactivo', description: 'Integración con Google Maps para ubicación' },
          { name: 'Chat en Vivo', description: 'Widget de WhatsApp o chat para atención inmediata' }
        ]
      },
      {
        title: 'Gestión de Contenido',
        icon: '📝',
        bgColor: 'bg-purple-100',
        description: 'Herramientas para que puedas actualizar tu contenido fácilmente.',
        requirements: [
          { name: 'CMS Intuitivo', description: 'Panel de administración fácil de usar' },
          { name: 'Editor Visual', description: 'Edita contenido sin necesidad de código' },
          { name: 'Gestión de Imágenes', description: 'Optimización automática de imágenes' },
          { name: 'Blog/Noticias', description: 'Sistema para publicar artículos y actualizaciones' },
          { name: 'Múltiples Usuarios', description: 'Diferentes niveles de acceso y permisos' },
          { name: 'Programación de Contenido', description: 'Publica contenido en fechas específicas' }
        ]
      },
      {
        title: 'Performance & Seguridad',
        icon: '🔒',
        bgColor: 'bg-green-100',
        description: 'Garantizamos velocidad y protección de datos.',
        requirements: [
          { name: 'Certificado SSL', description: 'Conexión segura HTTPS incluida' },
          { name: 'CDN Global', description: 'Entrega rápida de contenido en todo el mundo' },
          { name: 'Caché Optimizado', description: 'Tiempos de carga menores a 1 segundo' },
          { name: 'Backups Automáticos', description: 'Copias de seguridad diarias' },
          { name: 'Protección DDoS', description: 'Seguridad contra ataques maliciosos' },
          { name: 'Firewall Web', description: 'Protección adicional de aplicación' }
        ]
      },
      {
        title: 'Marketing & Conversión',
        icon: '📈',
        bgColor: 'bg-orange-100',
        description: 'Herramientas para maximizar conversiones y captar leads.',
        requirements: [
          { name: 'Pop-ups Inteligentes', description: 'Ventanas emergentes con targeting avanzado' },
          { name: 'Formularios Avanzados', description: 'Multi-paso con lógica condicional' },
          { name: 'Integración Email Marketing', description: 'Conexión con Mailchimp, SendGrid, etc.' },
          { name: 'Pixel de Conversión', description: 'Tracking para Facebook Ads y Google Ads' },
          { name: 'A/B Testing', description: 'Pruebas para optimizar conversiones' },
          { name: 'Testimonios Dinámicos', description: 'Carrusel de reseñas de clientes' }
        ]
      }
    ]
  },
  technicalSpecs: {
    type: Array,
    default: () => [
      {
        title: 'Frontend',
        icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
        items: [
          'Vue.js 3 / React',
          'TailwindCSS',
          'GSAP Animations',
          'Progressive Web App'
        ]
      },
      {
        title: 'Backend',
        icon: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01',
        items: [
          'Node.js / PHP',
          'API RESTful',
          'Base de datos MySQL/MongoDB',
          'Autenticación segura'
        ]
      },
      {
        title: 'Hosting',
        icon: 'M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z',
        items: [
          'Servidor VPS optimizado',
          'CDN Cloudflare',
          '99.9% uptime garantizado',
          'Soporte técnico 24/7'
        ]
      }
    ]
  },
  integrations: {
    type: Array,
    default: () => [
      { name: 'Google Analytics', icon: '📊' },
      { name: 'Mailchimp', icon: '📧' },
      { name: 'Stripe', icon: '💳' },
      { name: 'WhatsApp', icon: '💬' },
      { name: 'Facebook Pixel', icon: '📱' },
      { name: 'Google Maps', icon: '🗺️' },
      { name: 'Calendly', icon: '📅' },
      { name: 'Zapier', icon: '⚡' }
    ]
  }
});
</script>

<style scoped>
.requirement-card {
  transition: all 0.3s ease;
}

.requirement-card:hover {
  transform: translateX(4px);
}

.integration-card {
  transition: all 0.3s ease;
}

.integration-card:hover {
  transform: scale(1.05);
}
</style>
