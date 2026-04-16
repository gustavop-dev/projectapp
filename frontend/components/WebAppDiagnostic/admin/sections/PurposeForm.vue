<template>
  <div class="space-y-3">
    <div class="grid sm:grid-cols-6 gap-3">
      <div class="sm:col-span-1">
        <label class="block text-xs font-medium text-gray-500 mb-1">Índice</label>
        <input v-model="form.index" type="text" class="w-full px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
      </div>
      <div class="sm:col-span-5">
        <label class="block text-xs font-medium text-gray-500 mb-1">Título</label>
        <input v-model="form.title" type="text" class="w-full px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
      </div>
    </div>
    <div>
      <label class="block text-xs font-medium text-gray-500 mb-1">Párrafos (uno por línea)</label>
      <textarea v-model="form.paragraphsText" rows="5" class="w-full px-3 py-2 border rounded-lg text-sm font-mono dark:bg-gray-900 dark:border-gray-700"></textarea>
    </div>
    <div>
      <label class="block text-xs font-medium text-gray-500 mb-1">Nota de alcance</label>
      <textarea v-model="form.scopeNote" rows="3" class="w-full px-3 py-2 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700"></textarea>
    </div>

    <div class="pt-3 border-t border-gray-100 dark:border-gray-700 space-y-2">
      <div class="grid sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">Título de Severidad</label>
          <input v-model="form.severityTitle" type="text" class="w-full px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">Intro de Severidad</label>
          <input v-model="form.severityIntro" type="text" class="w-full px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
        </div>
      </div>
      <div>
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-medium text-gray-500">Niveles de severidad</span>
          <button type="button" class="text-xs text-emerald-600 hover:underline" @click="addLevel">+ Agregar</button>
        </div>
        <div class="space-y-2">
          <div
            v-for="(lvl, idx) in form.severityLevels"
            :key="idx"
            class="grid sm:grid-cols-[1fr,3fr,auto] gap-2 items-start"
          >
            <input v-model="lvl.level" type="text" placeholder="Crítico / Alto / Medio / Bajo" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
            <textarea v-model="lvl.meaning" rows="2" placeholder="Significado" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700"></textarea>
            <button type="button" class="text-xs text-rose-600 hover:underline" @click="removeLevel(idx)">Quitar</button>
          </div>
          <div v-if="!form.severityLevels.length" class="text-xs text-gray-400 italic">Sin niveles configurados.</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue';

const props = defineProps({ modelValue: { type: Object, required: true } });
const emit = defineEmits(['update:modelValue']);

const form = reactive({ ...props.modelValue, severityLevels: [...(props.modelValue.severityLevels || [])] });

watch(() => props.modelValue, (next) => {
  Object.assign(form, next);
  form.severityLevels = [...(next.severityLevels || [])];
}, { deep: true });

watch(form, (next) => emit('update:modelValue', { ...next, severityLevels: [...next.severityLevels] }), { deep: true });

function addLevel() { form.severityLevels.push({ level: '', meaning: '' }); }
function removeLevel(i) { form.severityLevels.splice(i, 1); }
</script>
