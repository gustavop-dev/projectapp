<template>
  <form class="space-y-6" @submit.prevent="$emit('submit')">
    <div>
      <label class="block">
        <span class="text-sm font-medium text-gray-700">Clasificación de tamaño</span>
        <select
          class="mt-1 w-full border rounded px-3 py-2"
          :value="modelValue.size_category"
          @change="updateRoot('size_category', $event.target.value)"
        >
          <option value="">— Sin clasificar —</option>
          <option value="small">Pequeña</option>
          <option value="medium">Mediana</option>
          <option value="large">Grande</option>
        </select>
      </label>
    </div>

    <fieldset>
      <legend class="text-sm font-semibold text-gray-700 mb-2">Stack</legend>
      <div class="grid gap-3 md:grid-cols-2">
        <input class="border rounded px-3 py-2" placeholder="Backend (nombre)"
          :value="stack.backend?.name"
          @input="updateStack('backend', 'name', $event.target.value)" />
        <input class="border rounded px-3 py-2" placeholder="Backend (versión)"
          :value="stack.backend?.version"
          @input="updateStack('backend', 'version', $event.target.value)" />
        <input class="border rounded px-3 py-2" placeholder="Frontend (nombre)"
          :value="stack.frontend?.name"
          @input="updateStack('frontend', 'name', $event.target.value)" />
        <input class="border rounded px-3 py-2" placeholder="Frontend (versión)"
          :value="stack.frontend?.version"
          @input="updateStack('frontend', 'version', $event.target.value)" />
      </div>
    </fieldset>

    <fieldset>
      <legend class="text-sm font-semibold text-gray-700 mb-2">Inventario técnico</legend>
      <div class="grid gap-3 md:grid-cols-3">
        <NumField label="Migraciones"   field="migrations_count"   :radiography="rad" @update="updateRad" />
        <NumField label="Entidades / modelos"   field="entities_count"     :radiography="rad" @update="updateRad" />
        <NumField label="Rutas backend totales" field="routes_total"       :radiography="rad" @update="updateRad" />
        <NumField label="Rutas públicas"        field="routes_public"      :radiography="rad" @update="updateRad" />
        <NumField label="Rutas protegidas"      field="routes_protected"   :radiography="rad" @update="updateRad" />
        <NumField label="Controladores"         field="controllers_count"  :radiography="rad" @update="updateRad" />
        <NumField label="Controladores sin ruta" field="controllers_disconnected" :radiography="rad" @update="updateRad" />
        <NumField label="Vistas frontend"       field="frontend_routes_count" :radiography="rad" @update="updateRad" />
        <NumField label="Componentes"           field="components_count"   :radiography="rad" @update="updateRad" />
        <NumField label="Integraciones externas" field="external_integrations" :radiography="rad" @update="updateRad" />
        <NumField label="Tests existentes"      field="test_files_count"   :radiography="rad" @update="updateRad" />
        <NumField label="Archivos CI/CD"        field="ci_files_count"     :radiography="rad" @update="updateRad" />
        <NumField label="Archivos Docker"       field="docker_files_count" :radiography="rad" @update="updateRad" />
      </div>
      <label class="block mt-3">
        <span class="text-sm font-medium text-gray-700">Etiqueta de cobertura de pruebas</span>
        <input class="mt-1 w-full border rounded px-3 py-2"
          placeholder="Ej: 0%, ~30%, etc."
          :value="rad.test_coverage_label"
          @input="updateRad('test_coverage_label', $event.target.value)" />
      </label>
    </fieldset>

    <fieldset>
      <legend class="text-sm font-semibold text-gray-700 mb-2">Módulos funcionales (uno por línea)</legend>
      <textarea
        rows="6"
        class="w-full border rounded px-3 py-2 font-mono text-sm"
        :value="(rad.modules || []).join('\n')"
        @input="updateRad('modules', $event.target.value.split('\n').map(s => s.trim()).filter(Boolean))"
      />
    </fieldset>

    <div class="text-right">
      <button
        type="submit"
        class="px-4 sm:px-5 py-2 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-all shadow-sm shadow-emerald-100 hover:shadow-md hover:shadow-emerald-200 active:scale-[0.98] disabled:opacity-50"
        :disabled="busy"
      >{{ busy ? 'Guardando...' : 'Guardar radiografía' }}</button>
    </div>
  </form>
</template>

<script setup>
import { computed, h } from 'vue';

const props = defineProps({
  modelValue: { type: Object, required: true },
  busy: { type: Boolean, default: false },
});
const emit = defineEmits(['update:modelValue', 'submit']);

const rad = computed(() => props.modelValue.radiography || {});
const stack = computed(() => rad.value.stack || {});

function updateRoot(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value });
}
function updateRad(key, value) {
  const nextRad = { ...rad.value, [key]: value };
  emit('update:modelValue', { ...props.modelValue, radiography: nextRad });
}
function updateStack(layer, key, value) {
  const nextStack = {
    ...stack.value,
    [layer]: { ...(stack.value[layer] || {}), [key]: value },
  };
  updateRad('stack', nextStack);
}

const NumField = {
  props: ['label', 'field', 'radiography'],
  emits: ['update'],
  setup(p, { emit }) {
    return () => h('label', { class: 'block' }, [
      h('span', { class: 'text-sm font-medium text-gray-700' }, p.label),
      h('input', {
        type: 'number',
        min: 0,
        class: 'mt-1 w-full border rounded px-3 py-2',
        value: p.radiography[p.field] ?? '',
        onInput: (e) => emit('update', p.field, Number(e.target.value) || 0),
      }),
    ]);
  },
};
</script>
