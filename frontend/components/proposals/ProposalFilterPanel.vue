<template>
  <Transition
    enter-active-class="transition-[opacity,transform] duration-200 ease-out"
    leave-active-class="transition-[opacity,transform] duration-150 ease-in"
    enter-from-class="opacity-0 -translate-y-2"
    enter-to-class="opacity-100 translate-y-0"
    leave-from-class="opacity-100 translate-y-0"
    leave-to-class="opacity-0 -translate-y-2"
  >
    <div v-if="isOpen" class="mb-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4">
      <!-- Status pills -->
      <div class="mb-4">
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Estado</label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="opt in statusOptions"
            :key="opt.value"
            type="button"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border"
            :class="modelValue.statuses.includes(opt.value)
              ? 'bg-emerald-600 text-white border-emerald-600'
              : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'"
            @click="toggleArrayFilter('statuses', opt.value)"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <!-- Grid filters -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-4">
        <!-- Project Type -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">Tipo de proyecto</label>
          <select
            :value="modelValue.projectTypes.length === 1 ? modelValue.projectTypes[0] : ''"
            class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 outline-none focus:ring-1 focus:ring-emerald-500"
            @change="toggleMultiSelect('projectTypes', $event.target.value)"
          >
            <option value="">Todos</option>
            <option v-for="opt in projectTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
          <div v-if="modelValue.projectTypes.length > 1" class="mt-1 flex flex-wrap gap-1">
            <span
              v-for="pt in modelValue.projectTypes"
              :key="pt"
              class="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 text-xs rounded-full"
            >
              {{ projectTypeLabelMap[pt] || pt }}
              <button type="button" class="hover:text-red-500" @click="removeFromArray('projectTypes', pt)">&times;</button>
            </span>
          </div>
        </div>

        <!-- Market Type -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">Tipo de mercado</label>
          <select
            :value="modelValue.marketTypes.length === 1 ? modelValue.marketTypes[0] : ''"
            class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 outline-none focus:ring-1 focus:ring-emerald-500"
            @change="toggleMultiSelect('marketTypes', $event.target.value)"
          >
            <option value="">Todos</option>
            <option v-for="opt in marketTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
          <div v-if="modelValue.marketTypes.length > 1" class="mt-1 flex flex-wrap gap-1">
            <span
              v-for="mt in modelValue.marketTypes"
              :key="mt"
              class="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 text-xs rounded-full"
            >
              {{ marketTypeLabelMap[mt] || mt }}
              <button type="button" class="hover:text-red-500" @click="removeFromArray('marketTypes', mt)">&times;</button>
            </span>
          </div>
        </div>

        <!-- Currency -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">Moneda</label>
          <div class="flex gap-2">
            <button
              v-for="cur in ['COP', 'USD']"
              :key="cur"
              type="button"
              class="px-3 py-2 rounded-lg text-xs font-medium transition-colors border flex-1"
              :class="modelValue.currencies.includes(cur)
                ? 'bg-emerald-600 text-white border-emerald-600'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-600 hover:border-gray-300'"
              @click="toggleArrayFilter('currencies', cur)"
            >
              {{ cur }}
            </button>
          </div>
        </div>

        <!-- Language -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">Idioma</label>
          <div class="flex gap-2">
            <button
              v-for="lang in [{value: 'es', label: 'ES'}, {value: 'en', label: 'EN'}]"
              :key="lang.value"
              type="button"
              class="px-3 py-2 rounded-lg text-xs font-medium transition-colors border flex-1"
              :class="modelValue.languages.includes(lang.value)
                ? 'bg-emerald-600 text-white border-emerald-600'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-600 hover:border-gray-300'"
              @click="toggleArrayFilter('languages', lang.value)"
            >
              {{ lang.label }}
            </button>
          </div>
        </div>

        <!-- Investment range -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">Inversión</label>
          <div class="flex items-center gap-2">
            <input
              :value="modelValue.investmentMin"
              type="number"
              placeholder="Mín"
              min="0"
              class="w-full px-2.5 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 outline-none focus:ring-1 focus:ring-emerald-500"
              @change="updateNumeric('investmentMin', $event.target.value)"
            />
            <span class="text-gray-400 text-xs">—</span>
            <input
              :value="modelValue.investmentMax"
              type="number"
              placeholder="Máx"
              min="0"
              class="w-full px-2.5 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 outline-none focus:ring-1 focus:ring-emerald-500"
              @change="updateNumeric('investmentMax', $event.target.value)"
            />
          </div>
        </div>

        <!-- Heat Score range -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">Heat Score</label>
          <div class="flex items-center gap-2">
            <input
              :value="modelValue.heatScoreMin"
              type="number"
              placeholder="Mín"
              min="0"
              max="10"
              class="w-full px-2.5 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 outline-none focus:ring-1 focus:ring-emerald-500"
              @change="updateNumeric('heatScoreMin', $event.target.value)"
            />
            <span class="text-gray-400 text-xs">—</span>
            <input
              :value="modelValue.heatScoreMax"
              type="number"
              placeholder="Máx"
              min="0"
              max="10"
              class="w-full px-2.5 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 outline-none focus:ring-1 focus:ring-emerald-500"
              @change="updateNumeric('heatScoreMax', $event.target.value)"
            />
          </div>
        </div>

        <!-- View Count range -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">Vistas</label>
          <div class="flex items-center gap-2">
            <input
              :value="modelValue.viewCountMin"
              type="number"
              placeholder="Mín"
              min="0"
              class="w-full px-2.5 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 outline-none focus:ring-1 focus:ring-emerald-500"
              @change="updateNumeric('viewCountMin', $event.target.value)"
            />
            <span class="text-gray-400 text-xs">—</span>
            <input
              :value="modelValue.viewCountMax"
              type="number"
              placeholder="Máx"
              min="0"
              class="w-full px-2.5 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 outline-none focus:ring-1 focus:ring-emerald-500"
              @change="updateNumeric('viewCountMax', $event.target.value)"
            />
          </div>
        </div>

        <!-- Active status -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">Estado activo</label>
          <div class="flex gap-2">
            <button
              v-for="opt in [{value: 'all', label: 'Todos'}, {value: 'active', label: 'Activas'}, {value: 'inactive', label: 'Inactivas'}]"
              :key="opt.value"
              type="button"
              class="px-3 py-2 rounded-lg text-xs font-medium transition-colors border flex-1"
              :class="modelValue.isActive === opt.value
                ? 'bg-emerald-600 text-white border-emerald-600'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-600 hover:border-gray-300'"
              @click="updateField('isActive', opt.value)"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>
      </div>

      <!-- Date ranges -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        <!-- Created date range -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">Fecha de creación</label>
          <div class="flex items-center gap-2">
            <input
              :value="modelValue.createdAfter"
              type="date"
              class="w-full px-2.5 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 outline-none focus:ring-1 focus:ring-emerald-500"
              @input="updateField('createdAfter', $event.target.value || null)"
            />
            <span class="text-gray-400 text-xs shrink-0">a</span>
            <input
              :value="modelValue.createdBefore"
              type="date"
              class="w-full px-2.5 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 outline-none focus:ring-1 focus:ring-emerald-500"
              @input="updateField('createdBefore', $event.target.value || null)"
            />
          </div>
        </div>

        <!-- Last activity date range -->
        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">Última actividad</label>
          <div class="flex items-center gap-2">
            <input
              :value="modelValue.lastActivityAfter"
              type="date"
              class="w-full px-2.5 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 outline-none focus:ring-1 focus:ring-emerald-500"
              @input="updateField('lastActivityAfter', $event.target.value || null)"
            />
            <span class="text-gray-400 text-xs shrink-0">a</span>
            <input
              :value="modelValue.lastActivityBefore"
              type="date"
              class="w-full px-2.5 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 outline-none focus:ring-1 focus:ring-emerald-500"
              @input="updateField('lastActivityBefore', $event.target.value || null)"
            />
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-700">
        <button
          type="button"
          class="text-sm text-gray-500 dark:text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors font-medium"
          @click="$emit('reset')"
        >
          Limpiar filtros
        </button>
        <span v-if="filterCount > 0" class="text-xs text-gray-400 dark:text-gray-500">
          {{ filterCount }} filtro{{ filterCount !== 1 ? 's' : '' }} activo{{ filterCount !== 1 ? 's' : '' }}
        </span>
      </div>
    </div>
  </Transition>
</template>

<script setup>
const props = defineProps({
  modelValue: { type: Object, required: true },
  isOpen: { type: Boolean, default: false },
  filterCount: { type: Number, default: 0 },
});

const emit = defineEmits(['update:modelValue', 'reset']);

const statusOptions = [
  { value: 'draft', label: 'Borrador' },
  { value: 'sent', label: 'Enviadas' },
  { value: 'viewed', label: 'Vistas' },
  { value: 'accepted', label: 'Aceptadas' },
  { value: 'rejected', label: 'Rechazadas' },
  { value: 'negotiating', label: 'Negociando' },
  { value: 'expired', label: 'Expiradas' },
];

const projectTypeOptions = [
  { value: 'website', label: 'Sitio Web' },
  { value: 'ecommerce', label: 'E-commerce' },
  { value: 'webapp', label: 'Aplicación Web' },
  { value: 'landing', label: 'Landing Page' },
  { value: 'redesign', label: 'Rediseño' },
  { value: 'mobile_app', label: 'App Móvil' },
  { value: 'branding', label: 'Branding' },
  { value: 'cms', label: 'Sistema CMS' },
  { value: 'portal', label: 'Portal / Intranet' },
  { value: 'api_integration', label: 'Integración de APIs' },
  { value: 'marketplace', label: 'Marketplace' },
  { value: 'erp', label: 'Sistema ERP' },
  { value: 'booking', label: 'Sistema de Reservas' },
  { value: 'dashboard', label: 'Dashboard / Reportes' },
  { value: 'crm', label: 'Sistema CRM' },
  { value: 'saas', label: 'SaaS / Plataforma' },
  { value: 'chatbot', label: 'Chatbot / IA' },
  { value: 'ai_tool', label: 'Herramienta con IA' },
  { value: 'automation', label: 'Automatización' },
  { value: 'data_analytics', label: 'Analítica de Datos' },
  { value: 'plugin_extension', label: 'Plugin / Extensión' },
  { value: 'other', label: 'Otro' },
];

const marketTypeOptions = [
  { value: 'b2b', label: 'B2B' },
  { value: 'b2c', label: 'B2C' },
  { value: 'saas', label: 'SaaS' },
  { value: 'retail', label: 'Retail' },
  { value: 'services', label: 'Servicios profesionales' },
  { value: 'health', label: 'Salud' },
  { value: 'education', label: 'Educación' },
  { value: 'real_estate', label: 'Inmobiliaria' },
  { value: 'fintech', label: 'Fintech' },
  { value: 'restaurant', label: 'Restaurantes' },
  { value: 'tourism', label: 'Turismo' },
  { value: 'logistics', label: 'Logística' },
  { value: 'sports', label: 'Deportes' },
  { value: 'legal', label: 'Servicios Legales' },
  { value: 'construction', label: 'Construcción' },
  { value: 'media', label: 'Medios' },
  { value: 'ngo', label: 'ONG / Sector Público' },
  { value: 'agriculture', label: 'Agro' },
  { value: 'tech', label: 'Tecnología' },
  { value: 'consulting', label: 'Consultoría' },
  { value: 'automotive', label: 'Automotriz' },
  { value: 'fashion', label: 'Moda' },
  { value: 'beauty', label: 'Belleza' },
  { value: 'manufacturing', label: 'Manufactura' },
  { value: 'energy', label: 'Energía' },
  { value: 'gaming', label: 'Gaming' },
  { value: 'other', label: 'Otro' },
];

const projectTypeLabelMap = Object.fromEntries(projectTypeOptions.map((o) => [o.value, o.label]));
const marketTypeLabelMap = Object.fromEntries(marketTypeOptions.map((o) => [o.value, o.label]));

function emitUpdate(partial) {
  emit('update:modelValue', { ...props.modelValue, ...partial });
}

function toggleArrayFilter(field, value) {
  const arr = [...props.modelValue[field]];
  const idx = arr.indexOf(value);
  if (idx >= 0) arr.splice(idx, 1);
  else arr.push(value);
  emitUpdate({ [field]: arr });
}

function removeFromArray(field, value) {
  emitUpdate({ [field]: props.modelValue[field].filter((v) => v !== value) });
}

function toggleMultiSelect(field, value) {
  if (!value) {
    emitUpdate({ [field]: [] });
  } else {
    const arr = [...props.modelValue[field]];
    const idx = arr.indexOf(value);
    if (idx >= 0) arr.splice(idx, 1);
    else arr.push(value);
    emitUpdate({ [field]: arr });
  }
}

function updateNumeric(field, value) {
  const parsed = value === '' ? null : Number(value);
  emitUpdate({ [field]: parsed });
}

function updateField(field, value) {
  emitUpdate({ [field]: value });
}
</script>
