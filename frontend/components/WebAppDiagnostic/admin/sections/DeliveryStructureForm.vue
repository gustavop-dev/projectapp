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
      <textarea v-model="form.intro" rows="2" class="w-full px-3 py-2 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700"></textarea>
    </div>

    <div class="flex items-center justify-between pt-2">
      <span class="text-xs font-medium text-gray-500">Bloques (lo que se encontró bien / hallazgos / recomendaciones)</span>
      <button type="button" class="text-xs text-emerald-600 hover:underline" @click="addBlock">+ Agregar</button>
    </div>
    <div class="space-y-2">
      <div
        v-for="(b, idx) in form.blocks"
        :key="idx"
        class="p-3 border border-gray-200 dark:border-gray-700 rounded-xl space-y-2"
      >
        <div class="flex items-center justify-between">
          <input v-model="b.title" type="text" placeholder="Título del bloque" class="flex-1 px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
          <button type="button" class="text-xs text-rose-600 hover:underline ml-2" @click="form.blocks.splice(idx, 1)">Quitar</button>
        </div>
        <textarea v-model="b.paragraphsText" rows="3" placeholder="Párrafos (uno por línea)" class="w-full px-3 py-2 border rounded-lg text-sm font-mono dark:bg-gray-900 dark:border-gray-700"></textarea>
        <input v-model="b.example" type="text" placeholder="Ejemplo (opcional)" class="w-full px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue';

const props = defineProps({ modelValue: { type: Object, required: true } });
const emit = defineEmits(['update:modelValue']);

const form = reactive({ ...props.modelValue, blocks: [...(props.modelValue.blocks || [])] });

watch(() => props.modelValue, (next) => {
  Object.assign(form, next);
  form.blocks = [...(next.blocks || [])];
}, { deep: true });

watch(form, (next) => emit('update:modelValue', { ...next, blocks: [...next.blocks] }), { deep: true });

function addBlock() { form.blocks.push({ title: '', paragraphsText: '', example: '' }); }
</script>
