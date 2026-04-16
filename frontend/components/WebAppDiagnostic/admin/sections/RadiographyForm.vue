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
      <label class="block text-xs font-medium text-gray-500 mb-1">Intro</label>
      <textarea v-model="form.intro" rows="3" class="w-full px-3 py-2 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700"></textarea>
    </div>

    <div class="pt-3 border-t border-gray-100 dark:border-gray-700 space-y-2">
      <div>
        <label class="block text-xs font-medium text-gray-500 mb-1">Título «¿Qué incluye?»</label>
        <input v-model="form.includesTitle" type="text" class="w-full px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
      </div>
      <div class="flex items-center justify-between">
        <span class="text-xs font-medium text-gray-500">Elementos de la radiografía</span>
        <button type="button" class="text-xs text-emerald-600 hover:underline" @click="addInclude">+ Agregar</button>
      </div>
      <div class="space-y-2">
        <div
          v-for="(it, idx) in form.includes"
          :key="idx"
          class="grid sm:grid-cols-[1fr,2fr,auto] gap-2 items-start"
        >
          <input v-model="it.title" type="text" placeholder="Título" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
          <textarea v-model="it.description" rows="2" placeholder="Descripción" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700"></textarea>
          <button type="button" class="text-xs text-rose-600 hover:underline" @click="removeInclude(idx)">Quitar</button>
        </div>
      </div>
    </div>

    <div class="pt-3 border-t border-gray-100 dark:border-gray-700 space-y-2">
      <div class="grid sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">Título de clasificación</label>
          <input v-model="form.classificationTitle" type="text" class="w-full px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">Intro clasificación</label>
          <input v-model="form.classificationIntro" type="text" class="w-full px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
        </div>
      </div>

      <div class="flex items-center justify-between">
        <span class="text-xs font-medium text-gray-500">Filas de tamaño</span>
        <button type="button" class="text-xs text-emerald-600 hover:underline" @click="addRow">+ Agregar</button>
      </div>
      <div class="space-y-2">
        <div
          v-for="(r, idx) in form.classificationRows"
          :key="idx"
          class="grid sm:grid-cols-[2fr,1fr,1fr,1fr,auto] gap-2 items-center"
        >
          <input v-model="r.dimension" type="text" placeholder="Dimensión" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
          <input v-model="r.small" type="text" placeholder="Pequeña" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
          <input v-model="r.medium" type="text" placeholder="Mediana" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
          <input v-model="r.large" type="text" placeholder="Grande" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
          <button type="button" class="text-xs text-rose-600 hover:underline" @click="removeRow(idx)">×</button>
        </div>
      </div>

      <div>
        <label class="block text-xs font-medium text-gray-500 mb-1">Nota de clasificación</label>
        <textarea v-model="form.classificationNote" rows="2" class="w-full px-3 py-2 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700"></textarea>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue';

const props = defineProps({ modelValue: { type: Object, required: true } });
const emit = defineEmits(['update:modelValue']);

const form = reactive({
  ...props.modelValue,
  includes: [...(props.modelValue.includes || [])],
  classificationRows: [...(props.modelValue.classificationRows || [])],
});

watch(() => props.modelValue, (next) => {
  Object.assign(form, next);
  form.includes = [...(next.includes || [])];
  form.classificationRows = [...(next.classificationRows || [])];
}, { deep: true });

watch(form, (next) => emit('update:modelValue', {
  ...next,
  includes: [...next.includes],
  classificationRows: [...next.classificationRows],
}), { deep: true });

function addInclude() { form.includes.push({ title: '', description: '' }); }
function removeInclude(i) { form.includes.splice(i, 1); }
function addRow() { form.classificationRows.push({ dimension: '', small: '', medium: '', large: '' }); }
function removeRow(i) { form.classificationRows.splice(i, 1); }
</script>
