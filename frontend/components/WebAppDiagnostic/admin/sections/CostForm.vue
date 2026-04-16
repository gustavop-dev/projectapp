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
    <p class="text-xs text-gray-400 italic">
      El monto, la moneda y los porcentajes se toman del tab de Pricing.
    </p>
    <div>
      <div class="flex items-center justify-between mb-1">
        <span class="text-xs font-medium text-gray-500">Descripción de los pagos</span>
        <button type="button" class="text-xs text-emerald-600 hover:underline" @click="addItem">+ Agregar</button>
      </div>
      <div class="space-y-2">
        <div
          v-for="(p, idx) in form.paymentDescription"
          :key="idx"
          class="grid sm:grid-cols-[1fr,3fr,auto] gap-2 items-start"
        >
          <input v-model="p.label" type="text" placeholder="al inicio / al final" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
          <textarea v-model="p.detail" rows="2" placeholder="Detalle" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700"></textarea>
          <button type="button" class="text-xs text-rose-600 hover:underline" @click="form.paymentDescription.splice(idx,1)">×</button>
        </div>
      </div>
    </div>
    <div>
      <label class="block text-xs font-medium text-gray-500 mb-1">Nota</label>
      <textarea v-model="form.note" rows="2" class="w-full px-3 py-2 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700"></textarea>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue';

const props = defineProps({ modelValue: { type: Object, required: true } });
const emit = defineEmits(['update:modelValue']);

const form = reactive({
  ...props.modelValue,
  paymentDescription: [...(props.modelValue.paymentDescription || [])],
});

watch(() => props.modelValue, (next) => {
  Object.assign(form, next);
  form.paymentDescription = [...(next.paymentDescription || [])];
}, { deep: true });

watch(form, (next) => emit('update:modelValue', {
  ...next,
  paymentDescription: [...next.paymentDescription],
}), { deep: true });

function addItem() { form.paymentDescription.push({ label: '', detail: '' }); }
</script>
