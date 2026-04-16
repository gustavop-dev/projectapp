<template>
  <section>
    <SectionHeader :index="content.index" :title="content.title" fallback="Radiografía" />
    <p v-if="content.intro" class="text-gray-700 leading-relaxed">{{ content.intro }}</p>

    <div v-if="content.includes?.length" class="mt-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ content.includesTitle || '¿Qué incluye esta radiografía?' }}</h3>
      <ul class="space-y-2">
        <li v-for="(i, idx) in content.includes" :key="idx" class="flex gap-2">
          <span class="text-emerald-600">•</span>
          <div>
            <strong class="text-gray-800">{{ i.title }}:</strong>
            <span class="text-gray-700">{{ ' ' + (i.description || '') }}</span>
          </div>
        </li>
      </ul>
    </div>

    <div v-if="content.classificationRows?.length" class="mt-8">
      <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ content.classificationTitle || 'Clasificación por tamaño' }}</h3>
      <p v-if="content.classificationIntro" class="text-gray-700 mb-3">{{ content.classificationIntro }}</p>
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-3 py-2 text-left font-semibold text-gray-700">Dimensión</th>
              <th class="px-3 py-2 text-left font-semibold text-gray-700">Pequeña</th>
              <th class="px-3 py-2 text-left font-semibold text-gray-700">Mediana</th>
              <th class="px-3 py-2 text-left font-semibold text-gray-700">Grande</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in content.classificationRows" :key="idx" class="border-t border-gray-200">
              <td class="px-3 py-2 text-gray-800">{{ row.dimension }}</td>
              <td class="px-3 py-2 text-gray-700">{{ row.small }}</td>
              <td class="px-3 py-2 text-gray-700">{{ row.medium }}</td>
              <td class="px-3 py-2 text-gray-700">{{ row.large }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="content.classificationNote" class="text-xs text-gray-500 mt-2 italic">{{ content.classificationNote }}</p>
    </div>

    <div v-if="renderContext && hasStack" class="mt-8 bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm">
      <h3 class="text-sm font-semibold text-gray-800 mb-2">Stack detectado</h3>
      <ul class="space-y-1 text-gray-700">
        <li v-if="renderContext.stack_backend_name">
          <strong>Backend:</strong> {{ renderContext.stack_backend_name }}
          <span v-if="renderContext.stack_backend_version"> ({{ renderContext.stack_backend_version }})</span>
        </li>
        <li v-if="renderContext.stack_frontend_name">
          <strong>Frontend:</strong> {{ renderContext.stack_frontend_name }}
          <span v-if="renderContext.stack_frontend_version"> ({{ renderContext.stack_frontend_version }})</span>
        </li>
        <li v-if="renderContext.entities_count"><strong>Entidades:</strong> {{ renderContext.entities_count }} ({{ renderContext.entities_size }})</li>
        <li v-if="renderContext.routes_total"><strong>Rutas backend:</strong> {{ renderContext.routes_total }} ({{ renderContext.routes_size }})</li>
        <li v-if="renderContext.frontend_routes_count"><strong>Rutas frontend:</strong> {{ renderContext.frontend_routes_count }} ({{ renderContext.frontend_routes_size }})</li>
        <li v-if="renderContext.components_count"><strong>Componentes:</strong> {{ renderContext.components_count }} ({{ renderContext.components_size }})</li>
        <li v-if="renderContext.external_integrations"><strong>Integraciones:</strong> {{ renderContext.external_integrations }} ({{ renderContext.integrations_size }})</li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import SectionHeader from './SectionHeader.vue';
const props = defineProps({
  content: { type: Object, required: true },
  renderContext: { type: Object, default: () => ({}) },
});
const hasStack = computed(() => !!(props.renderContext?.stack_backend_name || props.renderContext?.stack_frontend_name));
</script>
