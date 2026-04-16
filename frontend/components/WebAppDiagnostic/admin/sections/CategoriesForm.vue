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
      <span class="text-xs font-medium text-gray-500">Categorías evaluadas ({{ form.categories.length }})</span>
      <button type="button" class="text-xs text-emerald-600 hover:underline" @click="addCategory">+ Nueva categoría</button>
    </div>

    <div class="space-y-3">
      <details
        v-for="(cat, idx) in form.categories"
        :key="idx"
        class="border border-gray-200 dark:border-gray-700 rounded-xl"
      >
        <summary class="px-3 py-2 cursor-pointer select-none text-sm font-medium text-gray-700 dark:text-gray-200 flex items-center justify-between">
          <span class="truncate">{{ idx + 1 }}. {{ cat.title || '(sin título)' }}</span>
          <button type="button" class="text-xs text-rose-600 hover:underline ml-2" @click.prevent="removeCategory(idx)">Quitar</button>
        </summary>
        <div class="p-3 space-y-3 border-t border-gray-100 dark:border-gray-700">
          <div class="grid sm:grid-cols-2 gap-2">
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">Clave</label>
              <input v-model="cat.key" type="text" class="w-full px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">Título</label>
              <input v-model="cat.title" type="text" class="w-full px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
            </div>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">Descripción</label>
            <textarea v-model="cat.description" rows="3" class="w-full px-3 py-2 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700"></textarea>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">Lo bueno (una línea por ítem)</label>
            <textarea v-model="cat.strengthsText" rows="3" class="w-full px-3 py-2 border rounded-lg text-sm font-mono dark:bg-gray-900 dark:border-gray-700"></textarea>
          </div>

          <div class="pt-2 border-t border-gray-100 dark:border-gray-700">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs font-medium text-gray-500">Hallazgos</span>
              <button type="button" class="text-xs text-emerald-600 hover:underline" @click="addFinding(cat)">+ Agregar</button>
            </div>
            <div class="space-y-2">
              <div
                v-for="(f, fi) in cat.findings"
                :key="fi"
                class="grid sm:grid-cols-[1fr,2fr,3fr,auto] gap-2 items-start"
              >
                <select v-model="f.level" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700">
                  <option value="">Nivel…</option>
                  <option v-for="lvl in SEVERITY_LEVELS" :key="lvl" :value="lvl">{{ lvl }}</option>
                </select>
                <input v-model="f.title" type="text" placeholder="Título" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
                <textarea v-model="f.detail" rows="2" placeholder="Detalle" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700"></textarea>
                <button type="button" class="text-xs text-rose-600 hover:underline" @click="cat.findings.splice(fi,1)">×</button>
              </div>
            </div>
          </div>

          <div class="pt-2 border-t border-gray-100 dark:border-gray-700">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs font-medium text-gray-500">Recomendaciones</span>
              <button type="button" class="text-xs text-emerald-600 hover:underline" @click="addRec(cat)">+ Agregar</button>
            </div>
            <div class="space-y-2">
              <div
                v-for="(r, ri) in cat.recommendations"
                :key="ri"
                class="grid sm:grid-cols-[1fr,2fr,3fr,auto] gap-2 items-start"
              >
                <select v-model="r.level" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700">
                  <option value="">Nivel…</option>
                  <option v-for="lvl in SEVERITY_LEVELS" :key="lvl" :value="lvl">{{ lvl }}</option>
                </select>
                <input v-model="r.title" type="text" placeholder="Sugerencia" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700" />
                <textarea v-model="r.detail" rows="2" placeholder="Relación/Detalle" class="px-2 py-1.5 border rounded-lg text-sm dark:bg-gray-900 dark:border-gray-700"></textarea>
                <button type="button" class="text-xs text-rose-600 hover:underline" @click="r.recommendations?.splice(ri,1); cat.recommendations.splice(ri,1)">×</button>
              </div>
            </div>
          </div>
        </div>
      </details>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue';
import { SEVERITY_LEVELS } from '~/stores/diagnostics_constants';

const props = defineProps({ modelValue: { type: Object, required: true } });
const emit = defineEmits(['update:modelValue']);

function cloneCategories(list) {
  return (list || []).map((c) => ({
    key: c.key || '',
    title: c.title || '',
    description: c.description || '',
    strengthsText: c.strengthsText || '',
    findings: [...(c.findings || [])].map((f) => ({ ...f })),
    recommendations: [...(c.recommendations || [])].map((r) => ({ ...r })),
  }));
}

const form = reactive({
  ...props.modelValue,
  categories: cloneCategories(props.modelValue.categories),
});

watch(() => props.modelValue, (next) => {
  Object.assign(form, next);
  form.categories = cloneCategories(next.categories);
}, { deep: true });

watch(form, (next) => emit('update:modelValue', {
  ...next,
  categories: cloneCategories(next.categories),
}), { deep: true });

function addCategory() {
  form.categories.push({
    key: '',
    title: '',
    description: '',
    strengthsText: '',
    findings: [],
    recommendations: [],
  });
}
function removeCategory(i) { form.categories.splice(i, 1); }
function addFinding(cat) { cat.findings.push({ level: '', title: '', detail: '' }); }
function addRec(cat) { cat.recommendations.push({ level: '', title: '', detail: '' }); }
</script>
